
import io as _io
import datetime as _datetime
import uuid as _uuid
import json as _json
import os as _os

from ._account import Account as _Account
from ._service import Service as _Service

try:
    import oci as _oci
    has_oci = True
except:
    has_oci = False

__all__ = [ "ObjectStore", "get_service_info",
            "login_to_service_account", "get_service_private_key",
            "get_service_private_certificate", "get_service_public_key",
            "get_service_public_certificate",
            "ServiceAccountError", "MissingServiceAccountError" ]

class ObjectStoreError(Exception):
    pass

class ObjectStore:

    @staticmethod
    def get_object_as_file(bucket, key, filename):
        """Get the object contained in the key 'key' in the passed 'bucket'
           and writing this to the file called 'filename'"""

        try:
            response = bucket["client"].get_object(bucket["namespace"],
                                                   bucket["bucket_name"],
                                                   key)
            is_chunked = False
        except:
            try:
                response = bucket["client"].get_object(bucket["namespace"],
                                                       bucket["bucket_name"],
                                                       "%s/1" % key)
                is_chunked = True
            except:
                is_chunked = False
                pass
                
            if not is_chunked:
                raise

        if not is_chunked:
            with open(filename, 'wb') as f:
                for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
                    f.write(chunk)

            return filename

        # the data is chunked - get this out chunk by chunk
        with open(filename, 'wb') as f:
            next_chunk = 1
            while True:
                for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
                    f.write(chunk)

                # now get and write the rest of the chunks
                next_chunk += 1
                
                try:
                    response = bucket["client"].get_object(bucket["namespace"],
                                                           bucket["bucket_name"],
                                                           "%s/%d" % (key,next_chunk))
                except:
                    break
                                                           
    @staticmethod
    def get_object(bucket, key):
        """Return the binary data contained in the key 'key' in the
           passed bucket"""

        try:
            response = bucket["client"].get_object(bucket["namespace"],
                                                   bucket["bucket_name"],
                                                   key)
            is_chunked = False
        except:
            try:
                response = bucket["client"].get_object(bucket["namespace"],
                                                       bucket["bucket_name"],
                                                       "%s/1" % key)
                is_chunked = True
            except:
                is_chunked = False
                pass

            # Raise the original error
            if not is_chunked:
                raise

        data = None

        for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
            if not data:
                data = chunk
            else:
                data += chunk

        if is_chunked:
            # keep going through to find more chunks
            next_chunk = 1
            
            while True:
                next_chunk += 1
                
                try:
                    response = bucket["client"].get_object(bucket["namespace"],
                                                           bucket["bucket_name"],
                                                           "%s/%d" % (key,next_chunk))
                except:
                    response = None
                    break

                for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
                    if not data:
                        data = chunk
                    else:
                        data += chunk

        return data

    @staticmethod
    def get_string_object(bucket, key):
        """Return the string in 'bucket' associated with 'key'"""
        return ObjectStore.get_object(bucket, key).decode("utf-8")

    @staticmethod
    def get_object_from_json(bucket, key):
        """Return an object constructed from json stored at 'key' in
           the passed bucket. This returns None if there is no data
           at this key
        """

        data = None

        try:
            data = ObjectStore.get_string_object(bucket,key)
        except:
            return None

        return _json.loads(data)

    @staticmethod
    def get_all_object_names(bucket, prefix=None):
        """Returns the names of all objects in the passed bucket"""
        objects = bucket["client"].list_objects(bucket["namespace"],
                                                bucket["bucket_name"],
                                                prefix=prefix).data

        names = []

        for object in objects.objects:
            if prefix:
                if object.name.startswith(prefix):
                    names.append( object.name[len(prefix)+1:] )
            else:
                names.append( object.name )

        return names

    @staticmethod
    def get_all_objects(bucket, prefix=None):
        """Return all of the objects in the passed bucket"""

        objects = {}
        names = ObjectStore.get_all_object_names(bucket, prefix)

        if prefix:
            for name in names:
                objects[name] = ObjectStore.get_object(bucket, "%s/%s" % (prefix,name))
        else:
            for name in names:
                objects[name] = ObjectStore.get_object(bucket, name)

        return objects

    @staticmethod
    def get_all_strings(bucket, prefix=None):
        """Return all of the strings in the passed bucket"""

        objects = ObjectStore.get_all_objects(bucket, prefix)

        names = list(objects.keys())

        for name in names:
            try:
                s = objects[name].decode("utf-8")
                objects[name] = s
            except:
                del objects[name]

        return objects

    @staticmethod
    def set_object(bucket, key, data):
         """Set the value of 'key' in 'bucket' to binary 'data'"""
         f = _io.BytesIO(data)

         obj = bucket["client"].put_object(bucket["namespace"],
                                           bucket["bucket_name"],
                                           key, f)

    @staticmethod
    def set_object_from_file(bucket, key, filename):
        """Set the value of 'key' in 'bucket' to equal the contents
           of the file located by 'filename'"""

        with open(filename, 'rb') as f:
            obj = bucket["client"].put_object(bucket["namespace"], 
                                              bucket["bucket_name"], 
                                              key, f)

    @staticmethod
    def set_string_object(bucket, key, string_data):
        """Set the value of 'key' in 'bucket' to the string 'string_data'"""
        ObjectStore.set_object(bucket, key, string_data.encode("utf-8"))

    @staticmethod
    def set_object_from_json(bucket, key, data):
        """Set the value of 'key' in 'bucket' to equal to contents
           of 'data', which has been encoded to json"""
        ObjectStore.set_string_object(bucket, key, _json.dumps(data))
 
    @staticmethod
    def log(bucket, message, prefix="log"):
         """Log the the passed message to the object store in 
            the bucket with key "key/timestamp" (defaults
            to "log/timestamp"
         """

         ObjectStore.set_string_object(
                bucket, "%s/%s" % (prefix,_datetime.datetime.utcnow().timestamp()),
                           str(message))

    @staticmethod
    def delete_all_objects(bucket, prefix=None):
        """Deletes all objects..."""

        if prefix:
            for object in ObjectStore.get_all_object_names(bucket,prefix):
                if len(object) == 0:
                    bucket["client"].delete_object(bucket["namespace"],
                                                   bucket["bucket_name"],
                                                   prefix)
                else:
                    bucket["client"].delete_object(bucket["namespace"],
                                                   bucket["bucket_name"],
                                                   "%s/%s" % (prefix,object))
        else:
            for object in ObjectStore.get_all_object_names(bucket):
                bucket["client"].delete_object(bucket["namespace"], 
                                               bucket["bucket_name"],
                                               object)

    @staticmethod
    def get_log(bucket, log="log"):
        """Return the complete log as an xml string"""
        objs = ObjectStore.get_all_strings(bucket, log)

        lines = []
        lines.append("<log>")

        timestamps = list(objs.keys())
        timestamps.sort()

        for timestamp in timestamps:
            lines.append( "<logitem>" )
            lines.append( "<timestamp>%s</timestamp>" % \
                    _datetime.datetime.fromtimestamp(float(timestamp)) )
            lines.append( "<message>%s</message>" % objs[timestamp] )
            lines.append( "</logitem>" )

        lines.append("</log>")

        return "".join(lines)

    @staticmethod
    def clear_log(bucket, log="log"):
        """Clears out the log"""
        ObjectStore.delete_all_objects(bucket, log)

    @staticmethod
    def delete_object(bucket, key):
        """Removes the object at 'key'"""
        try:
            bucket["client"].delete_object(bucket["namespace"],
                                                   bucket["bucket_name"],
                                                   key)
        except:
            pass

    @staticmethod
    def clear_all_except(bucket, keys):
        """Removes all objects from the passed 'bucket' except those
           whose keys are or start with any key in 'keys'"""

        names = ObjectStore.get_all_object_names(bucket)

        for name in names:
            remove = True

            for key in keys:
                if name.startswith(key):
                    remove = False
                    break

            if remove:
                bucket["client"].delete_object(bucket["namespace"],
                                               bucket["bucket_name"],
                                               name)

