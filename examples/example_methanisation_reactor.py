import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from oemof.outputlib.processing import convert_keys_to_strings
from oemof.solph import Bus, EnergySystem, Flow, Model, Sink, Source, Transformer
from oemof.tabular.tools import postprocessing as postpro
from oemof_b3 import colors_odict, labels_dict
from oemof_b3.facades import MethanisationReactor
from oemof_b3.tools.data_processing import (
    filter_df,
    load_b3_timeseries,
    unstack_timeseries,
)
from oemoflex.tools import plots

# Constants
YEAR = 2018
REGION = "BE"
STEPS = 240  # time steps of simulation

# Demands
DEMAND_EL = 100000  # Electricity demand

# Capacities
CAP_WIND = 25  # Installed capacity wind
CAP_PV = 20  # Installed capacity PV
CAP_ELY = 8
CAP_CH4 = 20  # CH4 Power plant
CAP_CHARGE_M_REAC = 2.8
CAP_DISCHARGE_M_REAC = 7.7
METHANATION_RATE = 2

METHANATION_OPTION = 1
TS_TEST = False

# Costs
VAR_COST_WIND = 0.001
VAR_COST_PV = 0.001
VAR_COST_EL_DEMAND = 0.001
VAR_COST_EL_SHORTAGE = 1e9
VAR_COST_CH4_SHORTAGE = 40
VAR_COST_EL_EXCESS = 0
VAR_COST_CH4_EXCESS = 0
VAR_COST_CH4_PP_INPUT = 0
VAR_COST_ELY_INPUT = 0

# Efficiencies
EFF_CH4_PP = 0.45
EFF_ELY = 0.73
EFF_METHANATION = 0.93

# Set paths
path_file = os.path.abspath(__file__)
raw_path = os.path.abspath(os.path.join(path_file, os.pardir, os.pardir, "raw"))
examples_path = os.path.abspath(
    os.path.join(path_file, os.pardir, os.pardir, "examples")
)
schema_path = os.path.abspath(
    os.path.join(path_file, os.pardir, os.pardir, "oemof_b3", "schema")
)

# Read time series
stacked_ts = load_b3_timeseries(os.path.join(raw_path, "feedin_time_series.csv"))
el_demand = pd.read_csv(os.path.join(raw_path, "2015_entsoe_50Hz_h.csv"))

ts_region_filtered = filter_df(stacked_ts, "region", [REGION, "All"])

# Get wind profile
ts_region_wind_filtered = filter_df(ts_region_filtered, "var_name", "wind-profile")
ts_wind = unstack_timeseries(ts_region_wind_filtered)["wind-profile"]

# Get pv profile
ts_region_pv_filtered = filter_df(ts_region_filtered, "var_name", "pv-profile")
ts_pv = unstack_timeseries(ts_region_pv_filtered)["pv-profile"]

# Get electricity demand
el_demand_norm = np.divide(
    el_demand["Actual Total Load [MW] - CTA|DE(50Hertz)"],
    sum(el_demand["Actual Total Load [MW] - CTA|DE(50Hertz)"]),
)

# Define test timeseries
if TS_TEST:
    assert STEPS >= 240
    ts_wind = np.zeros(STEPS)
    ts_pv = np.zeros(STEPS)
    el_demand = np.zeros(STEPS)

    ts_wind[24:72] = 0.4
    el_demand[180:220] = 0.1

    el_demand_norm = el_demand / sum(el_demand)


def run_model():
    # Make time index
    timeindex = pd.date_range(str(YEAR) + "-01-01", periods=STEPS, freq="H")

    # Add energy system
    es = EnergySystem(timeindex=timeindex)

    # Add busses
    h2_bus = Bus(label="h2")
    co2_bus = Bus(label="co2", balanced=False)
    ch4_bus = Bus(label="ch4")
    el_bus = Bus(label="electricity")

    # Add Sources
    wind_source = Source(
        label="wind-onshore",
        outputs={
            el_bus: Flow(
                fixed=True,
                actual_value=ts_wind[0:STEPS],
                nominal_value=CAP_WIND,
                variable_costs=VAR_COST_WIND,
            )
        },
    )

    pv_source = Source(
        label="solar-pv",
        outputs={
            el_bus: Flow(
                fixed=True,
                actual_value=ts_pv[0:STEPS],
                nominal_value=CAP_PV,
                variable_costs=VAR_COST_PV,
            )
        },
    )

    # Add Sinks
    el_demand = Sink(
        label="electricity-demand",
        inputs={
            el_bus: Flow(
                fixed=True,
                actual_value=el_demand_norm[0:STEPS],
                nominal_value=DEMAND_EL,
                variable_costs=VAR_COST_EL_DEMAND,
            )
        },
    )

    # Add Shortages
    el_shortage = Source(
        label="electricity-shortage",
        outputs={el_bus: Flow(variable_costs=VAR_COST_EL_SHORTAGE)},
    )
    ch4_shortage = Source(
        label="ch4-shortage",
        outputs={ch4_bus: Flow(variable_costs=VAR_COST_CH4_SHORTAGE)},
    )

    # Add Excesses
    el_excess = Sink(
        label="electricity-curtailment",
        inputs={el_bus: Flow(variable_costs=VAR_COST_EL_EXCESS)},
    )
    ch4_excess = Sink(
        label="ch4-excess", inputs={ch4_bus: Flow(variable_costs=VAR_COST_CH4_EXCESS)}
    )

    # Add Transformers
    ch4_power_plant = Transformer(
        label="ch4-gt",
        inputs={ch4_bus: Flow(variable_costs=VAR_COST_CH4_PP_INPUT)},
        outputs={el_bus: Flow(nominal_value=CAP_CH4)},
        conversion_factors={el_bus: EFF_CH4_PP},
    )

    electrolyzer = Transformer(
        label="electricity-electrolyzer",
        inputs={el_bus: Flow(variable_costs=VAR_COST_ELY_INPUT)},
        outputs={h2_bus: Flow(nominal_value=CAP_ELY)},
        conversion_factors={h2_bus: EFF_ELY},
    )

    m_reactor = MethanisationReactor(
        label="m_reactor",
        carrier="h2_co2",
        tech="methanisation_reactor",
        h2_bus=h2_bus,
        co2_bus=co2_bus,
        ch4_bus=ch4_bus,
        capacity_charge=CAP_CHARGE_M_REAC,
        capacity_discharge=CAP_DISCHARGE_M_REAC,
        efficiency_charge=1,
        efficiency_discharge=1,
        methanisation_rate=METHANATION_RATE,  # TODO: Passing lists does not work here yet.
        efficiency_methanisation=EFF_METHANATION,
        methanisation_option=METHANATION_OPTION,
    )

    es.add(
        h2_bus,
        co2_bus,
        ch4_bus,
        el_bus,
        wind_source,
        pv_source,
        el_demand,
        el_shortage,
        ch4_shortage,
        el_excess,
        ch4_excess,
        ch4_power_plant,
        electrolyzer,
        m_reactor,
    )

    m = Model(es)

    lp_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "lp-file.lp"
    )
    m.write(lp_file_path, io_options={"symbolic_solver_labels": True})

    m.solve()

    es.results = m.results()

    return es


