"""Function(s) for plotting

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import matplotlib
import matplotlib.pyplot as plt
from . import plotting
from .. import stringoperations
from .. import helper
from .. import files


def plot_asset_groups(assets, grouplist, groupnames, fname, titlestring, analyzer, config):
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
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)

    # Strip white spaces of group names, for better plotting/file names:
    groupnames = [stringoperations.strip_whitespaces(x) for x in groupnames]

    # Collect the purposes of all available assets:
    asset_purposes = [asset.get_purpose() for asset in assets]

    # Iterate through all the groups (which collects different purposes)
    for purpidx, purposelist in enumerate(grouplist):

        # One plot per group:
        plotting.configure_lineplot(config)
        fig = plt.figure()
        ax = fig.add_subplot(111)

        colorlist = plotting.create_colormap("rainbow", len(purposelist) + 1, False)

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
            totlabel = f"Total Group Value of {groupnames[purpidx]}"
            ax.plot(xlist, totsum, alpha=1.0, zorder=3, clip_on=False, color=colorlist[len(purposelist)], marker='',
                    label=totlabel)
            # Label the last value:
            last_val = f"{totsum[-1]:.2f}"
            ax.text(xlist[-1], totsum[-1], last_val)

        # Only plot if there is actually a value in a group:
        if plotted is True:
            plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

            ax.set_xlabel("Dates")
            ax.set_ylabel(f"Value ({config.BASECURRENCY})")
            titlestr_mod = f"{titlestring}. Group: {groupnames[purpidx]}"
            plt.title(titlestr_mod)

            # Nicer date-plotting:
            fig.autofmt_xdate()
            ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

            # Modify the file name: add the name of the group:
            fname_cur = files.filename_append_string(fname, "_", groupnames[purpidx])

            # PDF Export:
            plt.savefig(fname_cur)

            if config.OPEN_PLOTS is True:
                plotting.open_plot(fname_cur)