class ServiceAccountError(Exception):
   pass

class MissingServiceAccountError(ServiceAccountError):
   pass

def get_service_info(bucket=None, need_private_access=False):
    """Return the service info object for this service. If private
       access is needed then this will decrypt and access the private
       keys and signing certificates, which is slow if you just need
       the public certificates.
    """

    if bucket is None:
        bucket = login_to_service_account()

    # find the service info from the object store
    service_key = "_service_info"

    service = ObjectStore.get_object_from_json(bucket, service_key)

    if not service:
        raise MissingServiceAccountError("You haven't yet created the service account "
                                         "for this service. Please create an account first.")

    if need_private_access:
        service_password = _os.getenv("SERVICE_PASSWORD")

        if service_password is None:
            raise ServiceAccountError("You must supply a $SERVICE_PASSWORD")

        service = _Service.from_data(service, service_password)
    else:
        service = _Service.from_data(service)

    return service

def login_to_service_account():
    """This function logs into the object store account of the service account.
       Accessing the object store means being able to access 
       all resources and which can authorise the creation
       of access all resources on the object store. Obviously this is
       a powerful account, so only log into it if you need it!!!

       The login information should not be put into a public 
       repository or stored in plain text. In this case,
       the login information is held in an environment variable
       (which should be encrypted or hidden in some way...)
    """

    # get the login information in json format from
    # the LOGIN_JSON environment variable
    access_json = _os.getenv("LOGIN_JSON")
    access_data = None

    # get the bucket information in json format from
    # the BUCKET_JSON environment variable
    bucket_json = _os.getenv("BUCKET_JSON")
    bucket_data = None

    if bucket_json and len(bucket_json) > 0:
        try:
            bucket_data = _json.loads(bucket_json)
            bucket_json = None
        except:
            raise ServiceAccountError(
             "Cannot decode the bucket information for the central service account")
    else:
        raise ServiceAccountError("You must supply valid bucket data!")

    if access_json and len(access_json) > 0:
        try:
            access_data = _json.loads(access_json)
            access_json = None
        except:
            raise ServiceAccountError(
             "Cannot decode the login information for the central service account")
    else:
        raise ServiceAccountError("You must supply valid login data!")

    # now login and create/load the bucket for this account
    try:
        account_bucket = _Account.create_and_connect_to_bucket(access_data,
                                                    bucket_data["compartment"],
                                                    bucket_data["bucket"])
    except Exception as e:
        raise ServiceAccountError(
             "Error connecting to the service account: %s" % str(e))

    return account_bucket

def get_service_private_key():
    """This function returns the private key for this service"""
    return get_service_info(need_private_access=True).private_key()

def get_service_private_certificate():
    """This function returns the private signing certificate for this service"""
    return get_service_info(need_private_access=True).private_certificate()

def get_service_public_key():
    """This function returns the public key for this service"""
    return get_service_info(need_private_access=False).public_key()

def get_service_public_certificate():
    """This function returns the public certificate for this service"""
    return get_service_info(need_private_access=False).public_certificate()

