"""Function(s) for plotting

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import pylab
from . import plotting
from .. import helper
from .. import analysis
from .. import files


def plot_asset_total_absolute_returns_accumulated(dates, returns, fname, analyzer, config):
    """Plots the accumulated absolute returns
    :param dates: List of dates
    :param returns: List of day-wise, summed returns of all investments
    :param fname: Name of the file/plot to be saved
    :param analyzer: Analyzer-instance (cached datetime conversions)
    :param config: PROFIT's config-instance
    """
    # Get the full path of the file:
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(returns) == 0:
        print(f"No assets given for plot: {fname}")
        return

    if len(dates) != len(returns):
        raise RuntimeError("The summed list and date-list must correspond in length.")

    if helper.list_all_zero(returns) is True:
        print(f"All summed asset values are zero. Not plotting. File: {fname.name}")
        return

    # Plot:
    plotting.configure_lineplot(config)
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    x = [analyzer.str2datetime(x) for x in dates]

    ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='', linewidth=1.6)
    # Label the last value:
    last_val = f"{returns[-1]:.2f}"
    ax.text(x[-1], returns[-1], last_val)

    # Add a comma to separate thousands:
    ax.get_yaxis().set_major_formatter(pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.set_xlabel("Dates")
    ax.set_ylabel(f"Absolute Returns ({config.BASECURRENCY})")
    plt.title("Summed absolute returns of all investments in analysis period")

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        plotting.open_plot(fname)


def plot_asset_returns_individual_absolute(assetlist, fname, analyzer, config):
    """Plots different absolute returns of each asset in an individual plot.
    The plots are created on a 2x3 grid
    :param assetlist: List of asset-objects
    :param fname: String of desired plot filename
    :param analyzer: Analyzer-instance (cached datetime conversions)
    :param config: PROFIT's config-instance
    """
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print(f"No assets given for plot: {fname.name}")
        return [0], [0]

    # Only plot assets with some value during the analysis period:
    assetlist_plot = []
    for asset in assetlist:
        if any(x > 1e-9 for x in asset.get_analysis_valuelist()):
            assetlist_plot.append(asset)

    if len(assetlist_plot) == 0:
        print(f"No assets of value given at the end of the analysis-period. Not plotting. File: {fname.name}")
        return [0], [0]

    dateformat = assetlist_plot[0].get_dateformat()
    if len(assetlist_plot) > 1:
        for asset in assetlist_plot[1:]:
            if asset.get_dateformat() != dateformat:
                raise RuntimeError("The dateformats of the assets must be identical.")

    # Get a list of asset-lists, whereas each top-level list contains 6 plots, for a single plot-sheet.
    assetlists_sheet = helper.partition_list(assetlist_plot, 6)
    num_sheets = len(assetlists_sheet)
    print(f"Plotting the asset-values with {num_sheets:d} figure-sheet(s). Filename: {fname.name}")

    xlabel = "Date"
    ylabel = "Return (Absolute; Currency)"

    dates = assetlist_plot[0].get_analysis_datelist()
    returns_total = [0.0] * len(dates)

    for sheet_num, assets in enumerate(assetlists_sheet):

        plotting.configure_gridplot(config)
        fig = plt.figure()
        fig.subplots_adjust(hspace=0.4, wspace=0.4)

        for idx, asset in enumerate(assets):
            plotidx = idx + 1
            ax = fig.add_subplot(2, 3, plotidx)
            try:
                dates, returns = analysis.calc_returns_asset_daily_absolute_analysisperiod(asset)
                returns_total = [a + b for a, b in zip(returns, returns_total)]
                x = [analyzer.str2datetime(i) for i in dates]
                ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='',
                        label="Absolute Returns")
            except:
                plt.text(0.05, 0.5, "Something went wrong", horizontalalignment='left',
                         verticalalignment='center',
                         transform=ax.transAxes, fontsize=7, bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'))

            # Format the y-axis labels
            ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))

            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            assetname = asset.get_filename()
            assetname = files.get_filename(assetname, keep_suffix=False)
            titlestr = f"Abs. Return/Gain: {assetname.name}"
            plt.title(titlestr)

            # Only use autofmt_xdate, if there are actually 6 plots on the sheet. Otherwise, the axis-labels of the
            # upper subplot-row disappear (this is a feature of autofmt_xdate...
            # This has to be done for each subplot
            if len(assets) < 6:
                # Only rotate the labels and right-align them; same as autofmt_xdate
                plt.setp(plt.xticks()[1], rotation=30, ha='right')

        # Only use autofmt_xdate, if there are actually 6 plots on the sheet. Otherwise, the axis-labels of the upper
        # subplot-row disappear (this is a feature of autofmt_xdate...
        if len(assets) == 6:
            # Nicer date-plotting:
            fig.autofmt_xdate()
            ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')
        elif len(assets) > 6:
            raise RuntimeError("More than 6 plots on the subplot-sheet are not possible.")

        fname_ext = files.filename_append_number(fname, "_", sheet_num + 1)

        # PDF Export:
        plt.savefig(fname_ext)

        if config.OPEN_PLOTS is True:
            plotting.open_plot(fname_ext)

    return dates, returns_total
