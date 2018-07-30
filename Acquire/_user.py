
from ._function import call_function as _call_function

__all__ = ["User"]

class User:
    """This class holds all functionality that would be used
       by a user to authenticate with and access the service
    """

    def __init__(self):
        """Construct a null user"""
        pass

    @staticmethod
    def requestLogin(auth_url, username):
        """Connect to the authentication URL at 'auth_url'
           and request a login to the account connected to 
           'username'. This will return a User object that 
           will hold all keys that will represent this login
        """
        result = _call_function(auth_url, {"username" : username})

        return result
