import os
import sys
import re

import matplotlib.pyplot as plt
import pandas as pd
from oemoflex.tools import plots
from oemof_b3.tools import dp

from oemof_b3 import colors_odict, labels_dict, label_simplification
from oemof_b3.config import config


MW_to_W = 1e6


def drop_near_zeros(df, tolerance=1e-3):
    # drop columns with data that is almost zero using the sum of the absolute values
    df = df.loc[:, df.abs().sum() > tolerance]
    return df


def load_results_sequence(file_path):
    df = pd.read_csv(file_path, header=[0, 1, 2], parse_dates=[0], index_col=[0])
    return df


def load_results_sequences(directory):
    files = os.listdir(directory)

    sequences = {}

    for file in files:
        name = os.path.splitext(file)[0]

        path = os.path.join(directory, file)

        df = load_results_sequence(path)

        sequences[name] = df

    return sequences


def filter_results_sequences(df, region=None, carrier=None, tech=None):
    """
    Filters data for the specified region, carrier and tech from
    results sequences.

    Parameters
    ----------
    df: pandas.DataFrame
        DataFrame containing results sequences
    region: str
        short name for the region that shall be filtered
    carrier: str
        carrier that shall be filtered
    tech: str
        tech that shall be filtered

    Returns
    -------
    df: pandas.DataFrame
        DataFrame that contains only the selected sequences
    """
    columns = []
    regex = "^" + "-".join([item for item in [region, carrier, tech] if item])

    # append '-' if only region is given
    if not (carrier or tech):
        regex = regex + "-"

    for col in df.columns:
        if re.search(regex, col[0]) or re.search(regex, col[1]):
            columns.append(col)

    df = df[columns]

    return df


def prepare_methanation_data(flows, region):
    h2_in = filter_results_sequences(flows, region, "h2", "methanation-combine-educts")

    ch4_out = filter_results_sequences(
        flows, region, "h2", "methanation-storage_products"
    )

    ch4_out *= -1

    def map_methanation_labels(col):
        assert isinstance(col, tuple)

        if "h2" in col[0] and "methanation-combine-educts" in col[1]:
            return "H2 input"
        elif "co2" in col[0] and "methanation-combine-educts" in col[1]:
            return "CO2 input"
        elif (
            "methanation-combine-educts" in col[0]
            and "methanation-storage_educts" in col[1]
        ):
            return "H2/CO2 mix input"
        elif "methanation" in col[0] and "methanation-storage_products" in col[1]:
            return "Methane production"
        elif "methanation-storage_products" in col[0] and "ch4" in col[1]:
            return "CH4 output"
        else:
            raise ValueError(f"Column could not be mapped {col}!")

    m_reaction_data = pd.concat([h2_in, ch4_out], 1)

    m_reaction_data.columns = [
        map_methanation_labels(col) for col in m_reaction_data.columns.to_flat_index()
    ]

    m_reaction_data = m_reaction_data.loc[:, ["H2 input", "CH4 output"]]

    return m_reaction_data


def prepare_storage_data(df, labels_dict=labels_dict):

    df = plots.map_labels(df, labels_dict=labels_dict)

    return df


