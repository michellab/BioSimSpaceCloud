"""
Modules that separates out all of the code to run a gromacs
simulation away from the code used to interface with Fn

@author Christopher Woods
"""

import os
import sys
import objstore
import datetime

def run(bucket):
    """Run the gromacs simulation whose input is contained
       in the passed bucket. Read the input from /input, 
       write a log to /log and write the output to /output
    """

    sys.stderr.write("\n\nOld log:\n%s\n\n" % "\n".join(objstore.get_log(bucket)))

    objstore.clear_log(bucket)
    log = lambda message: objstore.log(bucket,message)

    log("Running a gromacs simulation!\n")

    # get the value of the input key
    data = objstore.get_object(bucket, "input")

    objs = objstore.get_all_objects(bucket)

    names = list(objs.keys())
    names.sort()

    for name in names:
        sys.stderr.write("%s => %s\n" % (name,str(objs[name])))

    return (0, "Simulation complete: %s" % data)
