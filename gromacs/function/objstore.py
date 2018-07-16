import fdk
import oci
import io
import datetime

def get_object(bucket, key):
     """Return the data contained in the key 'key' in the
        passed bucket"""

     response = bucket["client"].get_object(bucket["namespace"],
                                            bucket["bucket_name"],
                                            key)

     data = None

     for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
         if not data:
             data = chunk
         else:
             data += chunk

     return data

def get_all_object_names(bucket, prefix=None):
    """Returns the names of all objects in the passed bucket"""
    objects = bucket["client"].list_objects(bucket["namespace"],
                                            bucket["bucket_name"],
                                            prefix=prefix).data

    names = []

    for object in objects.objects:
        names.append( object.name )

    return names

def get_all_objects(bucket, prefix=None):
    """Return all of the objects in the passed bucket"""

    objects = {}
    names = get_all_object_names(bucket)

    for name in names:
        objects[name] = get_object(bucket, name)

    return objects

def set_string_object(bucket, key, string_data):
     """Set the value of 'key' in 'bucket' to the string 'string_data'"""
     f = io.StringIO(str(string_data))

     obj = bucket["client"].put_object(bucket["namespace"],
                                       bucket["bucket_name"],
                                       key, f)

def set_object(bucket, key, data):
     """Set the value of 'key' in 'bucket' to binary 'data'"""
     f = io.BytesIO(data)

     obj = bucket["client"].put_object(bucket["namespace"],
                                       bucket["bucket_name"],
                                       key, f)

def log(bucket, message, key="log"):
     """Log the the passed message to the object store in 
        the bucket with key "key/timestamp" (defaults
        to "log/timestamp"
     """

     set_string_object(bucket, "%s/%s" % (key,datetime.datetime.utcnow().timestamp()),
                       str(message))

def delete_all_objects(bucket, prefix=None):
    """Deletes all objects..."""

    for object in get_all_object_names(bucket, prefix):
        bucket["client"].delete_object(bucket["namespace"], 
                                       bucket["bucket_name"],
                                       object)

def get_log(bucket, log="log"):
    """Return the complete log as a list of lines"""
    objs = get_all_objects(bucket, log)

    lines = []
    timestamps = list(objs.keys())
    timestamps.sort()

    for timestamp in timestamps:
        lines.append("%s: %s" % (timestamp,objs[timestamp]))

    return lines

def clear_log(bucket, log="log"):
    """Clears out the log"""
    delete_all_objects(bucket, log)
