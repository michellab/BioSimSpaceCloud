
from Acquire.Identity import Authorisation as _Authorisation

__all__ = ["Request"]


class Request:
    """This is the base class for all resource request classses. These
       classes are used to transmit information about a resource
       request, together with the user authorisation and account
       from which payment for the resource should be taken
    """
    def __init__(self):
        """Construct the resource request"""
        pass

    def is_null(self):
        """Return whether or not this request is null"""
        return True

    def to_data(self):
        """Return this class as a json-serialisable dictionary"""
        data = {}

        data["class"] = str(self.__class__.__name__)

        return data

    @staticmethod
    def from_data(data):
        """Construct a Request from the data in the json-deserialised
           dictionary
        """

        if (data and len(data) > 0):
            try:
                classname = data["class"]
            except:
                return Request()

            if classname == "FileWriteRequest":
                from ._filewriterequest import FileWriteRequest \
                                            as _FileWriteRequest
                return _FileWriteRequest.from_data(data)
            else:
                raise TypeError("Unknown type '%s'" % classname)

        return Request()
