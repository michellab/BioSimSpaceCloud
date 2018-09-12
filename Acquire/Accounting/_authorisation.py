
__all__ = ["Authorisation"]


class Authorisation:
    """This class holds the information needed to authorise a transaction
       in an account
    """
    def __init__(self):
        pass

    @staticmethod
    def from_data(data):
        """Return an authorisation created from the json-decoded dictionary"""
        a = Authorisation()

        return a

    def to_data(self):
        """Return this object serialised to a json-encoded dictionary"""
        data = {}

        return data
