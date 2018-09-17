
__all__ = ["Authorisation"]


class Authorisation:
    """This class holds the information needed to authorise a transaction
       in an account
    """
    def __init__(self):
        pass

    def __str__(self):
        return "Authorisation()"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_data(data):
        """Return an authorisation created from the json-decoded dictionary"""
        a = Authorisation()

        return a

    def to_data(self):
        """Return this object serialised to a json-encoded dictionary"""
        data = {}

        return data
