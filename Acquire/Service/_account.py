
import os as _os
import uuid as _uuid

try:
    import oci as _oci
    from oci.object_storage.models import CreateBucketDetails as _CreateBucketDetails
    _has_oci = True
except:
    _has_oci = False

from ._errors import AccountError

__all__ = ["Account"]

class Account:
    @staticmethod
    def _assert_valid_login_dict(login):
        """This function validates that the passed login dictionary
           contains all of the keys needed to login"""

        if login is None:
            raise AccountError( "You need to supply login credentials!" )

        if not isinstance(login, dict):
            raise AccountError( "You need to supply a valid login credential dictionary!" )

        needed_keys = [ "user", "key_lines", "fingerprint",
                        "tenancy", "region", "pass_phrase" ]

        missing_keys = []

        for key in needed_keys:
            if not key in login:
                missing_keys.append(key)

        if len(missing_keys) > 0:
            raise AccountError( "Cannot log in as the login dictionary " +
                                "is missing the following data: %s" % str(missing_keys) )

    @staticmethod
    def get_login(login):
        """This function turns the passed login details into
           a valid oci login, and actually logs in :-) """

        # validate that all of the information is held in the
        # 'login' dictionary
        Account._assert_valid_login_dict(login)

        # first, we need to convert the 'login' so that it puts
        # the private key into a file
        keyfile = "/tmp/key.pem"

        try:
            with open(keyfile, "w") as FILE:
                for line in login["key_lines"]:
                    FILE.write(line)
            
            _os.chmod(keyfile, 0o0600)

            del login["key_lines"]
            login["key_file"] = keyfile

            # validate the config is ok
            _oci.config.validate_config(login)

        except:
            _os.remove(keyfile)
            raise

        return login

    @staticmethod
    def _sanitise_bucket_name(bucket_name):
        """This function sanitises the passed bucket name. It will always
           return a valid bucket name. If "None" is passed, then a new,
           unique bucket name will be generated"""
        
        if bucket_name is None:
            return str(_uuid.uuid4())

        return "_".join(bucket_name.split())

    @staticmethod
    def create_and_connect_to_bucket(login_details, compartment, bucket_name=None):
        """Connect to the object store compartment 'compartment'
	   using the passed 'login_details', and create a bucket
           called 'bucket_name". Return a handle to the
	   created bucket. If the bucket already exists this will return
           a handle to the existing bucket"""

        login = Account.get_login(login_details)
        bucket = {}
        client = None

        try:
            client = _oci.object_storage.ObjectStorageClient(login)

            bucket["client"] = client
            bucket["compartment_id"] = compartment

            namespace = client.get_namespace().data
            bucket["namespace"] = namespace
            bucket["bucket_name"] = bucket_name

            try:
                request = _CreateBucketDetails()
                request.compartment_id = compartment
                request.name = Account._sanitise_bucket_name(bucket_name)

                bucket["bucket"] = client.create_bucket(
                                            client.get_namespace().data,
                                            request).data
            except Exception as e1:
                # couldn't create the bucket - likely because it already
                # exists - try to connect to the existing bucket
                try:
                    bucket["bucket"] = client.get_bucket(namespace, bucket_name).data
                except Exception as e:
                    raise AccountError("Cannot access the bucket '%s' : %s (originally %s)" % \
                                       (bucket_name, str(e), str(e1)))
        except:
            _os.remove( _os.path.abspath(login["key_file"]) )
            raise

        _os.remove( _os.path.abspath(login["key_file"]) )

        return bucket


    @staticmethod
    def connect_to_bucket( login_details, compartment, bucket_name ):
        """Connect to the object store compartment 'compartment'
           using the passed 'login_details', returning a handle to the 
           bucket associated with 'bucket'"""

        login = Account.get_login(login_details)
        bucket = {}

        try:
            client = _oci.object_storage.ObjectStorageClient(login)
            bucket["client"] = client
            bucket["compartment_id"] = compartment

            namespace = client.get_namespace().data
            bucket["namespace"] = namespace

            bucket["bucket"] = client.get_bucket(namespace, bucket_name).data
            bucket["bucket_name"] = bucket_name
        except:
            _os.remove( _os.path.abspath(login["key_file"]) )
            raise

        _os.remove( _os.path.abspath(login["key_file"]) )

        return bucket
