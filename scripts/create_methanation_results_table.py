# coding: utf-8
r"""
Inputs
------
in_path1 : str
    ``results/joined_scenarios/{scenario_group}/joined/scalars.csv``: path to scalar results.
in_path2 : str
    ``results/_resources/scal_methanation.csv``: path to methanation cost data.
out_path : str
    ``results/joined_scenarios/{scenario_group}/joined_methanation_tables/``: target path for
    results tables.
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


def get_scenario_pairs(scenarios):
    scenarios_methanation = [scen for scen in scenarios if "methanation" in scen]
    pairs = [(scen.strip("-methanation"), scen) for scen in scenarios_methanation]

    for pair in pairs:
        if pair[0] not in scenarios:
            print(f"{pair[1]} is missing partner. Drop.")
            pairs.remove(pair)

    return pairs


def delta_scenarios(df, pairs):
    a = df.loc[[p[0] for p in pairs]].unstack("var_name")

    b = df.loc[[p[1] for p in pairs]].unstack("var_name")

    b = b.rename(index={b: a for a, b in pairs})

    delta = a - b

    return delta


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


def add_methanation_cost(df, methanation_cost):

    idx = pd.IndexSlice

    methanation_cost = (
        dp.multi_filter_df(methanation_cost, var_name="storage_capacity_cost")
        .set_index("scenario_key")
        .loc[:, "var_value"]
    )

    def index_is_methanation_and_year(year):
        return [(str(year) in id[0] and "methanation" in id[0]) for id in df.index]

    df.loc[
        idx[index_is_methanation_and_year(2040), "total_system_cost"], "var_value"
    ] += int(methanation_cost["2040-methanation"])

    df.loc[
        idx[index_is_methanation_and_year(2050), "total_system_cost"], "var_value"
    ] += int(methanation_cost["2050-methanation"])

    return df


if __name__ == "__main__":
    in_path1 = sys.argv[1]  # input data
    in_path2 = sys.argv[2]  # input data
    out_path = sys.argv[3]
    logfile = sys.argv[4]

    logger = config.add_snake_logger(logfile, "create_results_table")

    scalars = pd.read_csv(os.path.join(in_path1, "scalars.csv"))

    methanation_cost = dp.load_b3_scalars(in_path2)

    # get scenario pairs
    scenarios = list(scalars["scenario"].unique())

    scenario_pairs = get_scenario_pairs(scenarios)

    # Workaround to conform to oemof-b3 format
    scalars.rename(columns={"scenario": "scenario_key"}, inplace=True)

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    df = create_total_system_cost_table(scalars)
    df = add_methanation_cost(df, methanation_cost)
    df = delta_scenarios(df, scenario_pairs)

    dp.save_df(df, os.path.join(out_path, "methanation_results.csv"))
