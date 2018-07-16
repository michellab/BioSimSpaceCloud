"""
Modules that separates out all of the code to run a gromacs
simulation away from the code used to interface with Fn

@author Christopher Woods
"""

import os
import sys

def log(message):
    sys.stderr.write( str(message) )
    sys.stderr.write("\n")

def run(bucket):
    log("Running a gromacs simulation!\n")

    log(bucket)

    return (0, "Simulation complete")
