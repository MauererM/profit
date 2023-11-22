"""Functions for plotting assets
This file is quite long, as some plotting methods require some specific handling of data

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import pylab
from . import stringoperations
from . import analysis
from . import config
from . import plotting_aux
from . import helper
from . import files

# Todo clean up this massive file

def plot_currency_values(assetlist, fname, titlestring, analyzer, drawstackedplot=True):
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
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)

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
                sumvals = helper.sum_lists(sumvals, values)
        curvals.append(sumvals)

    colorlist = plotting_aux.create_colormap("rainbow", len(curset), False)
    xlabel = "Date"
    if drawstackedplot is True:
        ylabel = "Value (" + config.BASECURRENCY + ")"
        alpha = 0.8
        plotting_aux.create_stackedplot(xlist, curvals, list(curset), colorlist, titlestring, xlabel, ylabel, alpha,
                                        fname)

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

        plotting_aux.configure_lineplot()
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
            plotting_aux.open_plot(fname)


def plot_asset_groups(assets, grouplist, groupnames, fname, titlestring, analyzer):
    """Plots the values of each user-defined group.
    Each group is on a new plot.
    :param assets: List of assets
    :param grouplist: List of lists of groups
    :param groupnames: List of names of grouplist-lists
    :param fname: Filename for plot, will be appended with the name of the group
    :param titlestring: Title of the plot. Also appended with the name of the group
    """
    # Sanity checks:
    if len(grouplist) != len(groupnames):
        raise RuntimeError("List of groups and list of corresponding names must be of identical length")
    if len(grouplist) < 1:
        print("No groups given, cannot plot different groups.")
        return
    if len(assets) < 1:
        print("No assets given, cannot plot different groups.")
        return

    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)

    # Strip white spaces of group names, for better plotting/file names:
    groupnames = [stringoperations.strip_whitespaces(x) for x in groupnames]

    # Collect the purposes of all available assets:
    asset_purposes = [asset.get_purpose() for asset in assets]

    # Iterate through all the groups (which collects different purposes)
    for purpidx, purposelist in enumerate(grouplist):

        # One plot per group:
        plotting_aux.configure_lineplot()
        fig = plt.figure()
        ax = fig.add_subplot(111)

        colorlist = plotting_aux.create_colormap("rainbow", len(purposelist) + 1, False)

        datelist = assets[0].get_analysis_datelist()  # Should be the same length everywhere -
        # we consider the analysis range...
        xlist = [analyzer.str2datetime(x) for x in datelist]

        # This holds the total value of the group:
        totsum = [0] * len(datelist)

        # Get the values of each purpose, from all assets:
        plotted = False
        for k, purpose in enumerate(purposelist):
            # Get the indices of the assets with the current purpose:
            indexes = [i for i, x in enumerate(asset_purposes) if x == purpose]
            # Only plot, if there's actually an asset with the given purpose:
            if len(indexes) > 0:
                # Sum the values of each purpose:
                sumvals = [0] * len(datelist)
                for idx in indexes:
                    values = assets[idx].get_analysis_valuelist()
                    sumvals = helper.sum_lists(sumvals, values)

                # For the total of the group:
                totsum = helper.sum_lists(totsum, sumvals)
                ax.plot(xlist, sumvals, alpha=1.0, zorder=3, clip_on=False, color=colorlist[k], marker='',
                        label=purpose)
                plotted = True
                # Label the last value:
                last_val = f"{sumvals[-1]:.2f}"
                ax.text(xlist[-1], sumvals[-1], last_val)

        # Plot the total sum of the group (only, if there are multiple constituents in a group)
        if len(purposelist) > 1 and plotted is True:
            totlabel = "Total Group Value of " + groupnames[purpidx]
            ax.plot(xlist, totsum, alpha=1.0, zorder=3, clip_on=False, color=colorlist[len(purposelist)], marker='',
                    label=totlabel)
            # Label the last value:
            last_val = f"{totsum[-1]:.2f}"
            ax.text(xlist[-1], totsum[-1], last_val)

        # Only plot if there is actually a value in a group:
        if plotted is True:
            plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

            ax.set_xlabel("Dates")
            ax.set_ylabel("Value " + "(" + config.BASECURRENCY + ")")
            titlestr_mod = titlestring + ". Group: " + groupnames[purpidx]
            plt.title(titlestr_mod)

            # Nicer date-plotting:
            fig.autofmt_xdate()
            ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

            # Modify the file name: add the name of the group:
            fname_cur = files.filename_append_string(fname, "_", groupnames[purpidx])

            # PDF Export:
            plt.savefig(fname_cur)

            if config.OPEN_PLOTS is True:
                plotting_aux.open_plot(fname_cur)


def plot_forex_rates(forexobjdict, fname, titlestr, analyzer):
    """Plot the forex rates.
    The forex-objects are stored in a dictionary, whose keys are the strings of the currencies, e.g., "USD".
    :param forexobjdict: Dictionary with the forex-objects
    :param fname: String of the filename of the plot
    :param titlestr: String of the title of the plot
    """

    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)

    plotting_aux.configure_lineplot()
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    colorlist = plotting_aux.create_colormap("rainbow", len(forexobjdict), False)
    i = 0
    # Iterate through the dictionary, only plot foreign currencies:
    for key, obj in forexobjdict.items():
        # Only plot foreign rates:
        if key != config.BASECURRENCY:
            date, rate = obj.get_price_data()
            xlist = [analyzer.str2datetime(x) for x in date]
            ax.plot(xlist, rate, alpha=1.0, zorder=3, clip_on=False, color=colorlist[i], marker='',
                    label=obj.get_currency())
            # Label the last value:
            last_val = f"{rate[-1]:.2f}"
            ax.text(xlist[-1], rate[-1], last_val)
            # Also plot the moving average:
            x_ma, y_ma = analysis.calc_moving_avg(xlist, rate, config.WINLEN_MA)
            linelabel = obj.get_currency() + ", Moving Avg"
            ax.plot(x_ma, y_ma, alpha=1.0, zorder=3, clip_on=False, color=colorlist[i], marker='',
                    label=linelabel, dashes=config.DASHES_MA)
        i += 1

    plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

    ax.set_xlabel("Dates")
    ax.set_ylabel("Exchange Rates with " + config.BASECURRENCY)
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        plotting_aux.open_plot(fname)


def plot_assets_grouped(assetlist, fname, titlestr, plottype, analyzer):
    """Plots the values of the assets, grouped according to their groups (see main-file)
    A stacked plot is used.
    :param assetlist: List of asset-objects
    :param fname: String of desired file-name for the plot
    :param titlestr: String of the plot's title
    :param plottype: String, either "line" or "stacked"; for the type of plot.
    :return:
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
        return

    if len(config.ASSET_GROUPNAMES) != len(config.ASSET_GROUPS):
        raise RuntimeError("The length of the asset-groups-list must be equal to the length of the list of the "
                           "asset-group names.")

    # Collect all asset purposes:
    purplist = []
    for asset in assetlist:
        purplist.append(asset.get_purpose())

    # If the configured asset-purposes are different from what is recorded from the actual assets: (at least, in length)
    purp_set = set(purplist)
    if len(config.ASSET_PURPOSES) < len(purp_set):
        raise RuntimeError("Assets with differing purposes than what ASSET_PURPOSES defines are found. "
                           "This should not happen.")

    vals_groups = []
    labels_groups = []
    # Collect the assets of a group and sum up their value
    for idx, group in enumerate(config.ASSET_GROUPS):
        # Just to make sure there are no double entries in our group:
        group_set = set(group)
        # Determine all the assets that belong to the current group:
        assets_cur = [assetlist[i] for i, purp in enumerate(purplist) if purp in group_set]
        # Only sum, if there is actually an asset of the selected group:
        if len(assets_cur) > 0:
            # Sum the value of these assets:
            assets_val = analysis.get_asset_values_summed(assets_cur)
            # Store the summed values of the group:
            vals_groups.append(assets_val)
            labels_groups.append(config.ASSET_GROUPNAMES[idx])

    # Create a stacked plot:
    xlist = assetlist[0].get_analysis_datelist()
    xlist = [analyzer.str2datetime(x) for x in xlist]

    colorlist = plotting_aux.create_colormap("rainbow", len(vals_groups), False)

    xlabel = "Date"
    ylabel = "Value (" + config.BASECURRENCY + ")"
    alpha = 0.75  # Plot transparency

    # Plot:
    if plottype == "stacked":
        plotting_aux.configure_stackedplot()
        plotting_aux.create_stackedplot(xlist, vals_groups, labels_groups, colorlist, titlestr, xlabel, ylabel, alpha,
                                        fname)
    elif plottype == "line":
        plotting_aux.configure_lineplot()
        fig = plt.figure()
        ax = fig.add_subplot(111)  # Only one plot

        for idx, val in enumerate(vals_groups):
            if idx > len(config.PLOTS_COLORS) - 1:
                raise RuntimeError("Not enough colors in PLOTS_COLORS (in config-file) given...")
            ax.plot(xlist, val, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[idx], marker='',
                    label=labels_groups[idx])
            # Label the last value:
            last_val = f"{val[-1]:.2f}"
            ax.text(xlist[-1], val[-1], last_val)

        plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

        # Add a comma to separate thousands:
        ax.get_yaxis().set_major_formatter(
            pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        ax.set_xlabel("Dates")
        ax.set_ylabel("Values (" + config.BASECURRENCY + ")")
        plt.title(titlestr)

        # Nicer date-plotting:
        fig.autofmt_xdate()
        ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

        # PDF Export:
        plt.savefig(fname)

        if config.OPEN_PLOTS is True:
            plotting_aux.open_plot(fname)

    else:
        raise RuntimeError("Unknown plottype. Only 'stacked' or 'line' are possible")


def plot_asset_purposes(assetlist, fname, titlestr, analyzer):
    """Plots the values of the assets, grouped according to their purposes.
    Furthermore, The asset-type (i.e., account or investment) is differentiated
    Multiple lines are plotted in a single plot
    :param assetlist: List of asset-objects
    :param fname: String for file-storage
    :param titlestr: String of plot-title
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
        return

    # Nr. of different purposes:
    num_purp_tot = len(config.ASSET_PURPOSES)

    # Collect all purposes and compare:
    purplist = []
    for asset in assetlist:
        purplist.append(asset.get_purpose())

    purp_set = set(purplist)

    # If the configured asset-purposes are different from what is recorded from the actual assets: (at least, in length)
    if num_purp_tot < len(purp_set):
        raise RuntimeError("Assets with differing purposes than what ASSET_PURPOSES defines are found. "
                           "This should not happen.")

    # Get colors for the purposes:
    purpcolor = plotting_aux.create_colormap('rainbow', num_purp_tot, invert_colorrange=False)
    typemarker = ['x', 'o']  # Two asset types, two markers

    # Plot:
    plotting_aux.configure_lineplot()
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    # Go through the different purposes and collect the assets:
    for purpidx, purp in enumerate(purp_set):
        # List of all assets with the current purpose:
        assets_cur = [assetlist[i] for i, x in enumerate(purplist) if x == purp]
        # Get the total value of the assets with the current purpose:
        asset_val_tot_cur = analysis.get_asset_values_summed(assets_cur)
        # Plot the total value:
        datelist = assets_cur[0].get_analysis_datelist()
        x = [analyzer.str2datetime(x) for x in datelist]

        # Get the type of these assets (either account or investment)
        # This is used for further distinction
        typelist_cur = [x.get_type() for x in assets_cur]
        type_cur_set = set(typelist_cur)
        # Sanity check:
        if len(type_cur_set) > 2:
            raise RuntimeError("No more than two different asset types can be found: Asset and investment. "
                               "Something's really wrong.")

        if len(type_cur_set) == 1:
            labelstr = purp + " (Type: " + typelist_cur[0] + ")"
        else:
            labelstr = purp + " (Multiple Types as follows)"

        # Plot the total values:
        ax.plot(x, asset_val_tot_cur, alpha=1.0, zorder=3, clip_on=False, color=purpcolor[purpidx], marker='',
                label=labelstr)

        # If the current purpose has value both in accounts and investments: plot both
        if len(type_cur_set) > 1:
            # Collect the value of these assets
            for i, typ in enumerate(type_cur_set):
                assetlist_type = [assets_cur[i] for i, x in enumerate(typelist_cur) if x == typ]

                # Get the total value of the assets with the current purpose and type:
                asset_val_tot_cur = analysis.get_asset_values_summed(assetlist_type)
                # Plot the total value of the current purpose and asset-type:
                datelist = assetlist_type[0].get_analysis_datelist()
                x = [analyzer.str2datetime(x) for x in datelist]
                labelstr = "     Type: " + typ
                if len(x) < 40.0:
                    marker_div = 1
                else:
                    marker_div = int(len(x) / 40.0)
                ax.plot(x, asset_val_tot_cur, alpha=1.0, zorder=3, clip_on=False, color=purpcolor[purpidx],
                        marker=typemarker[i], label=labelstr, markevery=marker_div, dashes=[2, 2])

    plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

    # Add a comma to separate thousands:
    ax.get_yaxis().set_major_formatter(
        pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.set_xlabel("Dates")
    ax.set_ylabel("Values (" + config.BASECURRENCY + ")")
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        plotting_aux.open_plot(fname)


def plot_asset_values_indices(assetlist, indexlist, fname, titlestr, analyzer):
    """Plots the summed values of the given assets, together with some stock-market indices
    :param assetlist: List of asset-objects
    :param indexlist: List of Index-objects that contain the index-data
    :param fname: String of filename of plot
    :param titlestr: String of plot-title
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
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
        print("All summed asset values are zero. Not plotting. File: " + fname)
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
    plotting_aux.configure_lineplot()
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    x = [analyzer.str2datetime(x) for x in datelist]
    ax.plot(x, sumlist_corr, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='',
            label="Asset Value",
            linewidth=1.6)
    # Label the last value:
    last_val = f"{sumlist_corr[-1]:.2f}"
    ax.text(x[-1], sumlist_corr[-1], last_val)
    # Also plot the moving average:
    x_ma, y_ma = analysis.calc_moving_avg(x, sumlist_corr, config.WINLEN_MA)
    ax.plot(x_ma, y_ma, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='',
            label="Asset Value, Moving Avg", dashes=config.DASHES_MA, linewidth=1.6)

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
        # Also plot the moving average:
        x_ma, y_ma = analysis.calc_moving_avg(x, val, config.WINLEN_MA)
        label_ma = indexname[i] + ", Moving Avg"
        ax.plot(x_ma, y_ma, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[i + 1], marker='',
                label=label_ma, dashes=config.DASHES_MA)

    plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='upper left',
               bbox_to_anchor=(0.01, 0.99))

    # Add a comma to separate thousands:
    ax.get_yaxis().set_major_formatter(
        pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.set_xlabel("Dates")
    ax.set_ylabel("Normalized Value")
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        plotting_aux.open_plot(fname)


def plot_asset_projections(assetlist, interest, num_years, fname, titlestr, analyzer):
    """Plots the past summed value of the assets and projects the value into the future, assuming a certain
    interest rate. Compounded growth is assumed.
    :param assetlist: List of asset-objects. Their value will be summed and used for the projection.
    :param interest: yearly interest rate (in percent) used for the projection
    :param num_years: Nr. of years projected into the future.
    :param fname: String of filename of plot
    :param titlestr: String of plot-title
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)
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
    _, vallist_fut_upper = analysis.project_values(datelist, sumlist, num_years, interest * fact_up, config.FORMAT_DATE)
    _, vallist_fut_lower = analysis.project_values(datelist, sumlist, num_years, interest * fact_low,
                                                   config.FORMAT_DATE)

    # Plot:
    plotting_aux.configure_lineplot()
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
    ax.get_yaxis().set_major_formatter(
        pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.set_xlabel("Dates")
    ax.set_ylabel("Values (" + config.BASECURRENCY + ")")
    ax.set_ylim(ymin=0)  # Looks better
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        plotting_aux.open_plot(fname)


def plot_asset_total_absolute_returns_accumulated(dates, returns, fname, analyzer):
    """Plots the accumulated absolute returns
    :param dates: List of dates
    :param returns: List of day-wise, summed returns of all investments
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(returns) == 0:
        print("No assets given for plot: " + fname)
        return

    if len(dates) != len(returns):
        raise RuntimeError("The summed list and date-list must correspond in length.")

    if helper.list_all_zero(returns) is True:
        print(f"All summed asset values are zero. Not plotting. File: {fname.name}")
        return

    # Plot:
    plotting_aux.configure_lineplot()
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    x = [analyzer.str2datetime(x) for x in dates]

    ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='', linewidth=1.6)
    # Label the last value:
    last_val = f"{returns[-1]:.2f}"
    ax.text(x[-1], returns[-1], last_val)

    # Add a comma to separate thousands:
    ax.get_yaxis().set_major_formatter(
        pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.set_xlabel("Dates")
    ax.set_ylabel("Absolute Returns (" + config.BASECURRENCY + ")")
    plt.title(
        "Summed absolute returns of all investments in analysis period")

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        plotting_aux.open_plot(fname)


def plot_assets_returns_total(assetlist, fname, titlestr, analyzer):
    """Plots the returns of all assets combined, for different periods (7, 30, 100 and 365 days)
    :param assetlist: List of asset-objects
    :param fname: String of the desired filename of the plot
    :param titlestr: String of plot-title
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print(f"No assets given for plot: {fname.name}")
        return

    plotting_aux.configure_lineplot()

    dateformat = assetlist[0].get_dateformat()
    if len(assetlist) > 1:
        for asset in assetlist[1:]:
            if asset.get_dateformat() != dateformat:
                raise RuntimeError("The dateformats of the assets must be identical.")

    plotting_aux.configure_lineplot()
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    plotted = False
    dates, returns = analysis.get_returns_assets_accumulated(assetlist, 2, analyzer)
    # Only plot if there is something to plot:
    if helper.list_all_zero(returns) is False:
        x = [analyzer.str2datetime(x) for x in dates]
        ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='o',
                label="2-day return")
        plotted = True

    dates, returns = analysis.get_returns_assets_accumulated(assetlist, 7, analyzer)
    # Only plot if there is something to plot:
    if helper.list_all_zero(returns) is False:
        x = [analyzer.str2datetime(x) for x in dates]
        ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[1], marker='x',
                label="7-day return",
                markersize=5)
        plotted = True

    dates, returns = analysis.get_returns_assets_accumulated(assetlist, 30, analyzer)
    # Only plot if there is something to plot:
    if helper.list_all_zero(returns) is False:
        x = [analyzer.str2datetime(x) for x in dates]
        ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[2], marker='d',
                label="30-day return",
                markersize=4)
        plotted = True

    dates, returns = analysis.get_returns_assets_accumulated(assetlist, 100, analyzer)
    # Only plot if there is something to plot:
    if helper.list_all_zero(returns) is False:
        x = [analyzer.str2datetime(x) for x in dates]
        ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[3], marker='s',
                label="100-day return")
        plotted = True

    dates, returns = analysis.get_returns_assets_accumulated(assetlist, 365, analyzer)
    # Only plot if there is something to plot:
    if helper.list_all_zero(returns) is False:
        x = [analyzer.str2datetime(x) for x in dates]
        ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[4], marker='+',
                label="365-day return",
                markersize=5)
        plotted = True

    if plotted is False:
        print(f"All returns of the given assets are zero for the considered period. Not plotting. File: {fname.name}")
        return

    plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='upper left',
               bbox_to_anchor=(0.01, 0.99))

    ax.set_xlabel("Dates")
    ax.set_ylabel("Returns (%)")
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # Format the y-axis labels
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        plotting_aux.open_plot(fname)


def plot_asset_values_cost_payout_individual(assetlist, fname, analyzer):
    """Plots the values of assets, with and without cost and payouts
    The plots are created on a 2x3 grid
    :param assetlist: List of asset-objects
    :param fname: String for desired filename
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
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
    ylabel = "Value (" + config.BASECURRENCY + ")"

    for sheet_num, assets in enumerate(assetlists_sheet):

        plotting_aux.configure_gridplot()
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
            # Also plot the moving average:
            x_ma, y_ma = analysis.calc_moving_avg(x, values, config.WINLEN_MA)
            ax.plot(x_ma, y_ma, alpha=1.0, zorder=3, clip_on=False, color='k', marker='',
                    label="Asset Value, Moving Avg", dashes=config.DASHES_MA)

            if helper.list_all_zero(payouts_accu) is False:
                values_payouts = helper.sum_lists(values, payouts_accu)
                ax.plot(x, values_payouts, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[1], marker='x',
                        label="Asset Value, with Payouts", markevery=marker_div)
            else:
                values_payouts = list(values)

            # Only plot cost, payouts, if there is actually some cost or payout:
            if helper.list_all_zero(costs_accu) is False:
                values_payouts_cost = helper.diff_lists(values_payouts, costs_accu)
                ax.plot(x, values_payouts_cost, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[2],
                        marker='d', label="Asset Value, with Payouts and Costs", markevery=marker_div)

            plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            assetname = asset.get_filename()
            assetname = files.get_filename(assetname, keep_suffix=False)
            assettype = asset.get_type()
            titlestr = "Values: " + assetname + " (in " + config.BASECURRENCY + ", " + assettype + ")"
            plt.title(titlestr)

            # Add a comma to separate thousands:
            ax.get_yaxis().set_major_formatter(
                pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

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
            plotting_aux.open_plot(fname_ext)


def plot_asset_returns_individual(assetlist, fname, analyzer):
    """Plots different returns of each asset in an individual plot.
    The plots are created on a 2x3 grid
    :param assetlist: List of asset-objects
    :param fname: String of desired plot filename
    """
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
        return

    # Only plot assets with some value during the analysis period:
    assetlist_plot = []
    for asset in assetlist:
        if any(x > 1e-9 for x in asset.get_analysis_valuelist()):
            assetlist_plot.append(asset)

    if len(assetlist_plot) == 0:
        print("No assets of value given at the end of the analysis-period. Not plotting. File: " + fname)
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
    ylabel = "Return (%)"

    for sheet_num, assets in enumerate(assetlists_sheet):

        plotting_aux.configure_gridplot()
        fig = plt.figure()
        fig.subplots_adjust(hspace=0.4, wspace=0.4)

        for idx, asset in enumerate(assets):

            plotidx = idx + 1
            ax = fig.add_subplot(2, 3, plotidx)

            plotted = False
            # Obtain the returns in 7-day periods:
            dates, returns = analysis.get_returns_asset(asset, 7, analyzer)
            if helper.list_all_zero(returns) is False:
                x = [analyzer.str2datetime(i) for i in dates]
                ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='o',
                        label="7-day return")
                plotted = True

            # Obtain the returns in 30-day periods:
            dates, returns = analysis.get_returns_asset(asset, 30, analyzer)
            if helper.list_all_zero(returns) is False:
                x = [analyzer.str2datetime(i) for i in dates]
                ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[1], marker='d',
                        label="30-day return")
                plotted = True

            # Obtain the returns in 365-day periods:
            dates, returns = analysis.get_returns_asset(asset, 365, analyzer)
            if helper.list_all_zero(returns) is False:
                x = [analyzer.str2datetime(i) for i in dates]
                ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[2], marker='x',
                        label="365-day return")
                plotted = True

            # Obtain the asset's return of the whole analysis-period:
            ret_a = analysis.get_returns_asset_analysisperiod(asset, analyzer)
            # Obtain the asset's holding period return:
            ret_h = analysis.get_return_asset_holdingperiod(asset, dateformat)
            # String for displaying in the plot:
            # Check, if the holding period return is irreasonably negative. Then, the holding period return calc. was
            # not possible due to missing price-data of today.
            if ret_h > -1e9:
                ret_str = "Analysis Period Return: {:.2f} %".format(ret_a) + "\n" + \
                          "Holding Period Return: {:.2f} %".format(ret_h)
            else:
                ret_str = "Analysis Period Return: {:.2f} %".format(ret_a) + "\n" + \
                          "Holding Period Return: N/A (missing price of today)"

            # Place the text relative to the axes:
            plt.text(0.05, 0.78, ret_str, horizontalalignment='left', verticalalignment='center',
                     transform=ax.transAxes, fontsize=7, bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'))

            if plotted is False:
                plt.text(0.05, 0.5, "Not enough data for period-wise returns.", horizontalalignment='left',
                         verticalalignment='center',
                         transform=ax.transAxes, fontsize=7, bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'))
            else:
                plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

            # Format the y-axis labels
            ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))

            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            assetname = asset.get_filename()
            assetname = files.get_filename(assetname, keep_suffix=False)
            titlestr = "Return: " + assetname
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
            plotting_aux.open_plot(fname_ext)


