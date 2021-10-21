import os
import pandas as pd
import numpy as np
from oemof.tabular.tools import postprocessing as postpro
from oemof.solph import Bus, EnergySystem, Flow, Model, Sink, Source, Transformer
from oemoflex.tools import plots
import matplotlib.pyplot as plt
from oemof_b3.facades import MethanisationReactor

from oemof_b3 import labels_dict, colors_odict

from oemof_b3.tools.data_processing import (
    load_b3_scalars,
    # stack_timeseries,
    unstack_timeseries,
    load_b3_timeseries,
    # save_df,
    filter_df,
)

# Constants
year = 2018
region = "BE"
steps = 240  # time steps of simulation
DEMAND_EL = 100000  # Electricity demand
DEMAND_H2 = 8
CAP_WIND = 16  # Installed capacity wind
CAP_PV = 10  # Installed capacity PV
CAP_CO2 = 2  # CO2 Import
CAP_CH4 = 6  # CH4 Power plant
CAP_CHARGE_M_REAC = 2.8
CAP_DISCHARGE_M_REAC = 7.7


# TODO: Only to sample time series - To be deleted after:
ts_test = []
for time_steps in np.arange(0, steps):
    ts_test.append(np.random.choice(np.arange(0.01, 0.8, 0.01)))


# Set paths
path_file = os.path.abspath(__file__)
raw_path = os.path.abspath(os.path.join(path_file, os.pardir, os.pardir, "raw"))
examples_path = os.path.abspath(
    os.path.join(path_file, os.pardir, os.pardir, "examples")
)
schema_path = os.path.abspath(
    os.path.join(path_file, os.pardir, os.pardir, "oemof_b3", "schema")
)

# Read scalars
sc = load_b3_scalars(os.path.join(raw_path, "scalars.csv"))
sc_region_filtered = filter_df(sc, "region", [region, "All"])

# Read time series
stacked_ts = load_b3_timeseries(os.path.join(raw_path, "feedin_time_series.csv"))
el_demand = pd.read_csv(os.path.join(raw_path, "2015_entsoe_50Hz_h.csv"))

ts_region_filtered = filter_df(stacked_ts, "region", [region, "All"])

# Get wind profile
ts_region_wind_filtered = filter_df(ts_region_filtered, "var_name", "wind-profile")
ts_wind = unstack_timeseries(ts_region_wind_filtered)

# Get pv profile
ts_region_pv_filtered = filter_df(ts_region_filtered, "var_name", "pv-profile")
ts_pv = unstack_timeseries(ts_region_pv_filtered)

# Get electricity demand
el_demand_norm = np.divide(
    el_demand["Actual Total Load [MW] - CTA|DE(50Hertz)"],
    sum(el_demand["Actual Total Load [MW] - CTA|DE(50Hertz)"]),
)

# Make time index
timeindex = pd.date_range(str(year) + "-01-01", periods=steps, freq="H")

# Add energy system
es = EnergySystem(timeindex=timeindex)

# Add busses
h2_bus = Bus(label="h2_co2")
co2_bus = Bus(label="co2", balanced=False)
ch4_bus = Bus(label="ch4")
el_bus = Bus(label="electricity")
# heat_cen_bus = Bus(label="heat_central")
# heat_dec_bus = Bus(label="heat_decentral")

# Add Sources
wind_source = Source(
    label="wind-onshore",
    outputs={
        el_bus: Flow(
            fixed=True,
            actual_value=ts_wind["wind-profile"][0:steps],
            nominal_value=CAP_WIND,
            variable_costs=15,
        )
    },
)

pv_source = Source(
    label="solar-pv",
    outputs={
        el_bus: Flow(
            fixed=True,
            actual_value=ts_pv["pv-profile"][0:steps],
            nominal_value=CAP_PV,
            variable_costs=10,
        )
    },
)

co2_import = Source(label="co2_import", outputs={co2_bus: Flow(nominal_value=CAP_CO2)})

