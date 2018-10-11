
import glob as _glob
import os as _os

from Acquire.Crypto import PrivateKey as _PrivateKey

from Acquire.Service import call_function as _call_function
from Acquire.Service import Service as _Service

from ._user import User as _User
from ._account import Account as _Account

from ._errors import LoginError

__all__ = ["CloudDrive", "expand_source_destination"]


def list_all_files(directory, ignore_hidden=True):
    """Return a list of the path relative to 'directory' of
       all files contained in 'directory'. If is_hidden is True, then include
       all hidden files - otherwise these are ignored
    """
    if not _os.path.isdir(directory):
        return []

    all_files = []

    for (root, dirs, filenames) in _os.walk(directory):
        root = root[len(directory)+1:]

        if ignore_hidden and root.startswith("."):
            continue

        for filename in filenames:
            if not (filename.startswith(".") and ignore_hidden):
                all_files.append(_os.path.join(root, filename))

    return all_files


def expand_source_destination(source, destination, ignore_hidden=True):
    """This function expands the 'source' and 'destination' into a pair
       of lists - the source files and the destination files.
    """
    if not isinstance(source, list):
        source = [str(source)]

    # expand all of the sources into the full paths of files (which must exist)
    abs_filenames = []
    rel_filenames = []

    for s in source:
        for f in _glob.glob(str(s)):
            abspath = _os.path.abspath(f)
            if not _os.path.exists(abspath):
                raise FileExistsError("The file '%s' does not exist!"
                                      % abspath)

            if _os.path.isdir(abspath):
                dirfiles = list_all_files(abspath, ignore_hidden)

                for dirfile in dirfiles:
                    abs_filenames.append(_os.path.join(abspath, dirfile))
                    rel_filenames.append(dirfile)
            else:
                abs_filenames.append(abspath)
                rel_filenames.append(_os.path.basename(abspath))

    des_filenames = []

    if destination is None:
        des_filenames = rel_filenames
    elif len(rel_filenames) == 1:
        if destination.endswith("/"):
            des_filenames.append(_os.path.join(destination, abs_filenames[0]))
        else:
            des_filenames.append(destination)
    else:
        for rel_filename in rel_filenames:
            des_filenames.append(_os.path.join(destination, rel_filename))

    return (abs_filenames, des_filenames)


def _get_access_url():
    """Function to discover and return the default access service url"""
    return "http://130.61.60.88:8080/r/access"


def _get_access_service(access_url=None):
    """Function to return the access service for the system"""
    if access_url is None:
        access_url = _get_access_url()

    privkey = _PrivateKey()
    response = _call_function(access_url, {}, response_key=privkey)

    try:
        service = _Service.from_data(response["service_info"])
    except:
        raise LoginError("Have not received the access service info from "
                         "the access service at '%s' - got '%s'" %
                         (access_url, response))

    if not service.is_access_service():
        raise LoginError(
            "You can only use a valid access service to access resources! "
            "The service at '%s' is a '%s'" %
            (access_url, service.service_type()))

    if service.service_url() != access_url:
        service.update_service_url(access_url)

    return service


class CloudDrive:
    """This class represents a cloud drive. This provides a storage space
       to read and write files, and also to stream files as they are
       being written
    """
    def __init__(self, user, root=None, access_url=None):
        """Create a drive that is billed to the passed account and accessed
           via the passed access service. If 'root' is specified, then
           only read or write to the drive from 'root', otherwise allow
           reading/writing to all parts of the drive.
        """
        if not isinstance(user, _User):
            raise TypeError("The user must be of type User")

        if not user.is_logged_in():
            raise PermissionError(
                "You cannot create/access a cloud drive belonging to '%s' "
                "without that user being logged in" % str(user))

        self._user = user
        self._access_service = _get_access_service(access_url)

        if root:
            self._root = str(root)
        else:
            self._root = None

    def upload(self, source, destination=None, ignore_hidden=True,
               account=None):
        """Upload a file (or files) from 'source' to 'destination'. If
           'destination is not supplied, then the file(s) will be uploaded
           with 'destination' equals 'source' (i.e. they will have the same
           name on the cloud drive as they do on the drive). If 'destination'
           is supplied then if it ends in a "/" then the destination will
           be treated like a directory. If the number of source files is
           greater than 1 and only a single destination directory is provided
           then all files will be uploaded into that directory.

           If 'ignore_hidden' is true, then hidden files will be ignored
           when uploading directories (but not when specifying files
           manually)

           If you pass in 'account', then
           this account will be used to pay for the storage. The account
           can be authorised from a different user to the owner of the drive,
           although both the user and account must be in the logged-in state.

           If you don't specify the account then the default account for
           the user will be used.

           Note that you cannot overwrite a file that already exists. It has
           to be explicitly removed first.

           Note that this is an atomic function - either all of none
           of the files will be written.

           This will return the list of read-only handles to allow you
           (or anyone else) to read these files.
        """
        (abs_filenames, des_filenames) = expand_source_destination(
                                            source, destination,
                                            ignore_hidden)

        if len(abs_filenames) == 0:
            return []

        if account is None:
            account = _Account(user=self._user)

        from Acquire.Access import FileWriteRequest as _FileWriteRequest
