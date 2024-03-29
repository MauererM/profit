"""Classes and functions for plotting

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import os
import matplotlib
import matplotlib.pyplot as plt
import pylab
from .. import files


class PlottingConfig:
    """The following strings name the files of the different plots that will be generated.
    Do not provide the file-extension; PDF files will be created.
    The plots are stored in the "plots" folder
    """
    # Values of all assets, stacked:
    FILENAME_STACKPLOT_ASSET_VALUES = "Asset_Values_Stacked"
    # Values of all investments, stacked:
    FILENAME_STACKPLOT_INVESTMENT_VALUES = "Investment_Values_Stacked"
    # Values of all accounts, stacked:
    FILENAME_STACKPLOT_ACCOUNT_VALUES = "Account_Values_Stacked"
    # Absolute returns of individual investments, multiple plots per sheet:
    FILENAME_INVESTMENT_RETURNS_ABSOLUTE = "Investments_Returns_Absolute"
    # Absolute returns of all investments, summed up:
    FILENAME_INVESTMENT_RETURNS_ABSOLUTE_TOTAL = "Investments_Returns_Absolute_Summed"
    # Values of individual investments, multiple plots per sheet:
    FILENAME_INVESTMENT_VALUES = "Investments_Values"
    # Values of individual accounts, multiple plots per sheet:
    FILENAME_ACCOUNT_VALUES = "Accounts_Values"
    # Value of all investments, compared to some indices:
    FILENAME_INVESTMENT_VALUES_INDICES = "Investment_Values_Indices"
    # Value of all assets, sorted according to their purpose:
    FILENAME_ASSETS_VALUES_PURPOSE = "Assets_Values_Purpose"
    # Value of the groups of assets (see below for groups), two plots are done; one line, one stacked
    FILENAME_ASSETS_VALUES_GROUPS_STACKED = "Assets_Values_Groups_Stacked"
    FILENAME_ASSETS_VALUES_GROUPS_LINE = "Assets_Values_Groups_Line"
    # Forex rates:
    FILENAME_FOREX_RATES = "Forex_Rates"
    # Plots of the groups (can be multiple plots), will be extended with the corresponding group name.
    FILENAME_PLOT_GROUP = "Group"
    # Plots of asset values according to currency:
    FILENAME_CURRENCIES_STACKED = "Asset_Values_Currencies_Stacked"
    FILENAME_CURRENCIES_LINE = "Asset_Values_Currencies_Line"
    # Projected investment values:
    FILENAME_INVESTMENT_PROJECTIONS = "Investments_Values_Projected"


def configure_plot_common(config):
    """Set plot-configurations that are common to all plots:
    """
    plt.rcParams['figure.figsize'] = config.PLOTSIZE
    plt.rcParams['figure.autolayout'] = True
    plt.rcParams['font.weight'] = 'medium'
    plt.rcParams['text.usetex'] = False  # Don't use Latex
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['legend.labelspacing'] = 0.5  # vertical space between the legend entries in fraction of fontsize
    plt.rcParams['legend.handletextpad'] = 0.6  # space between the legend line and legend text in fraction of fontsize
    plt.rcParams['legend.numpoints'] = 1  # the number of points in the legend line
    plt.rcParams['legend.borderpad'] = 0.25  # border whitespace in fontsize units
    plt.rcParams['legend.borderaxespad'] = 0.75  # Border between legend and axes
    plt.rcParams['legend.columnspacing'] = 0.75  # Spacing between legend columns
    plt.rcParams['axes.labelweight'] = 'medium'
    plt.rcParams['axes.linewidth'] = 0.5  # line width of axes
    plt.rcParams['axes.axisbelow'] = True  # Axis/grids behind the data points/lines
    plt.rcParams['axes.grid'] = True  # Enable/Disable grid.
    plt.rcParams['grid.color'] = "#cfcfcf"
    plt.rcParams['grid.linestyle'] = '-'
    plt.rcParams['grid.linewidth'] = 0.4
    plt.rcParams['xtick.major.size'] = 4  # major tick size in points
    plt.rcParams['ytick.major.size'] = 4  # major tick size in points
    plt.rcParams['xtick.minor.size'] = 2  # minor tick size in points
    plt.rcParams['ytick.minor.size'] = 2  # minor tick size in points
    plt.rcParams['xtick.minor.width'] = 0.5  # major tick width in points
    plt.rcParams['ytick.minor.width'] = 0.5  # major tick width in points
    plt.rcParams['xtick.major.pad'] = 4  # distance of labels(numbers) to major tick label in points
    plt.rcParams['xtick.minor.pad'] = 4  # distance of labels(numbers) to major tick label in points
    plt.rcParams['ytick.major.pad'] = 3  # distance of labels(numbers) to major tick label in points
    plt.rcParams['ytick.minor.pad'] = 3  # distance of labels(numbers) to major tick label in points


def configure_gridplot(config):
    """Set configuration parameters for stacked plots
    """
    configure_plot_common(config)
    plt.rcParams['font.size'] = 8.0  # Font size in points
    plt.rcParams['lines.linewidth'] = 0.8  # Line width in points
    plt.rcParams['lines.markeredgewidth'] = 0.2  # line width around the marker symbol
    plt.rcParams['lines.markersize'] = 4  # markersize, in points
    plt.rcParams['legend.handlelength'] = 2.5  # length of the legend lines in fraction of fontsize
    plt.rcParams['legend.fontsize'] = 6.0
    plt.rcParams['legend.markerscale'] = 1  # the relative size of legend markers vs. original
    plt.rcParams['axes.titlesize'] = 8.0  # fontsize of axes title
    plt.rcParams['axes.labelsize'] = 8.0  # fontsize of axes labels
    plt.rcParams['xtick.labelsize'] = 6.0  # fontsize of the tick labels
    plt.rcParams['ytick.labelsize'] = 6.0
    plt.rcParams['figure.max_open_warning'] = 100  # Override a warning generation


def configure_lineplot(config):
    """Set configuration parameters for stacked plots
    """
    configure_plot_common(config)
    plt.rcParams['font.size'] = 10.0  # Font size in points
    plt.rcParams['lines.linewidth'] = 0.8  # Line width in points
    plt.rcParams['lines.markeredgewidth'] = 0.5  # line width around the marker symbol
    plt.rcParams['lines.markersize'] = 4  # markersize, in points
    plt.rcParams['legend.handlelength'] = 3  # length of the legend lines in fraction of fontsize
    plt.rcParams['legend.fontsize'] = 8.0
    plt.rcParams['legend.markerscale'] = 1  # the relative size of legend markers vs. original
    plt.rcParams['axes.titlesize'] = 14.0  # fontsize of axes title
    plt.rcParams['axes.labelsize'] = 14.0  # fontsize of axes labels
    plt.rcParams['xtick.labelsize'] = 10.0  # fontsize of the tick labels
    plt.rcParams['ytick.labelsize'] = 10.0


def configure_stackedplot(config):
    """Set configuration parameters for stacked plots
    """
    configure_plot_common(config)
    plt.rcParams['font.size'] = 10.0  # Font size in points
    plt.rcParams['lines.linewidth'] = 0.5  # Line width in points
    plt.rcParams['lines.markeredgewidth'] = 0.5  # line width around the marker symbol
    plt.rcParams['lines.markersize'] = 3  # markersize, in points
    plt.rcParams['legend.handlelength'] = 1.5  # length of the legend lines in fraction of fontsize
    plt.rcParams['legend.fontsize'] = 8.0
    plt.rcParams['legend.markerscale'] = 1  # the relative size of legend markers vs. original
    plt.rcParams['axes.titlesize'] = 14.0  # fontsize of axes title
    plt.rcParams['axes.labelsize'] = 14.0  # fontsize of axes labels
    plt.rcParams['xtick.labelsize'] = 10.0  # fontsize of the tick labels
    plt.rcParams['ytick.labelsize'] = 10.0


def create_stackedplot(xlist, ylists, legendlist, colorlist, titlestring, xlabel, ylabel, alpha, fname, config):
    """Create a stacked-plot
    :param xlist: List of x-values
    :param ylists: List of lists for y-values
    :param legendlist: List of strings for labelling
    :param colorlist: List of colors
    :param titlestring: String for title
    :param xlabel: String for x-axis label
    :param ylabel: String for y-axis label
    :param alpha: Alpha of fills (transparency, 0...1)
    :param fname: Filename of plot
    """
    # Sanity-Check:
    for y in ylists:
        if len(xlist) != len(y):
            raise RuntimeError(f"Can only create stacked plot with equally sized data. Plot-filename: {fname}")

    configure_stackedplot(config)

    fig = plt.figure()
    ax = fig.add_subplot(111)

    # Sort the y-values according to the most recent value:
    sortlist = [x[-1] for x in ylists]
    sortedidx = sorted(range(len(sortlist)), key=lambda x: sortlist[x])
    sortedidx.reverse()
    # Sort the lists:
    ylists = [ylists[i] for i in sortedidx]
    legendlist = [legendlist[i] for i in sortedidx]

    # The list of lists needs to be re-formatted for matplotlib:
    ylists = list(ylists)

    ax.stackplot(xlist, ylists, alpha=alpha, zorder=1, clip_on=True, baseline="zero", colors=colorlist,
                 labels=legendlist, edgecolor='w', linewidth=1.0)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # Add a comma to separate thousands:
    ax.get_yaxis().set_major_formatter(pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plt.title(titlestring)

    # Revert the order of the legend entries, such that they correspond to the position in the stacked plot:
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles[::-1], labels[::-1], fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='upper left',
               bbox_to_anchor=(0.01, 0.99))

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        open_plot(fname)


def create_colormap(mapname, num_colors, invert_colorrange):
    """Create a list of colors
    :param mapname: String of desired color-range, e.g., "rainbow"
    :param num_colors: Number of desired colors
    :param invert_colorrange: Bool, if color-range is inverted or not
    :return: List of strings of colors
    """
    cmap = pylab.cm.get_cmap(mapname, num_colors)  # https://matplotlib.org/examples/color/colormaps_reference.html
    cmap_range = range(0, num_colors)
    colors = []
    for i in cmap_range:
        if invert_colorrange is False:
            rgb = cmap(i)[:3]  # will return rgba, we take only first 3 so we get rgb
            # print(matplotlib.colors.rgb2hex(rgb))
            colors.append(pylab.matplotlib.colors.rgb2hex(rgb))
        else:
            rgb = cmap(num_colors - i)[:3]  # will return rgba, we take only first 3 so we get rgb
            # print(matplotlib.colors.rgb2hex(rgb))
            colors.append(pylab.matplotlib.colors.rgb2hex(rgb))
    return colors


def modify_plot_path(folder, file):
    """Modifies the path of a plot-file.
    It attaches the plots-folder and the extension (.pdf)
    :param folder: String or Path-object of folder-path
    :param file: Filename, string or Path-Object
    :return: Path-object of amended path
    """
    pname = files.create_path(folder, file)
    return files.filename_add_extension(pname, ".pdf")


def open_plot(fname):
    """Opens a plot-file (normally a pdf).
    Works on linux and windows.
    :param fname: Path of the file (string)
    """
    # Windows:
    if os.name == "nt":
        os.system(f"start {fname}")
    # Linux:
    elif os.name == "posix":
        name = f"/usr/bin/xdg-open {fname}"
        os.system(name)
