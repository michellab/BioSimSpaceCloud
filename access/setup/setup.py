
import json
import fdk
import os

from Acquire import ObjectStore, Service, unpack_arguments, call_function, \
                    create_return_value, pack_return_value, \
                    login_to_service_account, get_service_info, \
                    get_service_private_key, MissingServiceAccountError

class ServiceSetupError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function is called to handle admin setup
       of the service, e.g. setting admin passwords,
       introducing trusted services etc."""

    status = 0
    message = None
    provisioning_uri = None

    log = []

    args = unpack_arguments(data) #, get_service_private_key)

    try:
        try:
            password = args["password"]
        except:
            password = None

        try:
            otpcode = args["otpcode"]
        except:
            otpcode = None

        try:
            new_service = args["new_service"]
        except:
            new_service = None

        try:
            new_password = args["new_password"]
        except:
            new_password = None

        # first, do we have an existing Service object? If not,
        # we grant access to the first user!
        bucket = login_to_service_account()

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
            service_url = args["service_url"]
            service_type = "access"

            service = Service(service_type, service_url)
            provisioning_uri = service.set_admin_password(password)

            # write the service data, encrypted using the service password
            service_password = os.getenv("SERVICE_PASSWORD")
            if service_password is None:
                raise ServiceSetupError("You must supply $SERVICE_PASSWORD "
                          "to setup a new service!")

            service = service.to_data(service_password)
            ObjectStore.set_object_from_json(bucket, "_service_info", service)
            service = Service.from_data(service)
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

    return_value = create_return_value(status, message, log)
    
    if provisioning_uri:
        return_value["provisioning_uri"] = provisioning_uri

    if log:
        return_value["log"] = log

    return pack_return_value(return_value,args)

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
