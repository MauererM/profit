"""Functions for plotting assets
This file is quite long, as some plotting methods require some specific handling of data

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import matplotlib.dates as mdates
import pylab
import PROFIT_main as cfg
import stringoperations
import analysis
import setup
import plotting_aux
import helper


def plot_asset_groups(assets, grouplist, groupnames, fname, titlestring):
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
    fname = plotting_aux.modify_plot_path(setup.PLOTS_FOLDER, fname)

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
        xlist = [stringoperations.str2datetime(x, setup.FORMAT_DATE) for x in datelist]

        # This holds the total value of the group:
        totsum = [0] * len(datelist)

        # Get the values of each purpose, from all assets:
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

        # Plot the total sum of the group (only, if there are multiple constituents in a group)
        if len(purposelist) > 1:
            totlabel = "Total Group Value of " + groupnames[purpidx]
            ax.plot(xlist, totsum, alpha=1.0, zorder=3, clip_on=False, color=colorlist[len(purposelist)], marker='',
                    label=totlabel)

        plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

        ax.set_xlabel("Dates")
        ax.set_ylabel("Value " + "(" + cfg.BASECURRENCY + ")")
        titlestr_mod = titlestring + ". Group: " + groupnames[purpidx]
        plt.title(titlestr_mod)

        # Nicer date-plotting:
        fig.autofmt_xdate()
        ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

        # Modify the file name: add the name of the group:
        fname_cur = stringoperations.filename_append_string(fname, "_", groupnames[purpidx])

        # PDF Export:
        plt.savefig(fname_cur)

        if cfg.OPEN_PLOTS is True:
            plotting_aux.open_plot(fname)


def plot_forex_rates(forexobjdict, fname, titlestr):
    """Plot the forex rates.
    The forex-objects are stored in a dictionary, whose keys are the strings of the currencies, e.g., "USD".
    :param forexobjdict: Dictionary with the forex-objects
    :param fname: String of the filename of the plot
    :param titlestr: String of the title of the plot
    """

    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(setup.PLOTS_FOLDER, fname)

    plotting_aux.configure_lineplot()
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    colorlist = plotting_aux.create_colormap("rainbow", len(forexobjdict), False)
    i = 0
    # Iterate through the dictionary, only plot foreign currencies:
    for key, obj in forexobjdict.items():
        # Only plot foreign rates:
        if key != cfg.BASECURRENCY:
            date, rate = obj.get_dates_rates()
            xlist = [stringoperations.str2datetime(x, setup.FORMAT_DATE) for x in date]
            ax.plot(xlist, rate, alpha=1.0, zorder=3, clip_on=False, color=colorlist[i], marker='',
                    label=obj.get_currency())
            # Also plot the moving average:
            x_ma, y_ma = analysis.calc_moving_avg(xlist, rate, cfg.WINLEN_MA)
            linelabel = obj.get_currency() + ", Moving Avg"
            ax.plot(x_ma, y_ma, alpha=1.0, zorder=3, clip_on=False, color=colorlist[i], marker='',
                    label=linelabel, dashes=setup.DASHES_MA)
        i += 1

    plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

    ax.set_xlabel("Dates")
    ax.set_ylabel("Exchange Rates with " + cfg.BASECURRENCY)
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if cfg.OPEN_PLOTS is True:
        plotting_aux.open_plot(fname)


def plot_assets_grouped(assetlist, fname, titlestr, plottype):
    """Plots the values of the assets, grouped according to their groups (see main-file)
    A stacked plot is used.
    :param assetlist: List of asset-objects
    :param fname: String of desired file-name for the plot
    :param titlestr: String of the plot's title
    :param plottype: String, either "line" or "stacked"; for the type of plot.
    :return:
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(setup.PLOTS_FOLDER, fname)
    # Sanity check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
        return

    if len(cfg.ASSET_GROUPNAMES) != len(cfg.ASSET_GROUPS):
        raise RuntimeError("The length of the asset-groups-list must be equal to the length of the list of the "
                           "asset-group names.")

    # Collect all asset purposes:
    purplist = []
    for asset in assetlist:
        purplist.append(asset.get_purpose())

    # If the configured asset-purposes are different from what is recorded from the actual assets: (at least, in length)
    purp_set = set(purplist)
    if len(cfg.ASSET_PURPOSES) < len(purp_set):
        raise RuntimeError("Assets with differing purposes than what ASSET_PURPOSES defines are found. "
                           "This should not happen.")

    vals_groups = []
    labels_groups = []
    # Collect the assets of a group and sum up their value
    for idx, group in enumerate(cfg.ASSET_GROUPS):
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
            labels_groups.append(cfg.ASSET_GROUPNAMES[idx])

    # Create a stacked plot:
    xlist = assetlist[0].get_analysis_datelist()
    dateformat = assetlist[0].get_dateformat()
    xlist = [stringoperations.str2datetime(x, dateformat) for x in xlist]

    colorlist = plotting_aux.create_colormap("rainbow", len(vals_groups), False)

    xlabel = "Date"
    ylabel = "Value (" + cfg.BASECURRENCY + ")"
    alpha = 0.75  # Plot transparency

    # Plot:
    if plottype is "stacked":
        plotting_aux.configure_stackedplot()
        plotting_aux.create_stackedplot(xlist, vals_groups, labels_groups, colorlist, titlestr, xlabel, ylabel, alpha,
                                        fname)
    elif plottype is "line":
        plotting_aux.configure_lineplot()
        fig = plt.figure()
        ax = fig.add_subplot(111)  # Only one plot

        for idx, val in enumerate(vals_groups):
            if idx > len(setup.PLOTS_COLORS) - 1:
                raise RuntimeError("Not enough colors in PLOTS_COLORS (in config-file) given...")
            ax.plot(xlist, val, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[idx], marker='',
                    label=labels_groups[idx])

        plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

        # Add a comma to separate thousands:
        ax.get_yaxis().set_major_formatter(
            pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        ax.set_xlabel("Dates")
        ax.set_ylabel("Values (" + cfg.BASECURRENCY + ")")
        plt.title(titlestr)

        # Nicer date-plotting:
        fig.autofmt_xdate()
        ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

        # PDF Export:
        plt.savefig(fname)

        if cfg.OPEN_PLOTS is True:
            plotting_aux.open_plot(fname)

    else:
        raise RuntimeError("Unknown plottype. Only 'stacked' or 'line' are possible")


def plot_asset_purposes(assetlist, fname, titlestr):
    """Plots the values of the assets, grouped according to their purposes.
    Furthermore, The asset-type (i.e., account or investment) is differentiated
    Multiple lines are plotted in a single plot
    :param assetlist: List of asset-objects
    :param fname: String for file-storage
    :param titlestr: String of plot-title
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(setup.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
        return

    # Nr. of different purposes:
    num_purp_tot = len(cfg.ASSET_PURPOSES)

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
        dateformat = assets_cur[0].get_dateformat()
        x = [stringoperations.str2datetime(x, dateformat) for x in datelist]

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
                dateformat = assets_cur[0].get_dateformat()
                x = [stringoperations.str2datetime(x, dateformat) for x in datelist]
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
    ax.set_ylabel("Values (" + cfg.BASECURRENCY + ")")
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if cfg.OPEN_PLOTS is True:
        plotting_aux.open_plot(fname)


def plot_asset_values_indices(assetlist, indexlist, fname, titlestr):
    """Plots the summed values of the given assets, together with some stock-market indices
    :param assetlist: List of asset-objects
    :param indexlist: List of MarketPrices-objects that contain the index-data
    :param fname: String of filename of plot
    :param titlestr: String of plot-title
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(setup.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
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

    # Obtain stock-market indices:
    indexvals = []  # List of lists
    indexname = []
    for stockidx in indexlist:
        # Check if the object actually contains data:
        if stockidx.is_price_avail() is True:
            dat = stockidx.get_price_values()
            if len(dat) != len(datelist):
                raise RuntimeError("The stockmarket-index-data must be of equal length than the asset values.")
            indexvals.append(dat)
            indexname.append(stockidx.get_currency())  # The name of the index is stored as currency

    # The index-values have to be rescaled to the asset-values (at the beginning of the analysis-period)
    # Find the first (summed) asset-value > 0:
    startidx = [i for i, x in enumerate(sumlist) if x > 1e-9][0]
    indexvals_rs = []
    for vals in indexvals:
        fact = vals[startidx] / sumlist[startidx]
        indexvals_rs.append([x / fact for x in vals])

    # Plot:
    plotting_aux.configure_lineplot()
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    dateformat = assetlist[0].get_dateformat()
    x = [stringoperations.str2datetime(x, dateformat) for x in datelist]
    ax.plot(x, sumlist, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[0], marker='', label="Asset Value",
            linewidth=1.6)
    # Also plot the moving average:
    x_ma, y_ma = analysis.calc_moving_avg(x, sumlist, cfg.WINLEN_MA)
    ax.plot(x_ma, y_ma, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[0], marker='',
            label="Asset Value, Moving Avg", dashes=setup.DASHES_MA, linewidth=1.6)

    # Plot the indexes:
    # Obtain some colors for the indexes:
    # colors = create_colormap('rainbow', len(indexvals_rs), invert_colorrange=False)
    for i, val in enumerate(indexvals_rs):
        if i > len(setup.PLOTS_COLORS) - 1:
            raise RuntimeError("Ran out of colors. Supply more in PLOTS_COLORS (configuration-file)")
        ax.plot(x, val, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[i + 1], marker='',
                label=indexname[i])
        # Also plot the moving average:
        x_ma, y_ma = analysis.calc_moving_avg(x, val, cfg.WINLEN_MA)
        label_ma = indexname[i] + ", Moving Avg"
        ax.plot(x_ma, y_ma, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[i + 1], marker='',
                label=label_ma, dashes=setup.DASHES_MA)

    plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='upper left',
               bbox_to_anchor=(0.01, 0.99))

    # Add a comma to separate thousands:
    ax.get_yaxis().set_major_formatter(
        pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.set_xlabel("Dates")
    ax.set_ylabel("Values (" + cfg.BASECURRENCY + ")")
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if cfg.OPEN_PLOTS is True:
        plotting_aux.open_plot(fname)


def plot_assets_returns_total(assetlist, fname, titlestr):
    """Plots the returns of all assets combined, for different periods (7, 30, 100 and 365 days)
    :param assetlist: List of asset-objects
    :param fname: String of the desired filename of the plot
    :param titlestr: String of plot-title
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(setup.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
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
    dates, returns = analysis.get_returns_assets_accumulated(assetlist, 2, setup.FORMAT_DATE)
    # Only plot if there is something to plot:
    if helper.list_all_zero(returns) is False:
        x = [stringoperations.str2datetime(x, dateformat) for x in dates]
        ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[0], marker='o',
                label="2-day return")
        plotted = True

    dates, returns = analysis.get_returns_assets_accumulated(assetlist, 7, setup.FORMAT_DATE)
    # Only plot if there is something to plot:
    if helper.list_all_zero(returns) is False:
        x = [stringoperations.str2datetime(x, dateformat) for x in dates]
        ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[1], marker='x',
                label="7-day return",
                markersize=5)
        plotted = True

    dates, returns = analysis.get_returns_assets_accumulated(assetlist, 30, setup.FORMAT_DATE)
    # Only plot if there is something to plot:
    if helper.list_all_zero(returns) is False:
        x = [stringoperations.str2datetime(x, dateformat) for x in dates]
        ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[2], marker='d',
                label="30-day return",
                markersize=4)
        plotted = True

    dates, returns = analysis.get_returns_assets_accumulated(assetlist, 100, setup.FORMAT_DATE)
    # Only plot if there is something to plot:
    if helper.list_all_zero(returns) is False:
        x = [stringoperations.str2datetime(x, dateformat) for x in dates]
        ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[3], marker='s',
                label="100-day return")
        plotted = True

    dates, returns = analysis.get_returns_assets_accumulated(assetlist, 365, setup.FORMAT_DATE)
    # Only plot if there is something to plot:
    if helper.list_all_zero(returns) is False:
        x = [stringoperations.str2datetime(x, dateformat) for x in dates]
        ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[4], marker='+',
                label="365-day return",
                markersize=5)
        plotted = True

    if plotted is False:
        print("All returns of the given assets are zero for the considered period. Not plotting. File: " + fname)
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

    if cfg.OPEN_PLOTS is True:
        plotting_aux.open_plot(fname)


def plot_asset_values_cost_payout_individual(assetlist, fname):
    """Plots the values of assets, with and without cost and payouts
    The plots are created on a 2x3 grid
    :param assetlist: List of asset-objects
    :param fname: String for desired filename
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(setup.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
        return

    # Only plot assets with a value > 0 in the last analysis-data-values:
    assetlist_plot = []
    for asset in assetlist:
        if asset.get_analysis_valuelist()[-1] > 1e-9:
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
    print("Plotting the asset-values with {:d} figure-sheet(s). Filename: ".format(num_sheets) + fname)

    xlabel = "Date"
    ylabel = "Value (" + cfg.BASECURRENCY + ")"

    for sheet_num, assets in enumerate(assetlists_sheet):

        plotting_aux.configure_gridplot()
        fig = plt.figure()
        fig.subplots_adjust(hspace=0.4, wspace=0.4)
        for idx, asset in enumerate(assets):
            plotidx = idx + 1
            ax = fig.add_subplot(2, 3, plotidx)

            # Obtain the returns in 7-day periods:
            dates = asset.get_analysis_datelist()
            values = asset.get_analysis_valuelist()
            costs = asset.get_analysis_costlist()
            payouts = asset.get_analysis_payoutlist()
            costs_accu = helper.accumulate_list(costs)
            payouts_accu = helper.accumulate_list(payouts)
            # Datetime for matplotlib:
            x = [stringoperations.str2datetime(i, dateformat) for i in dates]
            # Don't plot too many markers:
            if len(dates) < 40.0:
                marker_div = 1
            else:
                marker_div = int(len(dates) / 40.0)

            # Plot the asset's total value:
            ax.plot(x, values, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[0], marker='o',
                    label="Asset Value",
                    markevery=marker_div)
            # Also plot the moving average:
            x_ma, y_ma = analysis.calc_moving_avg(x, values, cfg.WINLEN_MA)
            ax.plot(x_ma, y_ma, alpha=1.0, zorder=3, clip_on=False, color='k', marker='',
                    label="Asset Value, Moving Avg", dashes=setup.DASHES_MA)

            if helper.list_all_zero(payouts_accu) is False:
                values_payouts = helper.sum_lists(values, payouts_accu)
                ax.plot(x, values_payouts, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[1], marker='x',
                        label="Asset Value, with Payouts", markevery=marker_div)
            else:
                values_payouts = list(values)

            # Only plot cost, payouts, if there is actually some cost or payout:
            if helper.list_all_zero(costs_accu) is False:
                values_payouts_cost = helper.diff_lists(values_payouts, costs_accu)
                ax.plot(x, values_payouts_cost, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[2],
                        marker='d', label="Asset Value, with Payouts and Costs", markevery=marker_div)

            plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            assetname = asset.get_filename()
            assetname = stringoperations.get_filename(assetname, keep_type=False)
            assettype = asset.get_type()
            titlestr = "Values: " + assetname + " (" + cfg.BASECURRENCY + ", " + assettype + ")"
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

        fname_ext = stringoperations.filename_append_number(fname, "_", sheet_num + 1)

        # PDF Export:
        plt.savefig(fname_ext)

        if cfg.OPEN_PLOTS is True:
            plotting_aux.open_plot(fname_ext)


def plot_asset_returns_individual(assetlist, fname):
    """Plots different returns of each asset in an individual plot.
    The plots are created on a 2x3 grid
    :param assetlist: List of asset-objects
    :param fname: String of desired plot filename
    """
    fname = plotting_aux.modify_plot_path(setup.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
        return

    # Only plot assets with a value > 0 in the last analysis-data-values:
    assetlist_plot = []
    for asset in assetlist:
        if asset.get_analysis_valuelist()[-1] > 1e-9:
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
    print("Plotting the asset-values with {:d} figure-sheet(s). Filename: ".format(num_sheets) + fname)

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
            dates, returns = analysis.get_returns_asset(asset, 7, dateformat)
            if helper.list_all_zero(returns) is False:
                x = [stringoperations.str2datetime(i, dateformat) for i in dates]
                ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[0], marker='o',
                        label="7-day return")
                plotted = True

            # Obtain the returns in 30-day periods:
            dates, returns = analysis.get_returns_asset(asset, 30, dateformat)
            if helper.list_all_zero(returns) is False:
                x = [stringoperations.str2datetime(i, dateformat) for i in dates]
                ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[1], marker='d',
                        label="30-day return")
                plotted = True

            # Obtain the returns in 365-day periods:
            dates, returns = analysis.get_returns_asset(asset, 365, dateformat)
            if helper.list_all_zero(returns) is False:
                x = [stringoperations.str2datetime(i, dateformat) for i in dates]
                ax.plot(x, returns, alpha=1.0, zorder=3, clip_on=False, color=setup.PLOTS_COLORS[2], marker='x',
                        label="365-day return")
                plotted = True

            # Obtain the asset's return of the whole analysis-period:
            ret_a = analysis.get_returns_asset_analysisperiod(asset, dateformat)
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
            assetname = stringoperations.get_filename(assetname, keep_type=False)
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

        fname_ext = stringoperations.filename_append_number(fname, "_", sheet_num + 1)

        # PDF Export:
        plt.savefig(fname_ext)

        if cfg.OPEN_PLOTS is True:
            plotting_aux.open_plot(fname_ext)


def plot_asset_values_stacked(assetlist, fname, title):
    """This function plots the values of the given assets with a stacked plot.
    :param assetlist: List of asset-objects
    :param fname: String of desired filename
    :param title: String of plot title
    """
    # Get the full path of the file:
    fname = plotting_aux.modify_plot_path(setup.PLOTS_FOLDER, fname)
    # Sanity Check:
    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
        return

    if len(assetlist) == 0:
        print("No assets given for plot: " + fname)
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
    xlist = assets_plt[0].get_analysis_datelist()
    # Matplotlib takes a datetime-list:
    xlist = [stringoperations.str2datetime(x, dateformat) for x in xlist]
    # Generate a list of the lists of values
    ylists = []
    legendlist = []
    for asset in assets_plt:
        ylists.append(asset.get_analysis_valuelist())
        legendlist.append(asset.get_filename())

    colorlist = plotting_aux.create_colormap("rainbow", len(ylists), False)

    titlestring = title + ". Currency: " + cfg.BASECURRENCY
    xlabel = "Date"
    ylabel = "Value (" + cfg.BASECURRENCY + ")"
    alpha = 0.75  # Plot transparency
    # Plot:
    plotting_aux.create_stackedplot(xlist, ylists, legendlist, colorlist, titlestring, xlabel, ylabel, alpha, fname)
