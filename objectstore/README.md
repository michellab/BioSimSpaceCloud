# Setting up the Oracle Object Store

The plan is to use Python (in Jupyter and Fn) to pass data between
the two services via the Oracle object store. I am now going to
try to set up Python scripts that can do this...

## The Oracle Cloud Infrastructure Python SDK

This is from [here](https://github.com/oracle/oci-python-sdk).

On the Oracle VM I have running...

```
# ssh opc@130.61.60.88
[opc@instance-fn-test ~]$
```

...I now type

```
[opc@instance-fn-test ~]$ sudo pip install upgrade pip
[opc@instance-fn-test ~]$ sudo pip install oci
[opc@instance-fn-test ~]$ python3.6
Python 3.6.3 (default, Jan  4 2018, 16:40:53) 
[GCC 4.8.5 20150623 (Red Hat 4.8.5-16)] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import oci
>>> 
>>> config = oci.config.from_file("~/.oci/config", "DEFAULT")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/lib/python3.6/site-packages/oci/config.py", line 77, in from_file
    raise ConfigFileNotFound("Could not find config file at {}".format(expanded_file_location))
oci.exceptions.ConfigFileNotFound: Could not find config file at /home/opc/.oci/config
```

## Setting up an API user account

The error is because I need to set up user credentials and an ID (OCID) for the
account used by the SDK. I need to generate a config file that contains
this based on the information given [here](https://docs.cloud.oracle.com/iaas/Content/API/Concepts/sdkconfig.htm).

First, I have created a normal account on the oracle cloud called "chryswoods".
The OCID of this account is `ocid1.user.oc1..aaaaaaaahxlrqhcgfzdv52ias5yt6go6ybgmb5hv7at5amepal22tagvaczq`.

I had to create the account to have full permissions in the `biosimspace_root`
compartment, in the group `biosimspace-admins` and with associated policies etc.
as described [here](https://docs.cloud.oracle.com/iaas/Content/GSG/Tasks/addingusers.htm).

The policy is;

```
Allow group biosimspace-admins to manage all-resources in compartment biosimspace_root
```

Next, I need to generate the correct openssl keys to connect to the api...

```
[opc@instance-fn-test ~]$ mkdir ~/.oci
[opc@instance-fn-test ~]$ openssl genrsa -out ~/.oci/oci_api_key.pem -aes128 2048
Generating RSA private key, 2048 bit long modulus
....................................................................+++
.+++
e is 65537 (0x10001)
Enter pass phrase for /home/opc/.oci/oci_api_key.pem:
Verifying - Enter pass phrase for /home/opc/.oci/oci_api_key.pem:
```

(I put in a passphrase). Next I have to ensure that only I can read the
private key...

```
[opc@instance-fn-test ~]$ chmod go-rwx ~/.oci/oci_api_key.pem
```

Now generate the public key...

```
[opc@instance-fn-test ~]$ openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
Enter pass phrase for /home/opc/.oci/oci_api_key.pem:
writing RSA key
```

Next, I need to get the key's fingerprint, using

```
[opc@instance-fn-test ~]$ openssl rsa -pubout -outform DER -in ~/.oci/oci_api_key.pem | openssl md5 -c
Enter pass phrase for /home/opc/.oci/oci_api_key.pem:
writing RSA key
(stdin)= 11:7e:8f:d4:2a:c8:73:e9:0c:e6:08:94:16:3b:72:e4
```

I then uploaded the public key to the cloud using the web interface and the
"Add Public Key" button under "Identity | Users | User Details | API Keys".

This displays the key's fingerprint on the screen :-)

Finally, from the web interface I can get the OCIDs of the tenancy and user account:

```
User account: ocid1.user.oc1..aaaaaaaahxlrqhcgfzdv52ias5yt6go6ybgmb5hv7at5amepal22tagvaczq 
Tenancy:      ocid1.tenancy.oc1..aaaaaaaa3eiex6fbfj626uwhs3dg24oygknrhhgfj4khqearluf4i74zdt2a
```

## Creating the OCI config file

I need to create the file `~/.oci/config` that provides the configuration for the 
CLI and python SDK. An example file is as follows;

```
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaat5nvwcna5j6aqzjcaty5eqbb6qt2jvpkanghtgdaqedqw3rynjq
fingerprint=20:3b:97:13:55:1c:5b:0d:d3:37:d8:50:4e:c5:3a:34
key_file=~/.oci/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..aaaaaaaaba3pv6wkcr4jqae5f15p2b2m2yt2j6rx32uzr4h25vqstifsfdsq
region=us-ashburn-1
```

I can adapt this for my account using

```
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaahxlrqhcgfzdv52ias5yt6go6ybgmb5hv7at5amepal22tagvaczq
fingerprint=11:7e:8f:d4:2a:c8:73:e9:0c:e6:08:94:16:3b:72:e4
key_file=~/.oci/oci_api_key.pem
pass_phrase=XXXXXX
tenancy=ocid1.tenancy.oc1..aaaaaaaa3eiex6fbfj626uwhs3dg24oygknrhhgfj4khqearluf4i74zdt2a
region=eu-frankfurt-1
```

(note that I had to add my key passphrase, which is in place of the `XXXXXX`)

## Connecting the Python SDK to Oracle

I am now ready to test if this can all connect. Here is the test script, with
output

```
[opc@instance-fn-test ~]$ python3.6
Python 3.6.3 (default, Jan  4 2018, 16:40:53) 
[GCC 4.8.5 20150623 (Red Hat 4.8.5-16)] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import oci
>>> config = oci.config.from_file("~/.oci/config", "DEFAULT")
>>> identity = oci.identity.IdentityClient(config)
>>> user = identity.get_user(config["user"]).data
>>> print(user)
{
  "compartment_id": "ocid1.tenancy.oc1..aaaaaaaa3eiex6fbfj626uwhs3dg24oygknrhhgfj4khqearluf4i74zdt2a",
  "defined_tags": {},
  "description": "chryswoods account for the biosimspace_root compartment",
  "freeform_tags": {},
  "id": "ocid1.user.oc1..aaaaaaaahxlrqhcgfzdv52ias5yt6go6ybgmb5hv7at5amepal22tagvaczq",
  "inactive_status": null,
  "lifecycle_state": "ACTIVE",
  "name": "chryswoods",
  "time_created": "2018-06-15T15:24:52.386000+00:00"
}
```

Yay - this is all working, at least from a VM that is running in the 
Oracle cloud :-)

## Testing from a non-Oracle VM

Can this work from a machine that is not in the Oracle cloud, e.g.
from cibod? I have copied the "~/.oci" directory from the VM
to cibod and have installed the oracle python SDK (`pip install oci`). Let's see
what happens...

```
[chris@cibod ~]$ python
Python 2.7.5 (default, Nov 20 2015, 02:00:19) 
[GCC 4.8.5 20150623 (Red Hat 4.8.5-4)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import oci
>>> config = oci.config.from_file("~/.oci/config", "DEFAULT")
>>> identity = oci.identity.IdentityClient(config)
>>> user = identity.get_user(config["user"]).data
>>> print(user)
{
  "compartment_id": "ocid1.tenancy.oc1..aaaaaaaa3eiex6fbfj626uwhs3dg24oygknrhhgfj4khqearluf4i74zdt2a", 
  "defined_tags": {}, 
  "description": "chryswoods account for the biosimspace_root compartment", 
  "freeform_tags": {}, 
  "id": "ocid1.user.oc1..aaaaaaaahxlrqhcgfzdv52ias5yt6go6ybgmb5hv7at5amepal22tagvaczq", 
  "inactive_status": null, 
  "lifecycle_state": "ACTIVE", 
  "name": "chryswoods", 
  "time_created": "2018-06-15T15:24:52.386000+00:00"
}
```

## Running an example that uploads/downloads from the object store

I am now going to try to upload and download files from the object store

