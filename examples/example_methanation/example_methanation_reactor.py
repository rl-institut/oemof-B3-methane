import os

import matplotlib.pyplot as plt

import pandas as pd
from oemof.solph.processing import convert_keys_to_strings
from oemof.solph import Bus, EnergySystem, Flow, Model, Sink, Source, Transformer
from oemof.tabular.tools import postprocessing as postpro
from oemof_b3 import colors_odict, labels_dict
from oemof_b3.facades import MethanationReactor
from oemof_b3.tools.data_processing import (
    filter_df,
    load_b3_timeseries,
    unstack_timeseries,
)
from oemoflex.tools import plots

# Constants
YEAR = 2018
REGION = "B"
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
STORAGE_CAPACITY_EDUCTS = 24e3
STORAGE_CAPACITY_PRODUCTS = 110e3

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
path_examples = os.path.dirname(os.path.abspath(__file__))

# Read time series
el_demand = pd.read_csv(os.path.join(path_examples, "2015_entsoe_50Hz_h.csv"))[
    "Actual Total Load [MW] - CTA|DE(50Hertz)"
]
stacked_ts = load_b3_timeseries(os.path.join(path_examples, "ts_feedin.csv"))

ts_scenarioy_key_filtered = filter_df(stacked_ts, "scenario_key", f"ts_{YEAR}")
ts_region_filtered = filter_df(ts_scenarioy_key_filtered, "region", [REGION, "All"])

# Get wind profile
ts_region_wind_filtered = filter_df(
    ts_region_filtered, "var_name", "wind-onshore-profile"
)
ts_wind = unstack_timeseries(ts_region_wind_filtered)["wind-onshore-profile"]

# Get pv profile
ts_region_pv_filtered = filter_df(ts_region_filtered, "var_name", "solar-pv-profile")
ts_pv = unstack_timeseries(ts_region_pv_filtered)["solar-pv-profile"]


# Normalize electricity demand
def normalize(series):
    return series / sum(series)


el_demand_norm = normalize(el_demand)


def run_model(methanation_option):
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
                fix=ts_wind[0:STEPS],
                nominal_value=CAP_WIND,
                variable_costs=VAR_COST_WIND,
            )
        },
    )

    pv_source = Source(
        label="solar-pv",
        outputs={
            el_bus: Flow(
                fix=ts_pv[0:STEPS],
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
                fix=el_demand_norm[0:STEPS],
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

    m_reactor = MethanationReactor(
        label="m_reactor",
        carrier="h2_co2",
        tech="methanation_reactor",
        h2_bus=h2_bus,
        co2_bus=co2_bus,
        ch4_bus=ch4_bus,
        capacity_charge=CAP_CHARGE_M_REAC,
        capacity_discharge=CAP_DISCHARGE_M_REAC,
        storage_capacity_educts=STORAGE_CAPACITY_EDUCTS,
        storage_capacity_products=STORAGE_CAPACITY_PRODUCTS,
        efficiency_charge=1,
        efficiency_discharge=1,
        methanation_rate=METHANATION_RATE,  # TODO: Passing lists does not work here yet.
        efficiency_methanation=EFF_METHANATION,
        methanation_option=methanation_option,
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

    lp_file_path = os.path.join(path_examples, "lp-file.lp")
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
        # Get raw Dataframe with bus data
        bus_sequences_dict = convert_keys_to_strings(bus_sequences)
        df_raw = bus_sequences_dict[bus]

        # Get MultiIndex of raw Dataframe with values as str only
        column_list = []
        for index_column, column in enumerate(df_raw.columns):
            column_array_tuple = tuple()
            for index_item, item in enumerate(column):
                column_array_tuple = column_array_tuple + (str(item),)
            column_list.append(column_array_tuple)
        pd_columns = pd.MultiIndex.from_tuples(column_list)

        # Add data and preprocessed MultiIndex to Dataframe
        df = pd.DataFrame(data=df_raw.values, columns=pd_columns)

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

    return fig


def save_scalar_results(sequences, path):
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

    sums_of_interest.to_csv(path, header=True)


if __name__ == "__main__":
    METHANATION_OPTIONS = [
        "no_constraints",
        "fixed_rate",
        "variable_rate",
        "variable_rate_with_min",
        "variable_rate_with_min_and_ramping",
        "variable_rate_with_ramping",
    ]
    for methanation_option in METHANATION_OPTIONS:
        es = run_model(methanation_option)
        sequences, bus_sequences = postprocess(es)
        plot_dispatch(bus_sequences)
        plt.savefig(f"example_methanation_reactor_option_{methanation_option}.png")
        save_scalar_results(sequences, f"sums_of_interest_{methanation_option}.csv")

    # join scalar results

    files_sum = [
        f"sums_of_interest_{methanation_option}.csv"
        for methanation_option in METHANATION_OPTIONS
    ]
    all_sums = pd.DataFrame()
    for f in files_sum:
        df = pd.read_csv(f, header=0, index_col=[0, 1])
        df.columns = [f.split(".")[0]]
        all_sums = pd.concat([all_sums, df], 1)

    all_sums.to_csv("sums_of_interest_all.csv")
