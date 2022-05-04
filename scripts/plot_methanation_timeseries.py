import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
from oemof.solph.processing import convert_keys_to_strings
from oemoflex.tools import plots

from oemof_b3 import colors_odict, labels_dict
from oemof_b3.config import config


def load_bus_sequences(bus_directory):
    bus_files = os.listdir(bus_directory)

    bus_sequences = {}

    for bus_file in bus_files:
        bus_name = os.path.splitext(bus_file)[0]

        bus_path = os.path.join(bus_directory, bus_file)

        sequences = pd.read_csv(
            bus_path, header=[0, 1, 2], parse_dates=[0], index_col=[0]
        )

        bus_sequences[bus_name] = sequences

    return bus_sequences


def plot_dispatch(bus_sequences):

    bus_name = ["B-electricity", "B-ch4"]

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

        if bus == "B-electricity":
            ax = ax1
        if bus == "B-ch4":
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

    # create the directory plotted where all plots are saved
    if not os.path.exists(target):
        os.makedirs(target)

    bus_sequences = load_bus_sequences(bus_directory)

    plot_dispatch(bus_sequences)

    plt.savefig(os.path.join(target, "methanation_operation.png"))
