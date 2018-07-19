# coding: utf-8
# Copyright (c) 2016, 2018, Oracle and/or its affiliates. All rights reserved.

import filecmp
import oci
import sys

config = oci.config.from_file()

# use the compartment ID of biosimspace_root
compartment_id = "ocid1.compartment.oc1..aaaaaaaat33j7w74mdyjenwoinyeawztxe7ri6qkfbm5oihqb5zteamvbpzq"
object_storage = oci.object_storage.ObjectStorageClient(config)

namespace = object_storage.get_namespace().data
bucket_name = "test-gromacs-bucket"
object_name = sys.argv[1]
filename = sys.argv[2]

print('Retrieving file from object storage')
get_obj = object_storage.get_object(namespace, bucket_name, object_name)
with open(filename, 'wb') as f:
    for chunk in get_obj.data.raw.stream(1024 * 1024, decode_content=False):
        f.write(chunk)

