"""
Modules that separates out all of the code to run a gromacs
simulation away from the code used to interface with Fn

@author Christopher Woods
"""

import os
import sys

def log(message):
    sys.stderr.write(message)
    sys.stderr.write("\n")

def run(data):
    log("Running a gromacs simulation!\n")

    return (0, "Simulation complete")
