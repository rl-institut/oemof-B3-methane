import os
import pandas as pd
import numpy as np
from oemof.solph import Bus, EnergySystem, Flow, Model, Sink, Source, Transformer
from oemof_b3.facades import MethanisationReactor
from oemoflex.tools import plots as plots


from oemof.outputlib.processing import convert_keys_to_strings
import matplotlib.pyplot as plt
from oemof_b3 import labels_dict, colors_odict

from oemof_b3.tools.data_processing import (
    load_b3_scalars,
    # stack_timeseries,
    unstack_timeseries,
    load_b3_timeseries,
    # save_df,
    filter_df,
)

year = 2018
region = "BE"
steps = 300

# TODO: To be deleted after:
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
ts_region_filtered = filter_df(stacked_ts, "region", [region, "All"])

# Get wind profile
ts_region_wind_filtered = filter_df(ts_region_filtered, "var_name", "wind-profile")
ts_wind = unstack_timeseries(ts_region_wind_filtered)

# Get pv profile
ts_region_pv_filtered = filter_df(ts_region_filtered, "var_name", "pv-profile")
ts_pv = unstack_timeseries(ts_region_pv_filtered)

# Get electricity demand
# TODO: Replace constant ts with ts of actual el demand data
el_demand_berlin_2018 = 38037 / 3600  # From Energie- und CO2-Bilanz in GWh
el_demand_berlin = pd.Series(np.ones(steps) * el_demand_berlin_2018 / steps)

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
    label="wind_source",
    outputs={
        el_bus: Flow(
            fixed=True,
            actual_value=ts_wind["wind-profile"][0:steps],
            nominal_value=0.2,
            variable_costs=15,
        )
    },
)

pv_source = Source(
    label="pv_source",
    outputs={
        el_bus: Flow(
            fixed=True,
            actual_value=ts_pv["pv-profile"][0:steps],
            nominal_value=6.437,
            variable_costs=10,
        )
    },
)

co2_import = Source(label="co2_import", outputs={co2_bus: Flow(nominal_value=0.6)})

# Add Sinks
el_demand = Sink(
    label="electricity-demand",
    inputs={el_bus: Flow(fixed=True, actual_value=el_demand_berlin, variable_costs=6)},
)

# ch4_demand = Sink(
#     label="ch4_demand",
#     inputs={ch4_bus: Flow(fixed=True, actual_valueed=True, nominal_value=100, actual_value=[0.1, 0.2, 0.1])},
# )
#
# ch4_shortage = Source(label="ch4_shortage", outputs={ch4_bus: Flow(variable_costs=1e9)})
#
# ch4_excess = Sink(label="ch4_excess", inputs={ch4_bus: Flow(variable_costs=0.0001)})

# Add Transformers
ch4_power_plant = Transformer(
    label="ch4-gt",
    inputs={ch4_bus: Flow(nominal_value=0.4, variable_costs=7)},
    outputs={el_bus: Flow()},
    conversion_factors={ch4_bus: 0.45},
)

electrolyzer = Transformer(
    label="electricity-electrolyzer",
    inputs={el_bus: Flow(variable_costs=6)},
    outputs={h2_bus: Flow(nominal_value=0.6)},
    conversion_factors={h2_bus: 0.73},
)

# electrolyzer = Source(
#     label="electrolyzer",
#     outputs={h2_bus: Flow(nominal_value=150)},
# )

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
    capacity_charge=2.832 / 1000,
    capacity_discharge=7.743 / 1000,
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
    electrolyzer,
    # ch4_demand,
    # ch4_shortage,
    # ch4_excess,
    ch4_power_plant,
    m_reactor,
    el_demand,
)

m = Model(es)

lp_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "lp-file.lp")
m.write(lp_file_path, io_options={"symbolic_solver_labels": True})

m.solve()

results = m.results()

results = convert_keys_to_strings(results)
seq_dict = {k: v["sequences"] for k, v in results.items() if "sequences" in v}
sequences = pd.concat(seq_dict.values(), 1)
sequences.columns = seq_dict.keys()

df, df_demand = plots.prepare_dispatch_data(
    sequences,
    bus_name="electricity",
    demand_name="demand",
    labels_dict=labels_dict,
)

fig, ax = plt.subplots()
plots.plot_dispatch(
    ax=ax,
    df=df,
    df_demand=df_demand,
    unit="W",
    colors_odict=colors_odict,
)

# TODO: Create plots of sequences time series like this: plot(sequences[sequences.columns[4]])
