
import oci as _oci
import os as _os

__all__ = ["Account"]

class Account:
    @staticmethod
    def get_login(login):
        """This function turns the passed login details into
           a valid oci login, and actually logs in :-) """

        # first, we need to convert the 'login' so that it puts
        # the private key into a file
        keyfile = "/tmp/key.pem"

        try:
            FILE = open(keyfile, "w")

            for line in login["key_lines"]:
                FILE.write(line)
            
            FILE.close()                    
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