def plot_methanation_operation(
    sequences_el,
    sequences_heat,
    sequences_methanation_input_output,
    sequences_methanation_storage,
):
    plot_title = "B-h2-methanation"

    # plot one winter and one summer month
    # select timeframe
    year = sequences_el.index[0].year
    timeframe = [
        (f"{year}-01-01 00:00:00", f"{year}-01-31 23:00:00"),
        (f"{year}-07-01 00:00:00", f"{year}-07-31 23:00:00"),
        (f"{year}-01-01 00:00:00", f"{year}-12-31 23:00:00"),
    ]

    for start_date, end_date in timeframe:
        sequences_el_filtered = plots.filter_timeseries(
            sequences_el, start_date, end_date
        )
        sequences_el_filtered = drop_near_zeros(sequences_el_filtered)

        sequences_heat_filtered = plots.filter_timeseries(
            sequences_heat, start_date, end_date
        )
        sequences_heat_filtered = drop_near_zeros(sequences_heat_filtered)

        sequences_methanation_storage_filtered = plots.filter_timeseries(
            sequences_methanation_storage, start_date, end_date
        )
        sequences_methanation_input_output_filtered = plots.filter_timeseries(
            sequences_methanation_input_output, start_date, end_date
        )
        sequences_methanation_input_output_filtered = plots._replace_near_zeros(
            sequences_methanation_input_output_filtered
        )

        bus_name = ["B-electricity", "B-heat_central"]

        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1)
        fig.set_size_inches(20, 12, forward=True)
        fig.subplots_adjust(hspace=0.5)

        for bus_name, df, ax in zip(
            bus_name, [sequences_el_filtered, sequences_heat_filtered], (ax1, ax2)
        ):
            # convert to SI-units
            df *= MW_to_W

            df, df_demand = plots.prepare_dispatch_data(
                df,
                bus_name=bus_name,
                demand_name="demand",
                labels_dict=labels_dict,
            )

            for i in df_demand.columns:
                colors_odict[i] = "#000000"

            plots.plot_dispatch(
                ax=ax,
                df=df,
                df_demand=df_demand,
                unit="W",
                colors_odict=colors_odict,
            )

            ax.set_title(bus_name)

            for tick in ax.get_xticklabels():
                tick.set_rotation(45)

        df = sequences_methanation_input_output_filtered
        if not (df.empty or (df == 0).all().all()):
            # convert to SI-units
            df *= MW_to_W

            plots.plot_dispatch(
                ax3,
                df,
                df_demand=pd.DataFrame(),
                unit="W",
                colors_odict=colors_odict,
            )

        ax3.set_title(plot_title)

        df = prepare_storage_data(sequences_methanation_storage_filtered)

        # convert to SI-units
        df *= MW_to_W

        plots.plot_dispatch(
            ax4,
            df,
            df_demand=pd.DataFrame(),
            unit="Wh",
            colors_odict=colors_odict,
        )

        ax4.set_title("storage_content B-h2-methanation-storage")

        for ax in [ax1, ax2, ax3, ax4]:
            handles, labels = dp.reduce_labels(
                ax=ax, simple_labels_dict=label_simplification
            )
            ax.legend(
                handles=handles,
                labels=labels,
                loc="center left",
                bbox_to_anchor=(1.0, 0, 0, 1),
                fancybox=True,
                ncol=1,
                fontsize=14,
            )

        ax1.set_ylabel("Power")
        ax2.set_ylabel("Power")
        ax3.set_ylabel("Power / MW")
        ax4.set_ylabel("Storage level / MWh")
        ax4.set_xlabel("Time")

        ax1.axes.get_xaxis().set_visible(False)
        ax2.axes.get_xaxis().set_visible(False)
        ax3.axes.get_xaxis().set_visible(False)

        fig.tight_layout()
        plot_name = (
            start_date[5:7] + "-" + end_date[5:7]
            if start_date[5:7] != end_date[5:7]
            else start_date[5:7]
        )
        file_name = "methanation_operation_" + plot_name + ".png"

        plt.savefig(os.path.join(target, file_name))


if __name__ == "__main__":
    postprocessed = sys.argv[1]
    target = sys.argv[2]
    logfile = sys.argv[3]

    logger = config.add_snake_logger(logfile, "plot_dispatch")

    bus_directory = os.path.join(postprocessed, "sequences", "bus")

    component_directory = os.path.join(postprocessed, "sequences", "component")

    variable_directory = os.path.join(postprocessed, "sequences", "by_variable")

    # create the directory plotted where all plots are saved
    if not os.path.exists(target):
        os.makedirs(target)

    bus_sequences = load_results_sequences(bus_directory)

    flows = load_results_sequence(os.path.join(variable_directory, "flow.csv"))

    methanation_input_output_sequences = prepare_methanation_data(flows, "B")

    storage_sequences = load_results_sequence(
        os.path.join(variable_directory, "storage_content.csv")
    )

    methanation_storage_sequences = filter_results_sequences(
        storage_sequences, "B", "h2", "methanation"
    )

    plot_methanation_operation(
        bus_sequences["B-electricity"],
        bus_sequences["B-heat_central"],
        methanation_input_output_sequences,
        methanation_storage_sequences,
    )
