
import json as _json
import oci as _oci
import os as _os

from Acquire import Account as _Account
from Acquire import ObjectStore as _ObjectStore
from Acquire import Service as _Service

class ServiceAccountError(Exception):
   pass

class MissingServiceAccountError(Exception):
   pass

_public_service_info = None
_private_service_info = None

def get_service_info(bucket=None, need_private_access=False):
    """Return the service info object for this service. If private
       access is needed then this will decrypt and access the private
       keys and signing certificates, which is slow if you just need
       the public certificates.
    """
    if bucket is None:
        bucket = login_to_service_account()

    if _private_service_info:
        return _private_service_info

    if not need_private_access:
        if _public_service_info:
            return _public_service_info

    # find the service info from the object store
    service_key = "_service_info"

    service = _ObjectStore.get_object_from_json(bucket, service_key)

    if not service:
        raise MissingServiceAccountError("You haven't yet created the service account "
                                         "for this service. Please create an account first.")

    if need_private_access:
        service_password = os.getenv("SERVICE_PASSWORD")

        if service_password is None:
            raise ServiceAccountError("You must supply a $SERVICE_PASSWORD")

        service = _Service.from_data(service, service_password)
        _private_service_info = service
    else:
        service = _Service.from_data(service)
        _public_service_info = service

    return service

_account_bucket = None

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

    if _account_bucket:
        return _account_bucket

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
        _account_bucket = _Account.create_and_connect_to_bucket(access_data,
                                                     bucket_data["compartment"],
                                                     bucket_data["bucket"])
    except Exception as e:
        raise ServiceAccountError(
             "Error connecting to the service account: %s" % str(e))

    return _account_bucket

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
