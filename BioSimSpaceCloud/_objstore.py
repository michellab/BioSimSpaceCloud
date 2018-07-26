
import io as _io
import datetime as _datetime
import uuid as _uuid

__all__ = [ "ObjectStore" ]

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
