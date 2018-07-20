"""
Modules that separates out all of the code to run a gromacs
simulation away from the code used to interface with Fn

@author Christopher Woods
"""

import os
import sys
import glob
import subprocess
import objstore
import datetime
import tarfile
import tempfile
import multiprocessing

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Error(Exception):
    """Base class for exceptions in this module"""
    pass

class GromppError(Error):
    """Exception caused by failure of grompp"""
    pass

class MDRunError(Error):
    """Exception raised by a failure of mdrun"""
    pass

class FileWatcher:
    """This class is used to watch a specific file,
       uploading chunks of the file to an object store
       when the watcher is updated"""
    def __init__(self, filename, bucket, rootkey):
        self._filename = filename
        self._bucket = bucket
        self._rootkey = rootkey
        self._handle = None
        self._key = None
        self._buffer = None
        self._last_upload_time = datetime.datetime.now()
        self._next_chunk = 0
        self._chunksize = 8192
        self._uploadsize = 8*1024*1024
        self._upload_timeout = 1

    def _uploadBuffer(self):
        """Internal function that uploads the current buffer to
           a new chunk in the object store"""
        if len(self._buffer) == 0:
            #nothing to upload
            return

        self._next_chunk += 1
        self._last_upload_time = datetime.datetime.now()

        objstore.log(self._bucket, "Upload %s chunk (%f KB) to %s/%s" % \
                       (self._filename, float(len(self._buffer))/1024.0,
                        self._key, self._next_chunk))

        self._buffer = None

    def finishUploads(self):
        """Finalise the uploads"""
        self._uploadBuffer()

    def update(self):
        """Called whenever the file changes"""
        if not self._key:
            # the file hasn't been opened or uploaded yet - create
            # key for this file, open the file and read as much as
            # possible into a buffer, ready for upload
            if self._rootkey:
                self._key = "%s/%s" % (self._rootkey,self._filename)
            else:
                self._key = self._filename

            # open the file and connect to the filehandle
            self._handle = open(self._filename, "rb")

        # read in the next chunk of the file
        while True:
            chunk = self._handle.read(self._chunksize)

            if chunk:
                if not self._buffer:
                    self._buffer = chunk
                else:
                    self._buffer += chunk

                if len(self._buffer) > self._uploadsize:
                    self._uploadBuffer()
            else:
                # nothing more to read
                break
    
        # we have read in everything that has been produced - should 
        # we upload it? Only upload if more than 5 seconds have passed
        # since the last update
        if (datetime.datetime.now() - self._last_upload_time).seconds \
                  > self._upload_timeout:
            self._uploadBuffer()
        

class PosixToObjstoreEventHandler(FileSystemEventHandler):
    """This class responds to events in the filesystem. 
       The aim is to detect as files are created and modified,
       and to stream this data up to the object store while
       the simulation is in progress. This is called in 
       a background thread by watchdog"""

    def __init__(self, bucket, root=None):
        FileSystemEventHandler.__init__(self)
        self._bucket = bucket
        self._root = root
        self._files = {}

    def finishUploads(self):
        # Call this to complete all of the uploads
        for f in self._files:
            self._files[f].finishUploads()

    def on_any_event(self, event):
        # ideally, if this is a new file then open the file in 
        # binary mode and connect to a handle

        # if file changed, then read the change in binary into a buffer.
        # If the buffer grows to larger than X or the amount of time since
        # the last upload to the object store is > 5 seconds (configurable)
        # then upload the buffer to the object store as the next chunk 
        # of the file, e.g. to /bucket/interim/filename/chunk_number

        # it should be that all of the chunks can be merged together
        # to recreate the original file... (we hope - should md5 check!)

        if event.is_directory:
            return

        filename = event.src_path

        if filename.startswith("./"):
            filename = filename[2:]

        if not filename in self._files:
            self._files[filename] = FileWatcher(filename, self._bucket, self._root)

        self._files[filename].update()


