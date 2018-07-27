
__all__ = ["UserAccount"]

class UsernameError(Exception):
    pass

class ExistingAccountError(Exception):
    pass

class UserAccount:
    """This class holds all information about a user's account,
       e.g. their username, the sanitised username for the person
       on the system, their account keys, status etc.

       This data can be serialised to an from json to allow
       easy saving a retrieval from an object store
    """

    def __init__(self, username=None):
        """Construct from the passed username"""
        self._username = username
        self._sanitised_username = UserAccount.sanitise_username(username)
        self._privkey = None
        self._pubkey = None

        if username is None:
            self._status = None
        else:
            self._status = "disabled"

    def __str__(self):
        return "UserAccount( name : %s )" % self._username

    def name(self):
        """Return the name of this account"""
        return self._username

    def sanitised_name(self):
        """Return the sanitised username"""
        return self._sanitised_username

    def is_valid(self):
        """Return whether or not this is a valid account"""
        return not (self._status is None)

    def public_key(self):
        """Return the lines of the public key for this account"""
        return self._pubkey

    def	private_key(self):
       	"""Return the lines of the private key for this account"""
       	return self._privkey

    def status(self):
       	"""Return the status for this account"""
        if self._status is None:
            return "invalid"

       	return self._status

    def set_keys(self, privkey, pubkey):
        """Set the private and public keys for this account. The 
           keys can be set from files or from lines in a file.
           They are stored in this object as lines from the file,
           so the original files can be deleted if necessary
        """

        if self._status is None or privkey is None or pubkey is None:
            return

        try:
            privkey = open(privkey,"r").readlines()
        except:
            pass

        try:
            pubkey = open(pubkey,"r").readlines()
        except:
            pass

        self._privkey = privkey
        self._pubkey = pubkey

        self._status = "active"

    @staticmethod
    def sanitise_username(username):
        """This function returns a sanitised version of
           the username. This will ensure that the username
           is valid (must be between 3 and 50 characters) and
           will remove anything problematic for the object
           store
        """

        if username is None:
            return None

        if len(username) < 3 or len(username) > 50:
            raise UsernameError("The username must be between 3 and 50 characters!")

        return "_".join(username.split()).replace("/","") \
                  .replace("@","_AT_").replace(".","_DOT_")

    def to_data(self):
        """Return a data representation of this object (dictionary)"""
        if self._username is None:
            return None

        data = {}
        data["username"] = self._username
        data["private_key"] = self._privkey
        data["public_key"] = self._pubkey
        data["status"] = self._status

        return data

    @staticmethod 
    def from_data(data):
        """Return a UserAccount constructed from the passed
           data (dictionary)
        """

        if data is None:
            return None

        user_account = UserAccount(data["username"])
        user_account._privkey = data["private_key"]
        user_account._pubkey = data["public_key"]
        user_account._status = data["status"]

        return user_account
