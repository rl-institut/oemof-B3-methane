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

from oemof.tools.economics import annuity

from oemof_b3.tools.data_processing import ScalarProcessor, load_b3_scalars, save_df


def annuise_investment_cost(sc):

    for var_name_cost, var_name_fixom_cost in [
        ("capacity_cost_overnight", "fixom_cost"),
        ("storage_capacity_cost_overnight", "storage_fixom_cost"),
    ]:

        invest_data = sc.get_unstacked_var(
            [var_name_cost, "lifetime", var_name_fixom_cost]
        )

        # TODO: Currently, (storage)_capacity_overnight_cost, (storage)_fixom_cost and lifetime have
        # to be given for each tech and each scenario, but wacc may change per scenario, but
        # is defined for all techs uniformly. Could offer a more general and flexible solution.

        # wacc is defined per scenario, ignore other index levels
        wacc = sc.get_unstacked_var("wacc")
        wacc.index = wacc.index.get_level_values("scenario_key")

        # set wacc per scenario_key
        scenario_keys = invest_data.index.get_level_values("scenario_key")
        invest_data["wacc"] = wacc.loc[scenario_keys].values

        # keep rows where all necessary values are given
        invest_data = invest_data.loc[~invest_data.isna().any(1)]

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

    sc.scalars = sc.scalars.sort_values(
        by=["carrier", "tech", "var_name", "scenario_key"]
    )

    sc.scalars.reset_index(inplace=True, drop=True)

    sc.scalars.index.name = "id_scal"


def load_process_save(path_source, path_target, func):
    df = load_b3_scalars(path_source)

    sc = ScalarProcessor(df)

    func(sc)

    save_df(sc.scalars, path_target)


if __name__ == "__main__":
    raw_scalars_costs_eff = sys.argv[1]  # path to raw scalar data
    raw_scalars_methanation = sys.argv[2]  # path to raw scalar data
    resources_costs_eff = sys.argv[3]  # path to destination
    resources_methanation = sys.argv[4]  # path to destination

    load_process_save(
        raw_scalars_costs_eff, resources_costs_eff, func=annuise_investment_cost
    )
    load_process_save(
        raw_scalars_methanation, resources_methanation, func=annuise_investment_cost
    )
