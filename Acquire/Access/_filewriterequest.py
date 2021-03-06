
from uuid import uuid4 as _uuid4
import copy as _copy
import os as _os
import hashlib as _hashlib
import glob as _glob

from ._request import Request as _Request

from Acquire.Identity import Authorisation as _Authorisation

__all__ = ["FileWriteRequest"]


def _get_key(root_key, filename):
    """Return the object store key for 'filename', using 'root_key' as
       the root
    """
    basename = _os.path.basename(filename)

    if root_key:
        return "%s/%s" % (str(root_key), basename)
    else:
        return basename


def _clean_key(root_key, filekey):
    """Return the cleaned key 'filekey', using 'root_key' as the root"""
    if root_key:
        return "%s/%s" % (str(root_key), str(filekey))
    else:
        return str(filekey)


def _get_filesize_and_checksum(filename):
    """Return a tuple of the size in bytes of the passed file and the
       file's md5 checksum
    """
    md5 = _hashlib.md5()
    size = 0

    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
            size += len(chunk)

    return (size, str(md5.hexdigest()))


def _list_all_files(directory, ignore_hidden=True):
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


def _clean_path(path):
    """This function cleans the passed path so that doesn't contain
       redundant slashes or '..' etc., so that all backslashes are forwards
       slashes, and that the trailing slash is removed
    """
    if path is None:
        return ""

    path = _os.path.normpath(path)

    # remove all ".." and "." from this path
    if path.find(".") != -1:
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part == "." or part == "..":
                parts[i] = ""

        path = _os.path.normpath("/".join(parts))

    return path


def _expand_source_destination(source, destination=None,
                               root=None, ignore_hidden=True):
    """This function expands the 'source' and 'destination' into a pair
       of lists - the source files and the destination keys in the
       object store.
    """
    if source is None:
        return ([], [])

    if not isinstance(source, list):
        source = [str(source)]

    is_destination_dir = False
    try:
        is_destination_dir = destination.endswith("/")
    except:
        pass

    destination = _os.path.normpath(_os.path.join(_clean_path(root),
                                                  _clean_path(destination)))

    # expand all of the sources into the full paths of files (which must exist)
    source_filenames = []
    rel_filenames = []

    for s in source:
        for f in _glob.glob(str(s)):
            abspath = _os.path.abspath(f)
            if not _os.path.exists(abspath):
                raise FileExistsError("The file '%s' does not exist!"
                                      % abspath)

            if _os.path.isdir(abspath):
                dirfiles = _list_all_files(abspath, ignore_hidden)

                for dirfile in dirfiles:
                    source_filenames.append(_os.path.join(abspath, dirfile))
                    rel_filenames.append(dirfile)
            else:
                source_filenames.append(abspath)
                rel_filenames.append(_os.path.basename(abspath))

    destination_keys = []

    if len(rel_filenames) == 1:
        if is_destination_dir:
            destination_keys.append(_os.path.join(destination,
                                                  rel_filenames[0]))
        else:
            destination_keys.append(destination)
    else:
        for rel_filename in rel_filenames:
            destination_keys.append(_os.path.join(destination, rel_filename))

    if len(source_filenames) != len(destination_keys):
        raise ValueError("Something went wrong as the number of source "
                         "filenames should be equal to the number of keys")

    return (source_filenames, destination_keys)


