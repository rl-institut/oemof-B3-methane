# coding: utf-8
r"""
Inputs
-------
scenario_specs : str
    ``scenarios/{scenario}.yml``: path of input file (.yml) containing scenario specifications
destination : str
    ``results/{scenario}/preprocessed``: path of output directory
logfile : str
    ``logs/{scenario}.log``: path to logfile

Outputs
---------
oemoflex.EnergyDatapackage
    EnergyDatapackage that can be read by oemof.tabular, with data (scalars and timeseries)
    as csv and metadata (describing resources and foreign key relations) as json.

Description
-------------
The script creates an empty EnergyDatapackage from the specifications given in the scenario_specs,
fills it with scalar and timeseries data, infers the metadata and saves it to the given destination.
Further, additional parameters like emission limit are saved in a separate file.
"""
import os
import sys
from oemof_b3.config import config
from oemoflex.model.datapackage import EnergyDataPackage
from oemoflex.model.variations import EDPSensitivity
from oemof_b3.model import foreign_keys_update
from SALib.sample import latin


if __name__ == "__main__":
    path_lb = sys.argv[1]

    path_ub = sys.argv[2]

    destination = sys.argv[3]

    n = int(sys.argv[4])

    logfile = sys.argv[5]

    logger = config.add_snake_logger(logfile, "build_linear_slide")

    if not os.path.exists(destination):
        os.mkdir(destination)

    lb = EnergyDataPackage.from_metadata(os.path.join(path_lb, "datapackage.json"))
    ub = EnergyDataPackage.from_metadata(os.path.join(path_ub, "datapackage.json"))

    lb.stack_components()
    ub.stack_components()

    sensitivity = EDPSensitivity(lb, ub)

    logger.info(f"Creating {n} samples.")
    samples = sensitivity.get_salib_samples(latin.sample, N=n)

    for n_sample, sample in samples.items():

        sample.unstack_components()

        path = os.path.join(destination, str(n_sample), "preprocessed")

        sample.basepath = path

        sample.to_csv_dir(path)

        sample.infer_metadata(foreign_keys_update)
