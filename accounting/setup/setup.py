
import json
import fdk
import os

from Acquire import ObjectStore, Service, unpack_arguments, call_function, \
                    create_return_value, pack_return_value, \
                    login_to_service_account, get_service_info, \
                    get_service_private_key, get_remote_service_info, \
                    set_trusted_service_info, get_trusted_service_info, \
                    remove_trusted_service_info, MissingServiceAccountError

class ServiceSetupError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function is called to handle admin setup
       of the service, e.g. setting admin passwords,
       introducing trusted services etc."""

    status = 0
    message = None
    provisioning_uri = None
    error = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

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
            remove_service = args["remove_service"]
        except:
            remove_service = None

        try:
            new_password = args["new_password"]
        except:
            new_password = None

        try:
            remember_device = args["remember_device"]
        except:
            remember_device = False

        # first, do we have an existing Service object? If not,
        # we grant access to the first user!
        bucket = login_to_service_account()

        # The data is stored in the object store at the key _service_info
        # and is encrypted using the value of $SERVICE_PASSWORD
        try:
            service = get_service_info(True)
        except MissingServiceAccountError:
            service = None

        if service:
            if not service.is_accounting_service():
                raise ServiceSetupError("Why is the accounting service info "
                      "for a service of type %s" % service.service_type())

            provisioning_uri = service.verify_admin_user(password,otpcode,
                                                         remember_device)
        else:
            # we need to create the service
            service_url = args["service_url"]
            service_type = "accounting"

            service = Service(service_type, service_url)
            provisioning_uri = service.set_admin_password(password)

            # write the service data, encrypted using the service password
            service_password = os.getenv("SERVICE_PASSWORD")
            if service_password is None:
                raise ServiceSetupError("You must supply $SERVICE_PASSWORD "
                          "to setup a new service!")

            service_data = service.to_data(service_password)
            ObjectStore.set_object_from_json(bucket, "_service_info", service_data)
            must_verify = False

        # we are definitely the admin user, so let's add or remove remote services
        if remove_service:
            log.append("Removing service '%s'" % remove_service)
            remove_trusted_service_info(remove_service)

        if new_service:
            service = get_remote_service_info(new_service)

            if new_service:
                log.append("Adding service '%s'" % new_service)
                set_trusted_service_info(new_service, service)

        status = 0
        message = "Success"

    except Exception as e:
        error = e

    return_value = create_return_value(status, message, log, error)
    
    if provisioning_uri:
        return_value["provisioning_uri"] = provisioning_uri

    return pack_return_value(return_value,args)

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
