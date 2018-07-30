This repository contains the code needed to build the Authentication,
Access and Accouting Infrastructure (AAAI) necessary to run 
BioSimSpace simulations on a function service run in the cloud.

The base library for this is called Acquire, as this should support
running such simulations for a wide range of different domains.

The subdirectories contain;

* Acquire: All of the shared code needed to implement the services
* user: Example scripts showing how the user can log into and access the service
* auth: The code needed to run the authentication service
* access: The code needed to run the access service
* accounting: The code needed to run the accounting service
* gromacs: The code needed to run gromacs on the function service
* oracle-k8s: Files needed to deploy services on the oracle k8s cluster

