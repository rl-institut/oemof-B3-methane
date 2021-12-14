import os

import pandas as pd
from oemof.solph import Bus, EnergySystem, Flow, Model, Sink, Source

from oemof_b3.facades import MethanationReactor


def test_methanation_reactor():
    timeindex = pd.date_range("2020-01-01", periods=3, freq="H")

    es = EnergySystem(timeindex=timeindex)

    h2_bus = Bus(label="h2_co2")

    co2_bus = Bus(label="co2", balanced=False)

    ch4_bus = Bus(label="ch4")

    electrolyzer = Source(
        label="electrolyzer",
        outputs={h2_bus: Flow(nominal_value=150)},
    )

    ch4_demand = Sink(
        label="ch4_demand",
        inputs={
            ch4_bus: Flow(fixed=True, nominal_value=100, actual_value=[0.1, 0.2, 0.1])
        },
    )

    ch4_shortage = Source(
        label="ch4_shortage", outputs={ch4_bus: Flow(variable_costs=1e9)}
    )

    ch4_excess = Sink(label="ch4_excess", inputs={ch4_bus: Flow(variable_costs=0.0001)})

    m_reactor = MethanationReactor(
        label="m_reactor",
        carrier="h2_co2",
        tech="methanation_reactor",
        h2_bus=h2_bus,
        co2_bus=co2_bus,
        ch4_bus=ch4_bus,
        capacity_charge=50,
        capacity_discharge=50,
        efficiency_charge=1,
        efficiency_discharge=1,
        methanation_rate=5,  # TODO: Passing lists does not work here yet.
        efficiency_methanation=0.93,
    )

    es.add(
        h2_bus,
        co2_bus,
        ch4_bus,
        electrolyzer,
        ch4_demand,
        ch4_shortage,
        ch4_excess,
        m_reactor,
    )

    m = Model(es)

    lp_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "lp-file.lp"
    )
    m.write(lp_file_path, io_options={"symbolic_solver_labels": True})

    m.solve()

    results = m.results()

    seq_dict = {k: v["sequences"] for k, v in results.items() if "sequences" in v}
    sequences = pd.concat(seq_dict.values(), 1)
    sequences.columns = seq_dict.keys()
    print(sequences)


if __name__ == "__main__":
    test_methanation_reactor()
