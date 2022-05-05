import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
from oemoflex.tools import plots

from oemof_b3 import colors_odict, labels_dict
from oemof_b3.config import config


def load_results_sequences(directory):
    files = os.listdir(directory)

    sequences = {}

    for file in files:
        name = os.path.splitext(file)[0]

        path = os.path.join(directory, file)

        df = pd.read_csv(path, header=[0, 1, 2], parse_dates=[0], index_col=[0])

        sequences[name] = df

    return sequences


def plot_methanation_operation(sequences_el, sequences_heat, methanation):

    bus_name = ["B-electricity", "B-ch4"]

    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1)
    fig.set_size_inches(12, 8, forward=True)
    fig.subplots_adjust(hspace=0.5)

    for bus_name, df, ax in zip(
        ["electricity", "heat"], [sequences_el, sequences_heat], (ax1, ax2)
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


if __name__ == "__main__":
    postprocessed = sys.argv[1]
    target = sys.argv[2]
    logfile = sys.argv[3]

    logger = config.add_snake_logger(logfile, "plot_dispatch")

    bus_directory = os.path.join(postprocessed, "sequences", "bus")

    component_directory = os.path.join(postprocessed, "sequences", "component")

    # create the directory plotted where all plots are saved
    if not os.path.exists(target):
        os.makedirs(target)

    bus_sequences = load_results_sequences(bus_directory)

    methanation_sequences = load_results_sequences(component_directory)[
        "methanation_reactor"
    ]

    plot_methanation_operation(
        bus_sequences["B-electricity"],
        bus_sequences["B-heat_central"],
        methanation_sequences,
    )

    plt.savefig(os.path.join(target, "methanation_operation.png"))
