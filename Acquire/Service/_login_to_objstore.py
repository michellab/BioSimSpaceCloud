
import os as _os
import json as _json

from cachetools import cached as _cached
from cachetools import TTLCache as _TTLCache

from Acquire.ObjectStore import ObjectStore as _ObjectStore
from Acquire.ObjectStore import use_oci_object_store_backend as \
                                _use_oci_object_store_backend
from Acquire.ObjectStore import use_testing_object_store_backend as \
                                _use_testing_object_store_backend

from ._account import Account as _Account

from ._errors import ServiceAccountError

# The cache can hold a maximum of 50 objects, and will be renewed
# every 300 seconds (so any changes in this service's key would
# cause problems for a maximum of 300 seconds)
_cache = _TTLCache(maxsize=50, ttl=300)


__all__ = ["login_to_service_account"]


_current_testing_objstore = None


# Cache this function as the result changes very infrequently, as involves
# lots of round trips to the object store, and it will give the same
# result regardless of which Fn function on the service makes the call
@_cached(_cache)
def login_to_service_account(testing_dir=None):
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
    # the LOGIN_JSON environment variable
    access_json = _os.getenv("LOGIN_JSON")
    access_data = None
    has_access_data = False

    # get the bucket information in json format from
    # the BUCKET_JSON environment variable
    bucket_json = _os.getenv("BUCKET_JSON")
    bucket_data = None
    has_bucket_data = False

    if (bucket_json is None) or (access_json is None):
        # see if this is running in testing mode...
        global _current_testing_objstore
        if testing_dir:
            _current_testing_objstore = testing_dir
            return _use_testing_object_store_backend(testing_dir)
        elif _current_testing_objstore:
            return _use_testing_object_store_backend(_current_testing_objstore)

    if bucket_json and len(bucket_json) > 0:
        try:
            bucket_data = _json.loads(bucket_json)
            bucket_json = None
            has_bucket_data = True
        except:
            pass

    if access_json and len(access_json) > 0:
        try:
            access_data = _json.loads(access_json)
            access_json = None
            has_access_data = True
        except:
            pass

    if not (has_access_data and has_bucket_data):
        if testing_dir:
            return _use_testing_object_store_backend(testing_dir)
        else:
            raise ServiceAccountError(
                "You need to supply login credentials via the 'LOGIN_JSON' "
                "and 'BUCKET_JSON' environment variables! %s" % testing_dir)

    # we have OCI login details, so make sure that we are using
    # the OCI object store backend
    _use_oci_object_store_backend()

    # now login and create/load the bucket for this account
    try:
        account_bucket = _Account.create_and_connect_to_bucket(
                                access_data,
                                bucket_data["compartment"],
                                bucket_data["bucket"])
    except Exception as e:
        raise ServiceAccountError(
             "Error connecting to the service account: %s" % str(e))

    return account_bucket
