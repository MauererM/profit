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


def plot_assets_grouped(assetlist, fname, titlestr, plottype, analyzer, config):
    """Plots the values of the assets, grouped according to their groups (see main-file)
    A stacked plot is used.
    :param assetlist: List of asset-objects
    :param fname: String of desired file-name for the plot
    :param titlestr: String of the plot's title
    :param plottype: String, either "line" or "stacked"; for the type of plot.
    :return:
    """
    # Get the full path of the file:
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)
    # Sanity check:
    if len(assetlist) == 0:
        print(f"No assets given for plot: {fname}")
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

    colorlist = plotting.create_colormap("rainbow", len(vals_groups), False)

    xlabel = "Date"
    ylabel = f"Value ({config.BASECURRENCY})"
    alpha = 0.75  # Plot transparency

    # Plot:
    if plottype == "stacked":
        plotting.configure_stackedplot(config)
        plotting.create_stackedplot(xlist, vals_groups, labels_groups, colorlist, titlestr, xlabel, ylabel, alpha,
                                    fname, config)
    elif plottype == "line":
        plotting.configure_lineplot(config)
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
        ax.get_yaxis().set_major_formatter(pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        ax.set_xlabel("Dates")
        ax.set_ylabel(f"Values ({config.BASECURRENCY})")
        plt.title(titlestr)

        # Nicer date-plotting:
        fig.autofmt_xdate()
        ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

        # PDF Export:
        plt.savefig(fname)

        if config.OPEN_PLOTS is True:
            plotting.open_plot(fname)

    else:
        raise RuntimeError("Unknown plottype. Only 'stacked' or 'line' are possible")
