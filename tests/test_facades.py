import logging
import os
import re
from difflib import unified_diff

import pandas as pd

from oemof.network.network import Node
from oemof.solph import helpers
import oemof.solph as solph

from oemof_b3.facades import MethanationReactor


def chop_trailing_whitespace(lines):
    return [re.sub(r"\s*$", "", line) for line in lines]


def remove(pattern, lines):
    if not pattern:
        return lines
    return re.subn(pattern, "", "\n".join(lines))[0].split("\n")


def normalize_to_positive_results(lines):
    negative_result_indices = [
        n for n, line in enumerate(lines) if re.match("^= -", line)
    ]
    equation_start_indices = [
        [n for n in reversed(range(0, nri)) if re.match(".*:$", lines[n])][0] + 1
        for nri in negative_result_indices
    ]
    for (start, end) in zip(equation_start_indices, negative_result_indices):
        for n in range(start, end):
            lines[n] = (
                "-"
                if lines[n] and lines[n][0] == "+"
                else "+"
                if lines[n]
                else lines[n]
            ) + lines[n][1:]
        lines[end] = "= " + lines[end][3:]
    return lines


def compare_lp_files(lp_file_1, lp_file_2, ignored=None):
    lines_1 = remove(ignored, chop_trailing_whitespace(lp_file_1.readlines()))
    lines_2 = remove(ignored, chop_trailing_whitespace(lp_file_2.readlines()))

    lines_1 = normalize_to_positive_results(lines_1)
    lines_2 = normalize_to_positive_results(lines_2)

    if not lines_1 == lines_2:
        raise AssertionError(
            "Failed matching lp_file_1 with lp_file_2:\n"
            + "\n".join(
                unified_diff(
                    lines_1,
                    lines_2,
                    fromfile=os.path.relpath(lp_file_1.name),
                    tofile=os.path.basename(lp_file_2.name),
                    lineterm="",
                )
            )
        )


class TestConstraints:
    @classmethod
    def setup_class(cls):
        cls.objective_pattern = re.compile(
            r"^objective.*(?=s\.t\.)", re.DOTALL | re.MULTILINE
        )

        cls.date_time_index = pd.date_range("1/1/2012", periods=3, freq="H")

        cls.tmpdir = helpers.extend_basic_path("tmp")
        logging.info(cls.tmpdir)

    @classmethod
    def setup(cls):
        cls.energysystem = solph.EnergySystem(
            groupings=solph.GROUPINGS, timeindex=cls.date_time_index
        )
        Node.registry = cls.energysystem

    def get_om(self):
        return solph.Model(self.energysystem, timeindex=self.energysystem.timeindex)

    def compare_to_reference_lp(self, ref_filename, my_om=None):
        if my_om is None:
            om = self.get_om()
        else:
            om = my_om

        tmp_filename = ref_filename.replace(".lp", "") + "_tmp.lp"

        new_filepath = os.path.join(self.tmpdir, tmp_filename)

        om.write(new_filepath, io_options={"symbolic_solver_labels": True})

        ref_filepath = os.path.join(
            os.path.dirname(__file__), "_files", "lp_files", ref_filename
        )

        with open(new_filepath) as new_file:
            with open(ref_filepath) as ref_file:
                compare_lp_files(new_file, ref_file)

    def test_methanation_reactor(self):

        h2_bus = solph.Bus(label="h2")

        co2_bus = solph.Bus(label="co2", balanced=False)

        ch4_bus = solph.Bus(label="ch4")

        MethanationReactor(
            label="m_reactor",
            carrier="h2_co2",
            tech="methanation_reactor",
            h2_bus=h2_bus,
            co2_bus=co2_bus,
            ch4_bus=ch4_bus,
            capacity_charge=50,
            capacity_discharge=50,
            storage_capacity_educts=100,
            storage_capacity_products=1000,
            efficiency_charge=1,
            efficiency_discharge=1,
            methanation_rate=5,  # TODO: Passing lists does not work here yet.
            efficiency_methanation=0.93,
            methanation_option="variable_rate",
        )

        self.compare_to_reference_lp("methanation_reactor.lp")

    def test_methanation_reactor_nonconvex(self):

        h2_bus = solph.Bus(label="h2")

        co2_bus = solph.Bus(label="co2", balanced=False)

        ch4_bus = solph.Bus(label="ch4")

        MethanationReactor(
            label="m_reactor",
            carrier="h2_co2",
            tech="methanation_reactor",
            h2_bus=h2_bus,
            co2_bus=co2_bus,
            ch4_bus=ch4_bus,
            capacity_charge=50,
            capacity_discharge=50,
            storage_capacity_educts=100,
            storage_capacity_products=1000,
            efficiency_charge=1,
            efficiency_discharge=1,
            methanation_rate=5,  # TODO: Passing lists does not work here yet.
            efficiency_methanation=0.93,
            methanation_option="variable_rate",
            nonconvex=True,
        )

        self.compare_to_reference_lp("methanation_reactor_nonconvex.lp")
