# coding: utf-8
r"""
Inputs
------
in_path : str
    ``results/joined_scenarios/{scenario_group}/joined/scalars.csv``: path to scalar results.
out_path : str
    ``results/joined_scenarios/{scenario_group}/joined_tables/``: target path for results tables.
logfile : str
    ``logs/{scenario}.log``: path to logfile

Outputs
-------
.csv
    Tables showing results.

Description
-----------
"""
import os
import sys

import pandas as pd

import oemof_b3.tools.data_processing as dp
from oemof_b3.config import config


def create_total_system_cost_table(scalars):
    df = scalars.copy()

    total_system_cost = dp.filter_df(df, "var_name", "total_system_cost")

    curtailment = dp.multi_filter_df(
        df, var_name="flow_in_electricity", tech="curtailment"
    )
    curtailment = dp.aggregate_scalars(curtailment, "region")
    curtailment["var_name"] = "curtailment"

    df = pd.concat([total_system_cost, curtailment])

    df = df.set_index(["scenario_key", "var_name"])

    df = df.loc[:, ["var_value"]]

    df = dp.round_setting_int(df, decimals={col: 0 for col in df.columns})

    return df


if __name__ == "__main__":
    in_path = sys.argv[1]  # input data
    out_path = sys.argv[2]
    logfile = sys.argv[3]

    logger = config.add_snake_logger(logfile, "create_results_table")

    scalars = pd.read_csv(os.path.join(in_path, "scalars.csv"))

    # Workaround to conform to oemof-b3 format
    scalars.rename(columns={"scenario": "scenario_key"}, inplace=True)

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    df = create_total_system_cost_table(scalars)
    dp.save_df(df, os.path.join(out_path, "methanation_results.csv"))