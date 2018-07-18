# coding: utf-8
# Copyright (c) 2016, 2018, Oracle and/or its affiliates. All rights reserved.

import filecmp
import oci
from oci.object_storage.models import CreateBucketDetails

config = oci.config.from_file()
# use the compartment ID of biosimspace_root
compartment_id = "ocid1.compartment.oc1..aaaaaaaat33j7w74mdyjenwoinyeawztxe7ri6qkfbm5oihqb5zteamvbpzq"
object_storage = oci.object_storage.ObjectStorageClient(config)

namespace = object_storage.get_namespace().data
bucket_name = "test-gromacs-bucket"
object_name = "input"
filename = sys.argv[1]

# Then upload the file to Object Storage
with open(filename, 'rb') as f:
    obj = object_storage.put_object(namespace, bucket_name, object_name, f)