def run(bucket):
    """Run the gromacs simulation whose input is contained
       in the passed bucket. Read the input from /input, 
       write a log to /log and write the output to /output
    """

    # path to the gromacs executables
    gmx = "/usr/local/gromacs/bin/gmx"

    # Clear the log for this simulation
    objstore.clear_log(bucket)

    # create a log function for logging messages to this bucket
    log = lambda message: objstore.log(bucket,message)

    # create a set_status function for setting the simulation status
    set_status = lambda status: objstore.set_string_object(bucket, "status", status)

    set_status("Loading...")

    # create a temporary directory for the simulation
    # (this ensures we are in the writable part of the container)
    tmpdir = tempfile.mkdtemp()

    os.chdir(tmpdir)

    log("Running a gromacs simulation in %s" % tmpdir)

    # get the value of the input key
    input_tar_bz2 = objstore.get_object_as_file(bucket, "input.tar.bz2", 
                                                "/%s/input.tar.bz2" % tmpdir)

    # now unpack this file
    with tarfile.open(input_tar_bz2, "r:bz2") as tar:
        tar.extractall(".")

    # remove the tar file to save space
    os.remove(input_tar_bz2)

    # all simulation will take place in the "output" directory
    os.makedirs("output")
    os.chdir("output")

    # get the name of the mdp, top and gro files
    mdpfile = glob.glob("../*.mdp")[0]
    topfile = glob.glob("../*.top")[0]
    grofile = glob.glob("../*.gro")[0]

    set_status("Preparing...")

    # run grompp to generate the input
    cmd = "%s grompp -f %s -c %s -p %s -o run.tpr" % (gmx,mdpfile,grofile,topfile)
    log("Running '%s'" % cmd)

    grompp_stdout = open("grompp.out", "w")
    grompp_stderr = open("grompp.err", "w")

    status = subprocess.run([gmx, "grompp",
                             "-f", mdpfile,
                             "-c", grofile,
                             "-p", topfile,
                             "-o", "run.tpr"],
                            stdout=grompp_stdout, stderr=grompp_stderr)

    log("gmx grompp completed. Return code == %s" % status.returncode)

    # Upload the grompp output to the object store
    objstore.set_object_from_file(bucket, "output/grompp.out", "grompp.out")
    objstore.set_object_from_file(bucket, "output/grompp.err", "grompp.err")

    if status.returncode != 0:
        raise GromppError("Grompp failed to run: Error code = %s" % 
                          status.returncode)

    # now write a run script to run the process and output the result
    cmd = "%s mdrun -v -deffnm run > mdrun.stdout 2> mdrun.stderr" % gmx
    FILE = open("run_mdrun.sh", "w")
    FILE.write("#!/bin/bash\n")
    FILE.write("%s\n" % cmd)
    FILE.close()

    set_status("Running...")

    # Start a watchdog process to look for new files
    observer = Observer()
    event_handler = PosixToObjstoreEventHandler(bucket,"interim")
    observer.schedule(event_handler, ".", recursive=False)
    log("Starting the filesystem observer...")
    observer.start()

    # start the processor in the background
    log("Running '%s'" % cmd)
    PROC = os.popen("bash run_mdrun.sh", "r")

    # wait for the gromacs job to finish...
    status = PROC.close()

    log("Gromacs has finished. Waiting for filesystem observer...")

    # stop monitoring for events
    observer.stop()
    observer.join()

    log("gmx mdrun completed. Return code == %s" % status)

    set_status("Uploading output...")

    # Upload all of the output files to the output directory
    log("Uploading mdrun.stdout")
    objstore.set_object_from_file(bucket, "output/mdrun.stdout", "mdrun.stdout")
    log("Uploading mdrun.stderr")
    objstore.set_object_from_file(bucket, "output/mdrun.stderr", "mdrun.stderr")

    for filename in glob.glob("run.*"):
        if not filename.endswith("tpr"):
            log("Uploading %s" % filename)
            objstore.set_object_from_file(bucket,
                                          "output/%s" % filename, filename) 

    log("Simulation and data upload complete.")

    if status:
        set_status("Error")
        return (status, "Simulation finished with ERROR")
    else:
        set_status("Completed")
        return (0, "Simulation finished successfully")