def postprocess(es):
    results = es.results

    str_results = convert_keys_to_strings(results)
    seq_dict = {k: v["sequences"] for k, v in str_results.items() if "sequences" in v}
    sequences = pd.concat(seq_dict.values(), 1)

    # drop status variable of integer variable if present
    if "status" in sequences.columns:
        sequences.drop("status", axis=1, inplace=True)

    sequences.columns = seq_dict.keys()

    bus_sequences = postpro.bus_results(es, results, select="sequences", concat=False)

    return sequences, bus_sequences


def plot_dispatch(bus_sequences):

    bus_name = ["electricity", "ch4"]

    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1)
    fig.set_size_inches(12, 8, forward=True)
    fig.subplots_adjust(hspace=0.5)

    for bus in bus_name:
        df = bus_sequences[bus]

        # labels to strings
        df.to_csv("test.csv")
        df = pd.read_csv("test.csv", header=[0, 1, 2], index_col=0)

        if bus == "electricity":
            ax = ax1
        if bus == "ch4":
            df.loc[:, ("ch4", "ch4-demand", "flow")] = 0
            ax = ax2

        df, df_demand = plots.prepare_dispatch_data(
            df,
            bus_name=bus,
            demand_name="demand",
            labels_dict=labels_dict,
        )

        plots.plot_dispatch(
            ax=ax,
            df=df,
            df_demand=df_demand,
            unit="MW",
            colors_odict=colors_odict,
        )

        for tick in ax.get_xticklabels():
            tick.set_rotation(45)

    ax3.plot(
        sequences[("m_reactor-storage_products", "None")],
        c="r",
        label="Storage Level Products",
    )
    ax3.plot(
        sequences[("m_reactor-storage_educts", "None")],
        c="b",
        label="Storage Level Educts",
    )

    methanation = sequences[("m_reactor", "m_reactor-storage_products")]
    ax4.fill_between(
        methanation.index,
        0,
        methanation,
        label="Methanation",
        color=colors_odict["Methanation"],
    )

    h_l = [ax.get_legend_handles_labels() for ax in (ax1, ax2, ax3, ax4)]
    handles = [item for sublist in list(map(lambda x: x[0], h_l)) for item in sublist]
    labels = [item for sublist in list(map(lambda x: x[1], h_l)) for item in sublist]

    ax4.legend(
        handles=handles,
        labels=labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.5),
        fancybox=True,
        ncol=4,
        fontsize=14,
    )

    ax1.set_ylabel("Power")
    ax2.set_ylabel("Power")
    ax3.set_ylabel("Storage level / MWh")
    ax4.set_ylabel("Power / MW")
    ax4.set_xlabel("Time")

    ax1.axes.get_xaxis().set_visible(False)
    ax2.axes.get_xaxis().set_visible(False)
    ax3.axes.get_xaxis().set_visible(False)

    fig.tight_layout()

    plt.savefig(f"example_methanisation_reactor_option_{METHANATION_OPTION}.png")


def get_scalar_results(sequences):
    # Get scalar results
    select_scalars = [
        ("electricity-electrolyzer", "h2"),
        ("m_reactor-storage_products", "ch4"),
        ("electricity", "electricity-curtailment"),
        ("electricity-shortage", "electricity"),
        ("ch4-gt", "electricity"),
    ]

    summed_sequences = sequences.sum().round(2)

    summed_sequences.index.names = ["from", "to"]

    summed_sequences.name = "annual_sum"

    sums_of_interest = summed_sequences.loc[select_scalars]

    sums_of_interest.to_csv(f"sums_of_interest_{METHANATION_OPTION}.csv", header=True)

    # join scalar results
    files = os.listdir(os.path.dirname(path_file))

    files_sum = sorted([f for f in files if "sums_of_interest" in f])
    all_sums = pd.DataFrame()
    for f in files_sum:
        df = pd.read_csv(f, header=0, index_col=[0, 1])
        df.columns = [f.split(".")[0]]
        all_sums = pd.concat([all_sums, df], 1)

    print(all_sums)


if __name__ == "__main__":
    es = run_model()
    sequences, bus_sequences = postprocess(es)
    plot_dispatch(bus_sequences)
    get_scalar_results(sequences)