def plot_asset_returns_individual_absolute(assetlist, fname, analyzer):
    """Plots different absolute returns of each asset in an individual plot.
    The plots are created on a 2x3 grid
    :param assetlist: List of asset-objects
    :param fname: String of desired plot filename
    """
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
        return [0], [0]

    # Only plot assets with some value during the analysis period:
    assetlist_plot = []
    for asset in assetlist:
        if any(x > 1e-9 for x in asset.get_analysis_valuelist()):
            assetlist_plot.append(asset)

    if len(assetlist_plot) == 0:
        print("No assets of value given at the end of the analysis-period. Not plotting. File: " + fname)
        return [0], [0]

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
    ylabel = "Return (Absolute; Currency)"

    dates = assetlist_plot[0].get_analysis_datelist()
    returns_total = [0.0 for _ in range(len(dates))]

    for sheet_num, assets in enumerate(assetlists_sheet):

        plotting_aux.configure_gridplot()
        fig = plt.figure()
        fig.subplots_adjust(hspace=0.4, wspace=0.4)

        for idx, asset in enumerate(assets):
            plotidx = idx + 1
            ax = fig.add_subplot(2, 3, plotidx)
            try:
                dates, returns = analysis.get_returns_asset_daily_absolute_analysisperiod(asset, dateformat, analyzer)
                returns_total = [a + b for a, b in zip(returns, returns_total)]
                if helper.list_all_zero(returns) is False:
                    x = [analyzer.str2datetime(i) for i in dates]
                    ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=config.PLOTS_COLORS[0], marker='',
                            label="Absolute Returns")
                else:
                    # Skip the plotting; no date of today available.
                    plt.text(0.05, 0.5, "Something went wrong", horizontalalignment='left',
                             verticalalignment='center',
                             transform=ax.transAxes, fontsize=7,
                             bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'))
            except:
                # Skip the plotting; no date of today available.
                plt.text(0.05, 0.5, "Missing price-data of today (or other error)", horizontalalignment='left',
                         verticalalignment='center',
                         transform=ax.transAxes, fontsize=7, bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'))

            # Format the y-axis labels
            ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))

            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            assetname = asset.get_filename()
            assetname = files.get_filename(assetname, keep_suffix=False)
            titlestr = "Abs. Return/Gain: " + assetname
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
            plotting_aux.open_plot(fname_ext)

    return dates, returns_total


def plot_asset_values_stacked(assetlist, fname, title, analyzer):
    """This function plots the values of the given assets with a stacked plot.
    :param assetlist: List of asset-objects
    :param fname: String of desired filename
    :param title: String of plot title
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print(f"No assets given for plot: {fname.name}") # Todo: convert all these fname to fname.name
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

    colorlist = plotting_aux.create_colormap("rainbow", len(ylists), False)

    titlestring = title + ". Currency: " + config.BASECURRENCY
    xlabel = "Date"
    ylabel = "Value (" + config.BASECURRENCY + ")"
    alpha = 0.75  # Plot transparency
    # Plot:
    plotting_aux.create_stackedplot(xlist, ylists, legendlist, colorlist, titlestring, xlabel, ylabel, alpha, fname)
