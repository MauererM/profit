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
from .. import files
from .. import investment


def plot_asset_values_indices(assetlist, indexlist, fname, titlestr, analyzer, config):
    """Plots the summed values of the given assets, together with some stock-market indices
    :param assetlist: List of asset-objects
    :param indexlist: List of Index-objects that contain the index-data
    :param fname: String of filename of plot
    :param titlestr: String of plot-title
    """
    # Get the full path of the file:
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print(f"No assets given for plot: {fname}")
        return

    # The date-range of the analysis-period (should be identical in all assets)
    datelist = assetlist[0].get_analysis_datelist()
    # The summed value for each day, over all assets:
    sumlist = analysis.get_asset_values_summed(assetlist)
    # The out/inflows are also considered to match the graphs better:
    sumlist_inflows = analysis.get_asset_inflows_summed(assetlist)
    sumlist_outflows = analysis.get_asset_outflows_summed(assetlist)
    sumlist_payouts = analysis.get_asset_payouts_summed(assetlist)
    sumlist_costs = analysis.get_asset_costs_summed(assetlist)
    # Sanity check:
    if len(datelist) != len(sumlist) or len(datelist) != len(sumlist_inflows) or len(datelist) != len(sumlist_outflows):
        raise RuntimeError("The summed list(s) and date-list must all correspond in length.")

    if helper.list_all_zero(sumlist) is True:
        print(f"All summed asset values are zero. Not plotting. File: {fname}")
        return

    # Subtract/Add the in/outflows to the summed value. Like this, there are not spikes in the value, and the
    # performance can be compared to the portfolio:
    sumlist_corr = []
    sum_inflow = 0.0
    sum_outflow = 0.0
    sum_payout = 0.0
    sum_cost = 0.0
    for idx, val in enumerate(sumlist):
        sum_inflow += sumlist_inflows[idx]
        sum_outflow += sumlist_outflows[idx]
        sum_payout += sumlist_payouts[idx]
        sum_cost += sumlist_costs[idx]
        sumlist_corr.append(val - sum_inflow + sum_outflow + sum_payout - sum_cost)

    # Obtain stock-market indices:
    indexvals = []  # List of lists
    indexname = []
    for stockidx in indexlist:
        # Check if the object actually contains data:
        if stockidx.is_price_avail() is True:
            dat = stockidx.get_values()
            if len(dat) != len(datelist):
                raise RuntimeError("The stockmarket-index-data must be of equal length than the asset values.")
            indexvals.append(dat)
            indexname.append(stockidx.get_name())  # The name of the index is stored as currency

    # Rescale the summed values such that the first entry is "100":
    startidx = [i for i, x in enumerate(sumlist_corr) if x > 1e-9 or x < -1e-9][0]
    fact = sumlist_corr[startidx] / 100.0
    if fact != 0.0:
        sumlist_corr = [x / fact for x in sumlist_corr]

    # The index-values have to be rescaled to the asset-values (at the beginning of the analysis-period)
    # Find the first (summed) asset-value > 0:
    indexvals_rs = []
    for vals in indexvals:
        fact = vals[startidx] / sumlist_corr[startidx]
        indexvals_rs.append([x / fact for x in vals])

    # Plot:
    plotting.configure_lineplot(config)
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    x = [analyzer.str2datetime(x) for x in datelist]
    ax.plot(x, sumlist_corr, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='',
            label="Asset Value",
            linewidth=1.6)
    # Label the last value:
    last_val = f"{sumlist_corr[-1]:.2f}"
    ax.text(x[-1], sumlist_corr[-1], last_val)

    # Plot the indexes:
    # Obtain some colors for the indexes:
    # colors = create_colormap('rainbow', len(indexvals_rs), invert_colorrange=False)
    for i, val in enumerate(indexvals_rs):
        if i > len(config.PLOTS_COLORS) - 1:
            raise RuntimeError("Ran out of colors. Supply more in PLOTS_COLORS (configuration-file)")
        ax.plot(x, val, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[i + 1], marker='',
                label=indexname[i])
        # Label the last value:
        last_val = f"{val[-1]:.2f}"
        ax.text(x[-1], val[-1], last_val)

    plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='upper left',
               bbox_to_anchor=(0.01, 0.99))

    # Add a comma to separate thousands:
    ax.get_yaxis().set_major_formatter(pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.set_xlabel("Dates")
    ax.set_ylabel("Normalized Value")
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        plotting.open_plot(fname)


def plot_asset_values_cost_payout_individual(assetlist, fname, analyzer, config):
    """Plots the values of assets, with and without cost and payouts
    The plots are created on a 2x3 grid
    :param assetlist: List of asset-objects
    :param fname: String for desired filename
    """
    # Get the full path of the file:
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print(f"No assets given for plot: {fname}")
        return

    # Only plot assets with some value during the analysis period:
    assetlist_plot = []
    for asset in assetlist:
        if any(x > 1e-9 for x in asset.get_analysis_valuelist()):
            assetlist_plot.append(asset)

    if len(assetlist_plot) == 0:
        print(f"No assets of value given at the end of the analysis-period. Not plotting. File: {fname.name}")
        return

    dateformat = assetlist_plot[0].get_dateformat()
    if len(assetlist_plot) > 1:
        for asset in assetlist_plot[1:]:
            if asset.get_dateformat() != dateformat:
                raise RuntimeError("The dateformats of the assets must be identical.")

    # Get a list of asset-lists, whereas each top-level list contains 6 plots, for a single plot-sheet.
    assetlists_sheet = analysis.partition_list(assetlist_plot, 6)
    num_sheets = len(assetlists_sheet)
    print(f"Plotting the asset-values with {num_sheets:d} figure-sheet(s). Filename: {fname.name}")

    xlabel = "Date"
    ylabel = f"Value ({config.BASECURRENCY})"

    for sheet_num, assets in enumerate(assetlists_sheet):

        plotting.configure_gridplot(config)
        fig = plt.figure()
        fig.subplots_adjust(hspace=0.4, wspace=0.4)
        for idx, asset in enumerate(assets):
            plotidx = idx + 1
            ax = fig.add_subplot(2, 3, plotidx)

            # Obtain the returns in 7-day periods:
            dates = analyzer.get_analysis_datelist()
            values = asset.get_analysis_valuelist()
            costs = asset.get_analysis_costlist()
            payouts = asset.get_analysis_payoutlist()
            costs_accu = helper.accumulate_list(costs)
            payouts_accu = helper.accumulate_list(payouts)
            # Datetime for matplotlib:
            x = analyzer.get_analysis_datelist_dt()
            # Don't plot too many markers:
            if len(dates) < 40.0:
                marker_div = 1
            else:
                marker_div = int(len(dates) / 40.0)

            # Plot the asset's total value:
            ax.plot(x, values, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='o',
                    label="Asset Value",
                    markevery=marker_div)

            if helper.list_all_zero(payouts_accu) is False:
                values_payouts = helper.sum_lists([values, payouts_accu])
                ax.plot(x, values_payouts, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[1], marker='x',
                        label="Asset Value, with Payouts", markevery=marker_div)
            else:
                values_payouts = list(values)

            # Only plot cost, payouts, if there is actually some cost or payout:
            if helper.list_all_zero(costs_accu) is False:
                values_payouts_cost = helper.diff_lists(values_payouts, costs_accu)
                ax.plot(x, values_payouts_cost, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[2],
                        marker='d', label="Asset Value, with Payouts and Costs", markevery=marker_div)

            if isinstance(asset, investment.Investment):
                # Obtain the asset's return of the whole analysis-period:
                ret_a = analysis.get_returns_asset_analysisperiod(asset, analyzer)
                # Obtain the asset's holding period return:
                ret_h = analysis.get_return_asset_holdingperiod(asset)
                if ret_h is not None:
                    ret_str = f"Analysis Period Return: {ret_a:.1f}%\nHolding Period Return: {ret_h:.1f}%"
                else:
                    ret_str = f"Analysis Period Return: {ret_a:.1f}%\nHolding Period Return: N/A (missing price of today)"
                # Place the text relative to the axes:
                plt.text(0.05, 0.78, ret_str, horizontalalignment='left', verticalalignment='center',
                         transform=ax.transAxes, fontsize=7, bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'))

            plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            assetname = asset.get_filename()
            assetname = files.get_filename(assetname, keep_suffix=False)
            assettype = asset.get_type()
            titlestr = f"Values: {assetname.name} (in {config.BASECURRENCY}, {assettype})"
            plt.title(titlestr)

            # Add a comma to separate thousands:
            ax.get_yaxis().set_major_formatter(pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

            # Nicer date-plotting:
            fig.autofmt_xdate()
            ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

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


def plot_asset_values_stacked(assetlist, fname, title, analyzer, config):
    """This function plots the values of the given assets with a stacked plot.
    :param assetlist: List of asset-objects
    :param fname: String of desired filename
    :param title: String of plot title
    """
    # Get the full path of the file:
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print(f"No assets given for plot: {fname.name}")
        return

    if len(assetlist) == 0:
        print(f"No assets given for plot: {fname.name}")
        return

    dateformat = assetlist[0].get_dateformat()
    if len(assetlist) > 1:
        for asset in assetlist[1:]:
            if asset.get_dateformat() != dateformat:
                raise RuntimeError("The dateformats of the assets must be identical.")

    if len(assetlist) == 0:
        print("No assets given. Not creating stacked value plot.")
        return

    # Identify assets that do not hold any value for the considered period
    assets_plt = []
    for asset in assetlist:
        bal = asset.get_analysis_valuelist()
        # Check if all values are zero:
        if helper.list_all_zero(bal) is False:
            assets_plt.append(asset)

    if len(assets_plt) == 0:
        print("All assets contain zero value. Not plotting.")
        return

    # The dates should be identical for all accounts, due to the way the data is generated:
    # Matplotlib takes a datetime-list:
    xlist = analyzer.get_analysis_datelist_dt()
    # Generate a list of the lists of values
    ylists = []
    legendlist = []
    for asset in assets_plt:
        ylists.append(asset.get_analysis_valuelist())
        legendlist.append(asset.get_filename())

    colorlist = plotting.create_colormap("rainbow", len(ylists), False)

    titlestring = f"{title}. Currency: {config.BASECURRENCY}"
    xlabel = "Date"
    ylabel = f"Value ({config.BASECURRENCY})"
    alpha = 0.75  # Plot transparency
    # Plot:
    plotting.create_stackedplot(xlist, ylists, legendlist, colorlist, titlestring, xlabel, ylabel, alpha, fname, config)