# Add Sinks
el_demand = Sink(
    label="electricity-demand",
    inputs={
        el_bus: Flow(
            fixed=True,
            actual_value=el_demand_norm[0:steps],
            nominal_value=DEMAND_EL,
            variable_costs=6,
        )
    },
)

# ch4_demand = Sink(
#     label="ch4_demand",
#     inputs={
#         ch4_bus: Flow(
#             fixed=True,
#             actual_valueed=True,
#             nominal_value=100,
#             actual_value=[0.1, 0.2, 0.1],
#         )
#     },
# )
# Add Shortages
el_shortage = Source(
    label="electricity-shortage", outputs={el_bus: Flow(variable_costs=1e9)}
)
ch4_shortage = Source(label="ch4-shortage", outputs={ch4_bus: Flow(variable_costs=1e9)})

# Add Excesses
el_excess = Sink(
    label="electricity-curtailment", inputs={el_bus: Flow(variable_costs=0.0001)}
)
ch4_excess = Sink(label="ch4-excess", inputs={ch4_bus: Flow(variable_costs=0.0001)})

# Add Transformers
ch4_power_plant = Transformer(
    label="ch4-gt",
    inputs={ch4_bus: Flow(nominal_value=CAP_CH4, variable_costs=7)},
    outputs={el_bus: Flow()},
    conversion_factors={ch4_bus: 0.45},
)

electrolyzer = Transformer(
    label="electricity-electrolyzer",
    inputs={el_bus: Flow(variable_costs=6)},
    outputs={h2_bus: Flow(nominal_value=DEMAND_H2)},
    conversion_factors={h2_bus: 0.73},
)

# heat_demand = Sink(
#     label="heat_demand", inputs={heat_cen_bus: Flow(actual_value=np.ones(steps))}
# )


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
    methanisation_rate=5,  # TODO: Passing lists does not work here yet.
    efficiency_methanisation=0.93,
)

es.add(
    h2_bus,
    co2_bus,
    ch4_bus,
    el_bus,
    # heat_cen_bus,
    # heat_dec_bus,
    wind_source,
    pv_source,
    # RoR_source,
    co2_import,
    el_demand,
    el_shortage,
    ch4_shortage,
    el_excess,
    ch4_excess,
    # ch4_demand,
    ch4_power_plant,
    electrolyzer,
    m_reactor,
)

m = Model(es)

lp_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "lp-file.lp")
m.write(lp_file_path, io_options={"symbolic_solver_labels": True})

m.solve()

results = m.results()

from oemof.outputlib.processing import convert_keys_to_strings
str_results = convert_keys_to_strings(results)
seq_dict = {k: v["sequences"] for k, v in str_results.items() if "sequences" in v}
sequences = pd.concat(seq_dict.values(), 1)
sequences.columns = seq_dict.keys()

bus_sequences = postpro.bus_results(es, results, select="sequences", concat=False)

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

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.5),
        fancybox=True,
        ncol=4,
        fontsize=14,
    )

    for tick in ax.get_xticklabels():
        tick.set_rotation(45)


ax3.plot(sequences[("m_reactor-storage_products", 'None')], c='b', label="Storage Level Products")
ax3.plot(sequences[("m_reactor-storage_educts", 'None')], c='r', label="Storage Level Educts")
ax3.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.5),
    fancybox=True,
    ncol=4,
    fontsize=14,
)
methanation = sequences[("m_reactor", "m_reactor-storage_products")]
ax4.plot(methanation)

ax1.set_ylabel("Power")
ax2.set_ylabel("Power")
ax2.set_xlabel("time")
ax2.sharex(ax1)

ax1.axes.get_xaxis().set_visible(False)
ax2.axes.get_xaxis().set_visible(False)
ax3.axes.get_xaxis().set_visible(False)
ax4.axes.get_xaxis().set_visible(False)

fig.tight_layout()

plt.savefig("dispatch.png")
