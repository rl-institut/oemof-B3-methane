# coding: utf-8
r"""
Inputs
------
in_path1 : str
    ``results/joined_scenarios/{scenario_group}/joined/``: path to scalar results.
in_path2 : str
    ``results/_resources/scal_methanation.csv``: path to methanation cost data.
out_path : str
    ``results/joined_scenarios/{scenario_group}/joined_tables_methanation/``: target path for
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


AGG_METHOD = {
    "var_value": sum,
    "name": lambda x: "None",
}


def get_scenario_pairs(scenarios):
    scenarios_methanation = [scen for scen in scenarios if "methanation" in scen]
    pairs = [(scen.strip("-methanation"), scen) for scen in scenarios_methanation]

    for pair in pairs:
        if pair[0] not in scenarios:
            print(f"Scenario {pair[1]} is missing partner. Drop.")
            pairs.remove(pair)

    return pairs


def delta_scenarios(df, pairs):
    r"""
    Calculates delta (b - a) of scalar results between scenario pairs (a, b). If results for b are
    smaller, the delta is negative.
    """
    a = df.loc[[p[0] for p in pairs]].unstack("var_name")

    b = df.loc[[p[1] for p in pairs]].unstack("var_name")

    b = b.rename(index={b: a for a, b in pairs})

    delta = b - a

    delta = delta.rename(columns={"var_value": "delta"})

    delta.index.name = "scenario"

    return delta


def create_table_system_cost_curtailment(scalars):
    # total system cost
    total_system_cost = dp.filter_df(scalars, "var_name", "total_system_cost")

    # curtailment
    curtailment = dp.multi_filter_df(
        scalars, var_name="flow_in_electricity", tech="curtailment"
    )

    curtailment = dp.aggregate_scalars(curtailment, "region", agg_method=AGG_METHOD)
    curtailment["var_name"] = "curtailment"

    df = pd.concat([total_system_cost, curtailment])

    df = df.set_index(["scenario_key", "var_name"])

    df = df.loc[:, ["var_value"]]

    df = dp.round_setting_int(df, decimals={col: 0 for col in df.columns})

    return df


def create_flh_table(scalars):
    capacity_in = 2.8
    capacity_out = 7.7

    methanation_ch4_out = dp.multi_filter_df(
        scalars, tech="methanation", var_name="flow_out_ch4"
    )
    methanation_h2_in = dp.multi_filter_df(
        scalars, tech="methanation", var_name="flow_in_h2"
    )

    # aggregate regions
    methanation_ch4_out = dp.aggregate_scalars(
        methanation_ch4_out, "region", agg_method=AGG_METHOD
    )
    methanation_ch4_out["var_name"] = "flow_out_ch4"
    methanation_ch4_out = methanation_ch4_out.set_index(["scenario_key", "var_name"])
    methanation_ch4_out = methanation_ch4_out.loc[:, ["var_value"]]

    methanation_h2_in = dp.aggregate_scalars(
        methanation_h2_in, "region", agg_method=AGG_METHOD
    )
    methanation_h2_in["var_name"] = "flow_in_h2"
    methanation_h2_in = methanation_h2_in.set_index(["scenario_key", "var_name"])
    methanation_h2_in = methanation_h2_in.loc[:, ["var_value"]]

    flh_out = methanation_ch4_out / capacity_out
    flh_out = flh_out.rename({"flow_out_ch4": "flh_out"})

    flh_in = methanation_h2_in / capacity_in
    flh_in = flh_in.rename({"flow_in_h2": "flh_in"})

    # concat, reorganize
    df = pd.concat([flh_in, flh_out])

    df = df.unstack("var_name")

    df = dp.round_setting_int(df, decimals={col: 0 for col in df.columns})

    df = df.rename(index=lambda x: x.strip("-methanation"))
    df.columns = df.columns.get_level_values("var_name")

    return df


def get_methanation_costs(methanation_df):
    return (
            dp.multi_filter_df(methanation_df, var_name="storage_capacity_cost")
                .set_index("scenario_key")
                .loc[:, "var_value"]
        )


def add_methanation_cost(df, methanation_df):

    idx = pd.IndexSlice
    methanation_cost = get_methanation_costs(methanation_df)

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

    methanation_df = dp.load_b3_scalars(in_path2)

    # get scenario pairs
    scenarios = list(scalars["scenario"].unique())
    scenario_pairs = get_scenario_pairs(scenarios)

    # Workaround to conform to oemof-b3 format
    scalars.rename(columns={"scenario": "scenario_key"}, inplace=True)

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    flh = create_flh_table(scalars)
    df = create_table_system_cost_curtailment(scalars)
    df = add_methanation_cost(df, methanation_df)
    df = delta_scenarios(df, scenario_pairs)

    df["installed"] = df[("delta", "total_system_cost")] < 0

    # rename columns
    df.columns = df.columns.to_flat_index()
    df = df.rename(columns=lambda x: " ".join(x))

    df = df.join(flh)

    dp.save_df(df, os.path.join(out_path, "methanation_results.csv"))
