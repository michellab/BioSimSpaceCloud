
import json
import fdk
import os

from Acquire import ObjectStore, Service, call_function
from accessaccount import loginToAccessAccount, get_service_info

class ServiceSetupError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function is called to handle admin setup
       of the service, e.g. setting admin passwords,
       introducing trusted services etc."""

    if not (data and len(data) > 0):
        return    

    status = 0
    message = None
    provisioning_uri = None

    log = []

    try:
        # data is already a decoded unicode string
        data = json.loads(data)

        try:
            password = data["password"]
        except:
            password = None

        try:
            otpcode = data["otpcode"]
        except:
            otpcode = None

        try:
            new_service = data["new_service"]
        except:
            new_service = None

        try:
            new_password = data["new_password"]
        except:
            new_password = None

        # first, do we have an existing Service object? If not,
        # we grant access to the first user!
        bucket = loginToAccessAccount()

        # The data is stored in the object store at the key _service_info
        # and is encrypted using the value of $SERVICE_PASSWORD
        try:
            service = get_service_info(bucket, True)
        except MissingServiceAccountError:
            service = None

        if service:
            if not service.is_access_service():
                raise ServiceSetupError("Why is the accounting service info "
                      "for a service of type %s" % service.service_type())

            service.verify_admin_user(password,otpcode)
        else:
            # we need to create the service
            service_url = data["service_url"]
            service_type = "access"

            service = Service(service_type, service_url)
            provisioning_uri = service.set_admin_password(password)

            # write the service data, encrypted using the service password
            service_password = os.getenv("SERVICE_PASSWORD")
            if service_password is None:
                raise ServiceSetupError("You must supply $SERVICE_PASSWORD "
                          "to setup a new service!")

            service = service.to_data(service_password)
            ObjectStore.set_object_from_json(bucket, service_key, service)
            service = service.from_data(service_password)
            must_verify = False

        # we are definitely the admin user, so let's be introduced to
        # the new service (if requested)
        if new_service:
            response = call_function(new_service, {}, response_key=service.private_key())
            new_service_obj = Service.from_data( response["service_info"] )
            ObjectStore.set_object_from_json(bucket, "services/%s" % new_service,
                                             new_service_obj.to_data())

        status = 0
        message = "Success"

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__,str(e))

    response = {}
    response["status"] = status
    response["message"] = message
    
    if provisioning_uri:
        response["provisioning_uri"] = provisioning_uri

    if log:
        response["log"] = log

    return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
