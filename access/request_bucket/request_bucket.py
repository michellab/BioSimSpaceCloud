
import json

from Acquire.Service import unpack_arguments, create_return_value, \
                            pack_return_value
from Acquire.Service import login_to_service_account, Service, \
                            get_service_private_key
from Acquire.Service import call_function

from Acquire.Crypto import PrivateKey

from Acquire.ObjectStore import ObjectStore, string_to_bytes


class RequestBucketError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function is used to request access to a bucket for
       data in the object store. The user can request read-only
       or read-write access. Access is granted based on a permission
       list"""

    status = 0
    message = None
    log = []

    access_token = None

    args = unpack_arguments(data, get_service_private_key)

    try:
        user_uuid = args["user_uuid"]
        identity_service_url = args["identity_service"]
        request_data = string_to_bytes(args["request"])
        signature = string_to_bytes(args["signature"])

        # log into the central access account
        bucket = login_to_service_account()

        # is the identity service supplied by the user one that we trust?
        identity_service = Service.from_data(
                            ObjectStore.get_object_from_json(
                                bucket,
                                "services/%s" % identity_service_url))

        if not identity_service:
            raise RequestBucketError(
                    "You cannot request a bucket because "
                    "this access service does not know or trust your supplied "
                    "identity service (%s)" % identity_service_url)

        if not identity_service.is_identity_service():
            raise RequestBucketError(
                "You cannot request a bucket because "
                "the passed service (%s) is not an identity service. It is "
                "a %s" %
                (identity_service_url, identity_service.service_type()))

        # Since we trust this identity service, we can ask it to give us the
        # public certificate and signing certificate for this user.
        args = {"user_uuid": user_uuid}

        key = PrivateKey()

        response = call_function("%s/get_user_keys" % identity_service_url,
                                 args, args_key=identity_service.public_key(),
                                 response_key=key)

        status = 0
        message = "Success: Status = %s" % str(response)

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__, str(e))

    return_value = create_return_value(status, message, log)

    if access_token:
        return_value["access_token"] = access_token

    return pack_return_value(return_value, args)

if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
