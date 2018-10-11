
from uuid import uuid4 as _uuid4
import copy as _copy
import os as _os
import hashlib as _hashlib

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


class FileWriteRequest(_Request):
    """This class holds a request to write a file (or files) to a remote
       object store
    """
    def __init__(self, filenames=None, filekeys=None, root_key=None,
                 account=None, testing_key=None):
        """Construct the request to write the files whose filenames are
           in 'filenames' to the object store. These will be written to
           the object store at keys based on the pass root_key and the name
           of the file (ignoring the file path). For example,
           /path/to/file.txt with root_key="root" will be written to
           /root/file.txt

           If you want to specify the object store keys yourself, then
           place them into the optional 'filekeys' list, which must have
           the same size as the filenames list.

           if 'root_key' is supplied, then all files will be written under
           'root_key' in the object store.

           You must pass the 'account' from which payment will be taken to
           write files to the object store.
        """
        super().__init__()

        self._filekeys = []
        self._filesizes = []
        self._checksums = []

        if filenames is not None:
            if filekeys is None:
                for filename in filenames:
                    (filesize, checksum) = _get_filesize_and_checksum(filename)
                    self._filekeys.append(_get_key(root_key, filename))
                    self._filesizes.append(filesize)
                    self._checksums.append(checksum)
            else:
                if len(filekeys) != len(filenames):
                    raise ValueError(
                        "The number of filenames (%d) must equal the number "
                        "of passed filekeys (%d)" %
                        (len(filenames), len(filekeys)))

                for i, filename in enumerate(filenames):
                    filekey = _clean_key(root_key, filekeys[i])
                    (filesize, checksum) = _get_filesize_and_checksum(filename)
                    self._filekeys.append(filekey)
                    self._filesizes.append(filesize)
                    self._checksums.append(checksum)

        if len(self._filekeys) == 0:
            self._uid = None
            return

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

    def filekeys(self):
        """Return the object store keys to which the files will be
           written
        """
        return _copy.copy(self._filekeys)

    def filesizes(self):
        """Return the sizes of the files that are requested to be written"""
        return _copy.copy(self.filesizes)

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
        data["filekeys"] = self._filekeys
        data["filesizes"] = self._filesizes
        data["checksums"] = self._checksums
        data["authorisation"] = self._authorisation.to_data()
        data["account_uid"] = self._account_uid
        data["accounting_service_url"] = self._accounting_service_url

        return data

    @staticmethod
    def from_data(data):
        f = FileWriteRequest()

        if (data and len(data) > 0):
            f._uid = data["uid"]
            f._filekeys = data["filekeys"]
            f._filesizes = data["filesizes"]
            f._checksums = data["checksums"]
            f._authorisation = _Authorisation.from_data(data["authorisation"])
            f._account_uid = data["account_uid"]
            f._accounting_service_url = data["accounting_service_url"]

        return f
