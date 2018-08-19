
import os as _os
import sys as _sys
import getpass as _getpass
import pickle as _pickle
import glob as _glob
import re as _re
import base64 as _base64

from ._function import call_function as _call_function
from ._function import pack_arguments as _pack_arguments
from ._function import unpack_arguments as _unpack_arguments
from ._keys import PrivateKey as _PrivateKey
from ._otp import OTP as _OTP
from ._useraccount import UserAccount as _UserAccount
from ._service import Service as _Service

__all__ = [ "Wallet" ]

class LoginError(Exception):
    pass

class Wallet:
    """This class holds a wallet that can be used to simplify
       sending passwords and one-time-password (OTP) codes
       to an acquire identity service.

       This holds a wallet of passwords and (optionally)
       OTP secrets that are encrypted using a local keypair
       that is unlocked by a password supplied by the user locally.
    """
    def __init__(self):
        self._get_wallet_key()
        self._cache = {}
        self._service_info = {}

    def _wallet_dir(self):
        """Directory containing all of the wallet files"""
        homedir = _os.path.expanduser("~")

        walletdir = "%s/.acquire" % homedir

        if not _os.path.exists(walletdir):
            _os.mkdir(walletdir)

        return walletdir

    def _create_wallet_key(self, filename):
        """Create a new wallet key for the user"""
        
        print("Please enter a password to encrypt your wallet. ", end="")
        _sys.stdout.flush()
        password = _getpass.getpass()

        key = _PrivateKey()

        bytes = key.bytes(password)

        print("Please confirm the password. ", end="")
        _sys.stdout.flush()
        password2 = _getpass.getpass()

        if password != password2:
            print("The passwords don't match. Please try again.")
            self._create_wallet_key(filename)
            return

        # the passwords match - write this to the file
        with open(filename, "wb") as FILE:
            FILE.write(bytes)

        return key

    def _get_wallet_key(self):
        """Return the private key used to encrypt everything in the wallet.
           This will ask for the users password
        """
        try:
            return self._wallet_key
        except:
            pass

        wallet_dir = self._wallet_dir()

        keyfile = "%s/wallet_key.pem" % wallet_dir

        if not _os.path.exists(keyfile):
            self._wallet_key = self._create_wallet_key(keyfile)
            return self._wallet_key

        # read the keyfile and decrypt
        with open(keyfile, "rb") as FILE:
            bytes = FILE.read()

        # get the user password
        wallet_key = None
        while not wallet_key:
            print("Please enter your wallet password. ", end="")
            _sys.stdout.flush()
            password = _getpass.getpass()

            try:
                wallet_key = _PrivateKey.read_bytes(bytes, password)
            except:
                print("Invalid password. Please try again.")

        self._wallet_key = wallet_key
        return wallet_key

    def _get_userfile(self, username):
        """Return the userfile for the passed username"""
        return "%s/user_%s_encrypted" % (self._wallet_dir(),
                                         UserAccount.sanitise_username(username))

    def _read_userfile(self, filename):
        """Read all info from the passed userfile"""
        try:
            return self._cache[filename]
        except:
            pass

        with open(filename, "rb") as FILE:
            data = _pickle.load(FILE)
            self._cache[filename] = data
            return data

    def _read_userinfo(self, username):
        """Read all info for the passed user"""
        return self._read_userfile( self._get_userfile(username) )

    def _get_username(self):
        """Function to find a username automatically, of if that fails,
           to ask the user
        """
        wallet_dir = self._wallet_dir()

        userfiles = _glob.glob("%s/user_*_encrypted" % wallet_dir)

        usernames = []

        for userfile in userfiles:
            try:
                usernames.append( self._read_userfile(userfile)["username"] )
            except:
                pass
    
        if len(usernames) == 1:
            return usernames[0]

        if len(usernames) == 0:
            print("Please type your username: ", end="")
            _sys.stdout.flush()
            return _sys.stdin.readline()[0:-1]

        print("Please choose the account by typing in its number, "
              "or type a new username if you want a different account.")

        for (i,username) in enumerate(usernames):
            print("[%d] %s" % (i,username))

        username = None

        while not username:
            print("Make your selection: ", end="")
            _sys.stdout.flush()

            input = _sys.stdin.readline()[0:-1]

            try:
                input = int(input)
                if input < 0 or input >= len(usernames):
                    print("Invalid account. Try again...")
                else:
                    username = usernames[input]
            except:
                pass

            username = input

        return username

    def _get_user_password(self,username):
        """Get the user password. If remember_device then save the 
           password in the wallet if it is not already there
        """
        try:
            password = self._read_userinfo(username)["password"]

            # this needs to be decrypted
            return self._wallet_key.decrypt(password).decode("utf-8")
        except:
            pass

        print("Please enter the login password: ", end="")
        _sys.stdout.flush()
        return _getpass.getpass()

    def _get_otpcode(self, username):
        """Get the OTP code for this user account"""
        try:
            secret = self._read_userinfo(username)
            secret = self._wallet_key.decrypt(secret).encode("utf-8")
            return _pyotp.totp.TOTP(secret).now()
        except:
            pass

        print("Please enter the one-time-password code: ", end="")
        _sys.stdout.flush()
        return _getpass.getpass()

    def _get_service_info(self, identity_service):
        """Return the service info for the passed identity service"""
        try:
            return self._service_info[identity_service]
        except:
            pass

        # can we read this from a file?
        service_file = "%s/service_%s" % (self._wallet_dir(), 
                         _base64.b64encode(identity_service.encode("utf-8")).decode("utf-8"))

        try:
            with open(service_file, "rb") as FILE:
                service_info = _Service.from_data(_unpack_arguments(FILE.read()))
                self._service_info[identity_service] = service_info
                return service_info
        except:
            pass

        try:
            key = _PrivateKey()
            response = _call_function(identity_service, {}, response_key=key)
            service = _Service.from_data(response["service_info"])
        except Exception as e:
            raise LoginError("Error connecting to the login service %s: Error = %s" % \
                  (identity_service,str(e)))

        if not service.is_identity_service():
            raise LoginError("You cannot log into something that is not "
                   "a valid identity service!")

        self._service_info[identity_service] = service

        # save this for future reference
        with open(service_file, "wb") as FILE:
            FILE.write(_pack_arguments(service.to_data()))

        return service

    def _get_service_key(self, identity_service):
        """Return the public encryption key for the passed identity service"""
        return self._get_service_info(identity_service).public_key()

    def send_password(self, url, username=None, remember_device=False):
        """Send a password and one-time code to the supplied login url"""

        # the login URL is of the form "server/code"
        words = url.split("/")
        identity_service = "/".join(words[0:-1])
        short_uid = words[-1]

        # get the public key of this identity service
        service_key = self._get_service_key(identity_service)
        
        if not username:
            # choose a username from any existing files...
            username = self._get_username()

        print("Logging in using username '%s'" % username)
        password = self._get_user_password(username)
        otpcode = self._get_otpcode(username)

        args = { "username" : username,
                 "password" : password,
                 "otpcode" : otpcode,
                 "remember_device" : remember_device,
                 "short_uid" : short_uid }

        try:
            key = _PrivateKey()
            response = _call_function("%s/login" % identity_service, args,
                                      args_key=service_key, response_key=key)
        except Exception as e:
            print("Failed to log in! Error is %s" % str(e))



        print("Logging in to '%s', session '%s'" % (identity_service,session_uid))
 
        return response
        