class FileWriteRequest(_Request):
    """This class holds a request to write a file (or files) to a remote
       object store
    """
    def __init__(self, source=None, destination=None, root=None,
                 ignore_hidden=True, account=None, testing_key=None):
        """Construct the request to write the files specified in 'source'
           to 'destination' in the cloud object store. You can optionally
           pass a 'root' for all of the keys in the object store, and,
           if the source is a directory, you can ignore hidden files using
           'ignore_hidden=True'.

           You must pass the 'account' from which payment will be taken to
           write files to the object store.
        """
        super().__init__()

        (filenames, keys) = FileWriteRequest.expand_source_and_destination(
                                                source, destination,
                                                root, ignore_hidden)

        self._destination_keys = keys
        self._source_filenames = filenames
        self._file_sizes = []
        self._checksums = []

        if len(self._source_filenames) == 0:
            self._uid = None
            return

        for filename in self._source_filenames:
            (size, checksum) = _get_filesize_and_checksum(filename)
            self._file_sizes.append(size)
            self._checksums.append(checksum)

        self._is_testing = False

        if testing_key:
            self._is_testing = True
            self._testing_key = testing_key
        elif account is not None:
            from Acquire.Client import Account as _Account
            if not isinstance(account, _Account):
                raise TypeError("The passed account must be type Account")

            if not account.is_logged_in():
                raise PermissionError(
                    "You can only authorise payment from the account if you "
                    "have logged in")

        else:
            raise ValueError("You must pass a valid account to write files!")

        self._uid = str(_uuid4())

        if self._is_testing:
            self._account_uid = "something"
            self._accounting_service_url = "somewhere"
            self._authorisation = _Authorisation(
                                    resource=self.resource_key(),
                                    testing_key=self._testing_key)

        else:
            self._account_uid = account.uid()
            self._accounting_service_url = account.accounting_service()\
                                                  .canonical_url()

            self._authorisation = _Authorisation(
                                    resource=self.resource_key(),
                                    user=account.owner())

    def is_null(self):
        """Return whether or not this is a null request"""
        return self._uid is None

    def __str__(self):
        if self.is_null():
            return "FileWriteRequest::null"
        else:
            return "FileWriteRequest(uid=%s)" % self._uid

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._uid == other._uid
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def resource_key(self):
        """Function to return a string that can be used as a
           summary key for this resource request
        """
        if self.is_null():
            return None
        else:
            return "%s %s" % (self._uid, ":".join(self._checksums))

    def uid(self):
        """Return the UID of this request"""
        return self._uid

    def authorisation(self):
        """Return the authorisation behind this request"""
        return self._authorisation

    def source_filenames(self):
        """Return the filenames of the files to be copied. Note that this
           information is only available in the copy of the object that
           created the request - it is not saved when this object is
           serialised to json as we don't want to leak potentially
           sensitive data to the object store
        """
        return self._source_filenames

    def destination_keys(self):
        """Return the object store keys to which the files will be
           written
        """
        return _copy.copy(self._destination_keys)

    def filesizes(self):
        """Return the sizes of the files that are requested to be written"""
        return _copy.copy(self._file_sizes)

    def checksums(self):
        """Return the checksums of the files that are requested
           to be written"""
        return _copy.copy(self._checksums)

    def account_uid(self):
        """Return the UID of the account from which payment should be
           taken for the file storage
        """
        try:
            return self._account_uid
        except:
            return None

    @staticmethod
    def expand_source_and_destination(source, destination, root=None,
                                      ignore_hidden=True):
        """This function expands the passed source and destination objects
           into the list of absolute paths of local source files, and the
           full keys of those files once they are uploaded to the object
           store. This returns a pair of lists - the lists match the
           absolute path of the local file to the desired full key
           of the file in the object store
        """
        return _expand_source_destination(source, destination, root,
                                          ignore_hidden)

    def accounting_service_url(self):
        """Return the canonical URL of the service holding the account"""
        try:
            return self._accounting_service_url
        except:
            return None

    def to_data(self):
        """Return this request as a json-serialisable dictionary"""
        if self.is_null():
            return {}

        data = super().to_data()
        data["uid"] = self._uid
        data["destination_keys"] = self._destination_keys
        data["file_sizes"] = self._file_sizes
        data["checksums"] = self._checksums
        data["authorisation"] = self._authorisation.to_data()
        data["account_uid"] = self._account_uid
        data["accounting_service_url"] = self._accounting_service_url

        # don't write self._source_filenames as this contains
        # potentially sensitive local data that is not needed
        # by the cloud object store

        return data

    @staticmethod
    def from_data(data):
        f = FileWriteRequest()

        if (data and len(data) > 0):
            f._uid = data["uid"]
            f._destination_keys = data["destination_keys"]
            f._file_sizes = data["file_sizes"]
            f._checksums = data["checksums"]
            f._authorisation = _Authorisation.from_data(data["authorisation"])
            f._account_uid = data["account_uid"]
            f._accounting_service_url = data["accounting_service_url"]

        return f
