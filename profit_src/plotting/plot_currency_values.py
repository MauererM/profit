"""Function(s) for plotting

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import matplotlib
import matplotlib.pyplot as plt
from . import plotting
from .. import helper


def plot_currency_values(assetlist, fname, titlestring, analyzer, config, drawstackedplot=True):
    """Plots the values of the assets grouped according to their currencies
    :param assetlist: List of asset-objects
    :param fname: String of desired filename
    :param titlestring: String of title of plot
    :param drawstackedplot: If True, the absolute values are plotted as stacked plot. If false, the relative values are
    plotted in a line plot
    """
    # Sanity checks:
    if len(assetlist) < 1:
        return

    # Get the full path of the file:
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)

    # x-data for the plots:
    datelist = assetlist[0].get_analysis_datelist()  # Should be the same length everywhere -
    # we consider the analysis range...
    xlist = [analyzer.str2datetime(x) for x in datelist]

    # Collect the currencies:
    curlist = [asset.get_currency() for asset in assetlist]
    curset = set(curlist)

    # Collect the values, grouped by the currency:
    curvals = []  # List of lists that stores the summed values of each currency:
    for currency in curset:
        # Iterate through all assets:
        sumvals = [0] * len(xlist)
        for idx, asset in enumerate(assetlist):
            if curlist[idx] == currency:
                values = asset.get_analysis_valuelist()
                sumvals = helper.sum_lists([sumvals, values])
        curvals.append(sumvals)

    colorlist = plotting.create_colormap("rainbow", len(curset), False)
    xlabel = "Date"
    if drawstackedplot is True:
        ylabel = f"Value ({config.BASECURRENCY})"
        alpha = 0.8
        plotting.create_stackedplot(xlist, curvals, list(curset), colorlist, titlestring, xlabel, ylabel, alpha,
                                    fname, config)

    else:  # Create a line-plot:
        # The relative values of the currencies are plotted:
        # Get the total value of the assets:
        totvals = []
        for idx, x in enumerate(xlist):
            sumval = 0
            for vallist in curvals:
                sumval = sumval + vallist[idx]
            totvals.append(sumval)
        # Get the relative values of the currency-groups:
        curvals_rel = []
        for vallist in curvals:
            # careful with zero division...
            rel = [(val / totvals[i] * 100.0) if totvals[i] > 1e-9 else 0 for i, val in enumerate(vallist)]
            curvals_rel.append(rel)

        # Sort the values, such that the colors coincide with the stacked plot:
        # Sort the y-values according to the most recent value:
        sortlist = [x[-1] for x in curvals]
        sortedidx = sorted(range(len(sortlist)), key=lambda x: sortlist[x])
        sortedidx.reverse()
        # Sort the lists:
        curvals_rel = [curvals_rel[i] for i in sortedidx]
        legendlist = list(curset)
        legendlist = [legendlist[i] for i in sortedidx]

        plotting.configure_lineplot(config)
        fig = plt.figure()
        ax = fig.add_subplot(111)

        for idx, rellist in enumerate(curvals_rel):
            ax.plot(xlist, rellist, alpha=1.0, zorder=3, clip_on=False, color=colorlist[idx], marker='',
                    label=legendlist[idx])
            # Label the last value:
            last_val = f"{rellist[-1]:.2f}"
            ax.text(xlist[-1], rellist[-1], last_val)

        plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

        ax.set_xlabel(xlabel)
        ax.set_ylabel("Relative Value (%)")
        plt.title(titlestring)

        # Nicer date-plotting:
        fig.autofmt_xdate()
        ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

        # PDF Export:
        plt.savefig(fname)

        if config.OPEN_PLOTS is True:
            plotting.open_plot(fname)
