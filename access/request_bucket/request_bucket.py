
import json
import fdk

from Acquire import ObjectStore, UserAccount, LoginSession, bytes_to_string
from accessaccount import loginToAccessAccount, getServicePrivateKey,
                          getServicePrivateCertificate

class RequestBucketError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function is used to request access to a bucket for 
       data in the object store. The user can request read-only
       or read-write access. Access is granted based on a permission
       list"""

    if not (data and len(data) > 0):
        return    

    status = 0
    message = None

    access_token = None

    try:
        # data is already a decoded unicode string
        data = json.loads(data)

        user_uuid = data["user_uuid"]
        identity_service_url = data["identity_service"]
        request_data = data["request"]
        signature = string_to_bytes( data["signature"] )

        # log into the central access account
        bucket = loginToAccessAccount()
        service = loginToService()

        # is the identity service supplied by the user one that we trust?
        identity_service = Service.from_data( ObjectStore.get_object_from_json(bucket,
                                              "services/%s" % identity_service_url))

        if not identity_service:
            raise RequestBucketError("You cannot request a bucket because "
                   "this access service does not know or trust your supplied "
                   "identity service (%s)" % identity_service_url)

        if not identity_service.is_identity_service():
            raise RequestBucketError("You cannot request a bucket because "
                   "the passed service (%s) is not an identity service. It is "
                   "a %s" % (identity_service_url,identity_service.service_type()))

        # Since we trust this identity service, we can ask it to give us the public
        # certificate and signing certificate for this user.
        args = { "user_uuid" : user_uuid }

        response = call_function("%s/get_user_keys" % identity_service_url,
                                 args, identity_service.public_key(),
                                 service.private_key())

        status = 0
        message = "Success: Status = %s" % str(response)

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__,str(e))

    response = {}
    response["status"] = status
    response["message"] = message
    
    return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
