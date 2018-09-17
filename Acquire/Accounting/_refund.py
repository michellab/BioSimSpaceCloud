
__all__ = ["Refund"]


class Refund:
    """This class is used to refund transactions"""
    def __init__(self):
        pass

    def to_data(self):
        """Return this object serialised to a json-compatible dictionary"""
        data = {}

        return data

    @staticmethod
    def from_data(data):
        """Return this object constructed from the passed json-compatible
           dictionary
        """
        refund = Refund()

        if (data and len(data) > 0):
            pass

        return refund
