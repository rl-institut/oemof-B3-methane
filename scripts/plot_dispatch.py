# coding: utf-8
r"""
Inputs
-------
postprocessed : str
    ``results/{scenario}/postprocessed/``: path to directory which contains the input data which
    can be plotted
plotted : str
    ``results/{scenario}/plotted/dispatch/``: path where a new directory is created and
    the plots are saved
logfile : str
    ``logs/{scenario}.log``: path to logfile

Outputs
---------
.pdf
    dispatch plot in pdf-format.
.png
    dispatch plot in png-format.
.html
    interactive plotly dispatch plot in html-format.

Description
-------------
The script creates dispatch plots based on plot_dispatch and plot_dispatch_plotly
functions in oemoflex.
The static plots are saved as pdf-files and the interactive plotly plots as html-files
in a new directory called plotted.
Timeframes and the carrier for the plot can be chosen.
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import oemoflex.tools.plots as plots
import matplotlib.dates as mdates
import oemof_b3.tools.data_processing as data_processing

from oemof_b3 import labels_dict, colors_odict, label_simplification
from oemof_b3.config import config
from oemof_b3.tools import data_processing as dp


def prepare_dispatch_data(bus_file):
    bus_name = os.path.splitext(bus_file)[0]
    bus_path = os.path.join(bus_directory, bus_file)

    data = pd.read_csv(bus_path, header=[0, 1, 2], parse_dates=[0], index_col=[0])

    # convert data to SI-unit
    MW_to_W = 1e6
    data = data * MW_to_W

    # prepare dispatch data
    df, df_demand = plots.prepare_dispatch_data(
        data,
        bus_name=bus_name,
        demand_name="demand",
        labels_dict=labels_dict,
    )

    return df, df_demand


def plot_dispatch_data(df, df_demand):
    # change colors for demand in colors_odict to black
    for i in df_demand.columns:
        colors_odict[i] = "#000000"

    # interactive plotly dispatch plot
    fig_plotly = plots.plot_dispatch_plotly(
        df=df, df_demand=df_demand, unit="W", colors_odict=colors_odict
    )
    file_name = bus_name + "_dispatch_interactive" + ".html"
    fig_plotly.write_html(
        file=os.path.join(plotted, file_name),
        # The following parameters are set according to
        # https://plotly.github.io/plotly.py-docs/generated/plotly.io.write_html.html
        # The files are much smaller now because a script tag containing the plotly.js source
        # code (~3MB) is not included in the output anymore. It is refered to plotlyjs via a
        # link in div of the plot.
        include_plotlyjs="cdn",
        full_html=False,
    )

    # normal dispatch plot
    # plot one winter and one summer month
    # select timeframe
    year = df.index[0].year
    timeframe = [
        (f"{year}-01-01 00:00:00", f"{year}-01-31 23:00:00"),
        (f"{year}-07-01 00:00:00", f"{year}-07-31 23:00:00"),
    ]

    for start_date, end_date in timeframe:
        fig, ax = plt.subplots(figsize=(12, 5))

        # filter timeseries
        df_time_filtered = plots.filter_timeseries(df, start_date, end_date)
        df_demand_time_filtered = plots.filter_timeseries(
            df_demand, start_date, end_date
        )

        if df_time_filtered.empty:
            logger.warning(f"Data for bus '{bus_name}' is empty, cannot plot.")
            continue

        # plot time filtered data
        plots.plot_dispatch(
            ax=ax,
            df=df_time_filtered,
            df_demand=df_demand_time_filtered,
            unit="W",
            colors_odict=colors_odict,
        )

        plt.grid()
        plt.title(bus_name + " dispatch", pad=20, fontdict={"size": 22})
        plt.xlabel("Date", loc="right", fontdict={"size": 17})
        plt.ylabel("Power", loc="top", fontdict={"size": 17})
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        # format x-axis representing the dates
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator())

        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position(
            [box.x0, box.y0 + box.height * 0.15, box.width, box.height * 0.85]
        )

        # Simplify legend. As there is only one color per technology, there should
        # be only one label per technology.

        handles, labels = data_processing.reduce_labels(
            ax=ax, simple_labels_dict=label_simplification
        )

        # Put a legend below current axis

        ax.legend(
            handles=handles,
            labels=labels,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.1),
            fancybox=True,
            ncol=4,
            fontsize=14,
        )

        fig.tight_layout()
        file_name = bus_name + "_" + start_date[5:7] + ".pdf"
        plt.savefig(os.path.join(plotted, file_name), bbox_inches="tight")
        file_name = bus_name + "_" + start_date[5:7] + ".png"
        plt.savefig(os.path.join(plotted, file_name), bbox_inches="tight")


def prepare_data_for_aggregation(df_stacked, df):
    if isinstance(df_stacked, type(None)):
        df_stacked = dp.stack_timeseries(df)
    else:
        df_stacked = pd.concat([df_stacked, dp.stack_timeseries(df)])

    return df_stacked


if __name__ == "__main__":
    postprocessed = sys.argv[1]
    plotted = sys.argv[2]
    logfile = sys.argv[3]

    logger = config.add_snake_logger(logfile, "plot_dispatch")

    # create the directory plotted where all plots are saved
    if not os.path.exists(plotted):
        os.makedirs(plotted)

    bus_directory = os.path.join(postprocessed, "sequences/bus/")
    bus_files = os.listdir(bus_directory)

    # select carrier
    carriers = ["electricity", "heat_central", "heat_decentral"]

    selected_bus_files = [
        file for file in bus_files for carrier in carriers if carrier in file
    ]

    # Aggregate data of busses and demand by region
    df_stacked = None
    df_demand_stacked = None

    for carrier in carriers:
        # Find all files where carrier is same and hence multiple regions exist
        busses_to_be_aggregated = [file for file in bus_files if carrier in file]
        if len(busses_to_be_aggregated) > 1:
            for bus_to_be_aggregated in busses_to_be_aggregated:
                df, df_demand = prepare_dispatch_data(bus_to_be_aggregated)

                df_stacked = prepare_data_for_aggregation(df_stacked, df)
                df_demand_stacked = prepare_data_for_aggregation(
                    df_demand_stacked, df_demand
                )

            # Exchange region from bus_name with "ALL"
            bus_name = "ALL_" + carrier

            # Aggregate bus data and demand
            df_aggregated = dp.aggregate_timeseries(
                df_stacked, columns_to_aggregate="region"
            )
            df_demand_aggregated = dp.aggregate_timeseries(
                df_demand_stacked, columns_to_aggregate="region"
            )
            # Unstack aggregated bus data and demand
            df_aggregated = dp.unstack_timeseries(df_aggregated)
            df_demand_aggregated = dp.unstack_timeseries(df_demand_aggregated)

            plot_dispatch_data(df_aggregated, df_demand_aggregated)

            # Set df_stacked and df_demand_stacked to None as preparation for new cycle
            df_stacked = None
            df_demand_stacked = None

    for bus_file in selected_bus_files:
        df, df_demand = prepare_dispatch_data(bus_file)
        plot_dispatch_data(df, df_demand)
