import fdk
import oci
import io
import sys
import datetime

def get_object_as_file(bucket, key, filename):
    """Get the object contained in the key 'key' in the passed 'bucket'
       and writing this to the file called 'filename'"""

    response = bucket["client"].get_object(bucket["namespace"],
                                           bucket["bucket_name"],
                                           key)

    with open(filename, 'wb') as f:
        for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
            f.write(chunk)

    return filename

def get_object(bucket, key):
     """Return the binary data contained in the key 'key' in the
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

def get_string_object(bucket, key):
    """Return the string in 'bucket' associated with 'key'"""
    return get_object(bucket, key).decode("utf-8")

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

def get_all_objects(bucket, prefix=None):
    """Return all of the objects in the passed bucket"""

    objects = {}
    names = get_all_object_names(bucket, prefix)

    if prefix:
        for name in names:
            objects[name] = get_object(bucket, "%s/%s" % (prefix,name))
    else:
        for name in names:
            objects[name] = get_object(bucket, name)

    return objects

def get_all_strings(bucket, prefix=None):
    """Return all of the strings in the passed bucket"""

    objects = get_all_objects(bucket, prefix)

    names = list(objects.keys())

    for name in names:
        try:
            s = objects[name].decode("utf-8")
            objects[name] = s
        except:
            del objects[name]

    return objects

def set_object(bucket, key, data):
     """Set the value of 'key' in 'bucket' to binary 'data'"""
     f = io.BytesIO(data)

     obj = bucket["client"].put_object(bucket["namespace"],
                                       bucket["bucket_name"],
                                       key, f)

def set_object_from_file(bucket, key, filename):
     """Set the value of 'key' in 'bucket' to equal the contents
        of the file located by 'filename'"""

     with open(filename, 'rb') as f:
        obj = bucket["client"].put_object(bucket["namespace"], 
                                          bucket["bucket_name"], 
                                          key, f)

def set_string_object(bucket, key, string_data):
     """Set the value of 'key' in 'bucket' to the string 'string_data'"""
     set_object(bucket, key, string_data.encode("utf-8"))

def log(bucket, message, prefix="log"):
     """Log the the passed message to the object store in 
        the bucket with key "key/timestamp" (defaults
        to "log/timestamp"
     """

     set_string_object(bucket, "%s/%s" % (prefix,datetime.datetime.utcnow().timestamp()),
                       str(message))

def delete_all_objects(bucket, prefix=None):
    """Deletes all objects..."""

    if prefix:
        for object in get_all_object_names(bucket,prefix):
            bucket["client"].delete_object(bucket["namespace"],
                                           bucket["bucket_name"],
                                           "%s/%s" % (prefix,object))
    else:
        for object in get_all_object_names(bucket):
            bucket["client"].delete_object(bucket["namespace"], 
                                           bucket["bucket_name"],
                                           object)

def get_log(bucket, log="log"):
    """Return the complete log as an xml string"""
    objs = get_all_strings(bucket, log)

    lines = []
    lines.append("<log>")

    timestamps = list(objs.keys())
    timestamps.sort()

    for timestamp in timestamps:
        lines.append( "<logitem>" )
        lines.append( "<timestamp>%s</timestamp>" % \
                datetime.datetime.fromtimestamp(float(timestamp)) )
        lines.append( "<message>%s</message>" % objs[timestamp] )
        lines.append( "</logitem>" )

    lines.append("</log>")

    return "".join(lines)

def clear_log(bucket, log="log"):
    """Clears out the log"""
    delete_all_objects(bucket, log)
