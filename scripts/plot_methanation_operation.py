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


def filter_storage_sequences(df, region, bus, component):
    """
    Columns matching the specified region, bus and component are filtered
    from the storage level data.

    Parameters
    ----------
    df: pandas.DataFrame
        DataFrame with storage filling levels
    region: str
        short name for the region that shall be filtered
    bus: str
        bus that shall be filtered
    component: str
        component that shall be filtered

    Returns
    -------
    df: pandas.DataFrame
        DataFrame that contains only the selected storage
    """
    columns = []
    str = region + "-" + bus + "-" + component
    for i in df.columns:
        if i[0].startswith(str):
            columns.append(i)
    df = df[columns]

    df = df.droplevel(["to", "type"], axis=1)
    df.columns = df.columns.str.strip(region + "-")

    df = plots.map_labels(df, labels_dict=labels_dict)

    return df


def filter_region_ts(df, region):
    columns = [col for col in df.columns if re.search(region, col[0])]
    return df.loc[:, columns]


def prepare_reaction_data(df, bus_name, labels_dict=labels_dict):
    # This script is a copy of plots.prepare_dispatch_data excluding lines on demand
    df.columns = df.columns.to_flat_index()
    for i in df.columns:
        if i[0] == bus_name:
            df[i] = df[i] * -1
    df = plots.map_labels(df, labels_dict)
    return df


def plot_methanation_operation(
    sequences_el,
    sequences_heat,
    sequences_methanation_reaction,
    sequences_methanation_storage,
):

    bus_name = ["B-electricity", "B-heat_central"]

    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1)
    fig.set_size_inches(12, 8, forward=True)
    fig.subplots_adjust(hspace=0.5)

    for bus_name, df, ax in zip(bus_name, [sequences_el, sequences_heat], (ax1, ax2)):

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

    df = prepare_reaction_data(sequences_methanation_reaction, "B-h2-methanation")
    plots.plot_dispatch(
        ax3,
        df,
        df_demand=pd.DataFrame(),
        unit="MW",
        colors_odict=colors_odict,
    )

    plots.plot_dispatch(
        ax4,
        sequences_methanation_storage,
        df_demand=pd.DataFrame(),
        unit="MWh",
        colors_odict=colors_odict,
    )

    h_l = [ax.get_legend_handles_labels() for ax in (ax1, ax2, ax3, ax4)]
    handles = [item for sublist in list(map(lambda x: x[0], h_l)) for item in sublist]
    labels = [item for sublist in list(map(lambda x: x[1], h_l)) for item in sublist]

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

    return fig


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

    methanation_reaction_sequences = filter_region_ts(
        methanation_reaction_sequences, "^B-"
    )

    methanation_storage_sequences = filter_storage_sequences(
        storage_sequences, "B", "h2", "methanation"
    )

    plot_methanation_operation(
        bus_sequences["B-electricity"],
        bus_sequences["B-heat_central"],
        methanation_reaction_sequences,
        methanation_storage_sequences,
    )

    plt.savefig(os.path.join(target, "methanation_operation.png"))
