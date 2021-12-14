# coding: utf-8
r"""
Inputs
-------
preprocessed : str
    ``results/{scenario}/preprocessed``
optimized : str
    ``results/{scenario}/optimized/``

Outputs
---------
es.dump
    oemof.solph.EnergySystem with results, meta-results and parameters

Description
-------------
Given an EnergyDataPackage, this script creates an oemof.solph.EnergySystem and an
oemof.solph.Model, which is optimized. The EnergySystem with results, meta-results and parameters
is saved.
"""
import os
import sys

from oemof.solph import EnergySystem, Model
from oemof.outputlib import processing

# DONT REMOVE THIS LINE!
# pylint: disable=unusedimport
from oemof.tabular import datapackage  # noqa
from oemof.tabular.facades import TYPEMAP


if __name__ == "__main__":
    preprocessed = sys.argv[1]

    optimized = sys.argv[2]

    filename_metadata = "datapackage.json"

    solver = "cbc"

    if not os.path.exists(optimized):
        os.mkdir(optimized)

    es = EnergySystem.from_datapackage(
        os.path.join(preprocessed, filename_metadata), attributemap={}, typemap=TYPEMAP
    )

    # create model from energy system (this is just oemof.solph)
    m = Model(es)

    # select solver 'gurobi', 'cplex', 'glpk' etc
    m.solve(solver=solver)

    # get the results from the the solved model(still oemof.solph)
    es.meta_results = processing.meta_results(m)
    es.results = processing.results(m)
    es.params = processing.parameter_as_dict(es)

    # dump the EnergySystem
    es.dump(optimized)
