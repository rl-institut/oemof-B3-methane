# coding: utf-8
r"""
Inputs
-------
in_path1 : str
    ``raw/scalars/costs_efficiencies.csv``: path incl. file name of input file with raw scalar data
out_path : str
    ``results/_resources/scal_costs_efficiencies.csv``: path incl. file name of output file with
    prepared scalar data

Outputs
---------
pandas.DataFrame
    with scalar data prepared for parametrization

Description
-------------
The script performs the following steps to prepare scalar data for parametrization:

* Calculate annualized investment cost from overnight cost, lifetime and wacc.
"""

import sys

import pandas as pd

from oemof.tools.economics import annuity

from oemof_b3.tools.data_processing import ScalarProcessor, load_b3_scalars, save_df


def fill_na(df):
    key = "scenario_key"

    value = "None"

    _df = df.copy()

    # save index and columns before resetting index
    id_names = _df.index.names

    columns = _df.columns

    _df.reset_index(inplace=True)

    # separate data where NaNs should be filled and base
    df_fill_na = _df.loc[_df[key] != value]

    base = _df.loc[_df[key] == value]

    # merge data on the columns of the data to update
    df_merged = df_fill_na.drop(columns, 1).merge(base.drop(key, 1), "left")

    # update dataframe NaNs
    df_fill_na.update(df_merged)

    # combine the filled data with the base data
    df_fill_na = pd.concat([df_fill_na, base])

    # set index as before
    df_fill_na = df_fill_na.set_index(id_names)

    return df_fill_na


def annuise_investment_cost(sc):

    for var_name_cost, var_name_fixom_cost in [
        ("capacity_cost_overnight", "fixom_cost"),
        ("storage_capacity_cost_overnight", "storage_fixom_cost"),
    ]:

        invest_data = sc.get_unstacked_var(
            [var_name_cost, "lifetime", var_name_fixom_cost]
        )

        # if some value is None in some scenario key, use the values from Base scenario to fill NaNs
        invest_data = fill_na(invest_data)

        # wacc is defined per scenario, ignore other index levels
        wacc = sc.get_unstacked_var("wacc")
        wacc.index = wacc.index.get_level_values("scenario_key")

        # set wacc per scenario_key
        scenario_keys = invest_data.index.get_level_values("scenario_key")
        invest_data["wacc"] = wacc.loc[scenario_keys].values

        annuised_investment_cost = invest_data.apply(
            lambda x: annuity(x[var_name_cost], x["lifetime"], x["wacc"])
            + x[var_name_fixom_cost],
            1,
        )

        sc.append(var_name_cost.replace("_overnight", ""), annuised_investment_cost)

    sc.drop(
        [
            "wacc",
            "lifetime",
            "capacity_cost_overnight",
            "storage_capacity_cost_overnight",
            "fixom_cost",
            "storage_fixom_cost",
        ]
    )


if __name__ == "__main__":
    in_path = sys.argv[1]  # path to raw scalar data
    out_path = sys.argv[2]  # path to destination

    df = load_b3_scalars(in_path)

    sc = ScalarProcessor(df)

    annuise_investment_cost(sc)

    sc.scalars = sc.scalars.sort_values(
        by=["carrier", "tech", "var_name", "scenario_key"]
    )

    sc.scalars.reset_index(inplace=True, drop=True)

    sc.scalars.index.name = "id_scal"

    save_df(sc.scalars, out_path)
