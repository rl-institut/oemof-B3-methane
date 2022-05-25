import os
import sys
import re

import matplotlib.pyplot as plt
import pandas as pd
from oemoflex.tools import plots

from oemof_b3 import colors_odict, labels_dict
from oemof_b3.config import config


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


def prepare_reaction_data(df, bus_name, labels_dict=labels_dict):
    # This script is a copy of plots.prepare_dispatch_data excluding lines on demand
    df.columns = df.columns.to_flat_index()
    for i in df.columns:
        if i[0] == bus_name:
            df[i] = df[i] * -1
    df = plots.map_labels(df, labels_dict)
    return df


def prepare_storage_data(df, labels_dict=labels_dict):

    df = plots.map_labels(df, labels_dict=labels_dict)

    return df


def plot_methanation_operation(
    sequences_el,
    sequences_heat,
    sequences_methanation_reaction,
    sequences_methanation_storage,
):

    # plot one winter and one summer month
    # select timeframe
    year = sequences_el.index[0].year
    timeframe = [
        (f"{year}-01-01 00:00:00", f"{year}-01-31 23:00:00"),
        (f"{year}-07-01 00:00:00", f"{year}-07-31 23:00:00"),
    ]

    for start_date, end_date in timeframe:
        sequences_el_filtered = plots.filter_timeseries(
            sequences_el, start_date, end_date
        )

        sequences_heat_filtered = plots.filter_timeseries(
            sequences_heat, start_date, end_date
        )
        sequences_methanation_storage_filtered = plots.filter_timeseries(
            sequences_methanation_storage, start_date, end_date
        )
        sequences_methanation_reaction_filtered = plots.filter_timeseries(
            sequences_methanation_reaction, start_date, end_date
        )
        bus_name = ["B-electricity", "B-heat_central"]

        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1)
        fig.set_size_inches(12, 8, forward=True)
        fig.subplots_adjust(hspace=0.5)

        for bus_name, df, ax in zip(
            bus_name, [sequences_el_filtered, sequences_heat_filtered], (ax1, ax2)
        ):

            df, df_demand = plots.prepare_dispatch_data(
                df,
                bus_name=bus_name,
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

        df = prepare_reaction_data(
            sequences_methanation_reaction_filtered, "B-h2-methanation"
        )
        if not (df.empty or (df == 0).all().all()):
            plots.plot_dispatch(
                ax3,
                df,
                df_demand=pd.DataFrame(),
                unit="MW",
                colors_odict=colors_odict,
            )

        df = prepare_storage_data(sequences_methanation_storage_filtered)
        plots.plot_dispatch(
            ax4,
            df,
            df_demand=pd.DataFrame(),
            unit="MWh",
            colors_odict=colors_odict,
        )

        h_l = [ax.get_legend_handles_labels() for ax in (ax1, ax2, ax3, ax4)]
        handles = [
            item for sublist in list(map(lambda x: x[0], h_l)) for item in sublist
        ]
        labels = [
            item for sublist in list(map(lambda x: x[1], h_l)) for item in sublist
        ]

        # The last two labels are identical with the previous two and are therefore removed.
        labels = labels[:-2]

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
        ax3.set_ylabel("Power / MW")
        ax4.set_ylabel("Storage level / MWh")
        ax4.set_xlabel("Time")

        ax1.axes.get_xaxis().set_visible(False)
        ax2.axes.get_xaxis().set_visible(False)
        ax3.axes.get_xaxis().set_visible(False)

        fig.tight_layout()

        file_name = "methanation_operation" + "_" + start_date[5:7] + ".png"

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

    methanation_reaction_sequences = load_results_sequence(
        os.path.join(component_directory, "methanation_reactor.csv")
    )

    storage_sequences = load_results_sequence(
        os.path.join(variable_directory, "storage_content.csv")
    )

    methanation_reaction_sequences = filter_results_sequences(
        methanation_reaction_sequences, "B"
    )

    methanation_storage_sequences = filter_results_sequences(
        storage_sequences, "B", "h2", "methanation"
    )

    plot_methanation_operation(
        bus_sequences["B-electricity"],
        bus_sequences["B-heat_central"],
        methanation_reaction_sequences,
        methanation_storage_sequences,
    )
