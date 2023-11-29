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


def plot_asset_purposes(assetlist, fname, titlestr, analyzer, config):
    """Plots the values of the assets, grouped according to their purposes.
    Furthermore, The asset-type (i.e., account or investment) is differentiated
    Multiple lines are plotted in a single plot
    :param assetlist: List of asset-objects
    :param fname: String for file-storage
    :param titlestr: String of plot-title
    """
    # Get the full path of the file:
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)
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
    purpcolor = plotting.create_colormap('rainbow', num_purp_tot, invert_colorrange=False)
    typemarker = ['x', 'o']  # Two asset types, two markers

    # Plot:
    plotting.configure_lineplot(config)
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
            labelstr = f"{purp} (Type: {typelist_cur[0]})"
        else:
            labelstr = f"{purp} (Multiple Types as follows)"

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
                labelstr = f"     Type: {typ}"
                if len(x) < 40.0:
                    marker_div = 1
                else:
                    marker_div = int(len(x) / 40.0)
                ax.plot(x, asset_val_tot_cur, alpha=1.0, zorder=3, clip_on=False, color=purpcolor[purpidx],
                        marker=typemarker[i], label=labelstr, markevery=marker_div, dashes=[2, 2])

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
