"""Function(s) for plotting

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import matplotlib
import matplotlib.pyplot as plt
import pylab
from . import plotting
from .. import analysis
from .. import helper


def plot_asset_projections(assetlist, interest, num_years, fname, titlestr, analyzer, config):
    """Plots the past summed value of the assets and projects the value into the future, assuming a certain
    interest rate. Compounded growth is assumed.
    :param assetlist: List of asset-objects. Their value will be summed and used for the projection.
    :param interest: yearly interest rate (in percent) used for the projection
    :param num_years: Nr. of years projected into the future.
    :param fname: String of filename of plot
    :param titlestr: String of plot-title
    """
    # Get the full path of the file:
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
        return

    if num_years < 1:
        print("Cannot project less than 1 year in advance. Plot: " + fname)
        return

    # The date-range of the analysis-period (should be identical in all assets)
    datelist = assetlist[0].get_analysis_datelist()
    # The summed value for each day, over all assets:
    sumlist = analysis.get_asset_values_summed(assetlist)
    # Sanity check:
    if len(datelist) != len(sumlist):
        raise RuntimeError("The summed list and date-list must correspond in length.")

    if helper.list_all_zero(sumlist) is True:
        print("All summed asset values are zero. Not plotting. File: " + fname)
        return

    datelist_fut, vallist_fut_base = analysis.project_values(datelist, sumlist, num_years, interest, config.FORMAT_DATE)
    # Vary interest rates by +/- 10% and also show these values:
    tolband = 10.0
    fact_up = (tolband / 100.0) + 1.0
    fact_low = 1.0 - (tolband / 100.0)
    _, vallist_fut_upper = analysis.project_values(datelist, sumlist, num_years,
                                                   interest * fact_up, config.FORMAT_DATE)
    _, vallist_fut_lower = analysis.project_values(datelist, sumlist, num_years,
                                                   interest * fact_low, config.FORMAT_DATE)

    # Plot:
    plotting.configure_lineplot(config)
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    x = [analyzer.str2datetime(x) for x in datelist_fut]

    labelstr = f"{(interest * fact_up):.2f} %"
    ax.plot(x, vallist_fut_upper, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='',
            label=labelstr, linewidth=1.6)
    # Label the last value:
    last_val = f"{vallist_fut_upper[-1]:.2f}"
    ax.text(x[-1], vallist_fut_upper[-1], last_val)

    labelstr = f"{interest:.2f} %"
    ax.plot(x, vallist_fut_base, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[1], marker='',
            label=labelstr, linewidth=1.6)
    # Label the last value:
    last_val = f"{vallist_fut_base[-1]:.2f}"
    ax.text(x[-1], vallist_fut_base[-1], last_val)

    labelstr = f"{(interest * fact_low):.2f} %"
    ax.plot(x, vallist_fut_lower, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[2], marker='',
            label=labelstr, linewidth=1.6)
    # Label the last value:
    last_val = f"{vallist_fut_lower[-1]:.2f}"
    ax.text(x[-1], vallist_fut_lower[-1], last_val)

    plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='upper left',
               bbox_to_anchor=(0.01, 0.99))

    # Add a comma to separate thousands:
    ax.get_yaxis().set_major_formatter(pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.set_xlabel("Dates")
    ax.set_ylabel(f"Values ({config.BASECURRENCY})")
    ax.set_ylim(ymin=0)  # Looks better
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        plotting.open_plot(fname)
