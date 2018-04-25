"""Auxiliary functions for plotting

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018 Mario Mauerer
"""

import os
import matplotlib
import matplotlib.pyplot as plt
import pylab
import files
import setup
import PROFIT_main as cfg


def configure_plot_common():
    """Set plot-configurations that are common to all plots:
    """
    plt.rcParams['figure.figsize'] = setup.PLOTSIZE
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


def configure_gridplot():
    """Set configuration parameters for stacked plots
    """
    configure_plot_common()
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


def configure_lineplot():
    """Set configuration parameters for stacked plots
    """
    configure_plot_common()
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


def configure_stackedplot():
    """Set configuration parameters for stacked plots
    """
    configure_plot_common()
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


def create_stackedplot(xlist, ylists, legendlist, colorlist, titlestring, xlabel, ylabel, alpha, fname):
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
            raise RuntimeError("Can only create stacked plot with equally sized data. Plot-filename: " + fname)

    configure_stackedplot()

    fig = plt.figure()
    ax = fig.add_subplot(111)

    # The list of lists needs to be re-formatted for matplotlib:
    ylists = [x for x in ylists]

    ax.stackplot(xlist, ylists, alpha=alpha, zorder=1, clip_on=True, baseline="zero", colors=colorlist,
                 labels=legendlist, edgecolor='w', linewidth=1.0)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # Add a comma to separate thousands:
    ax.get_yaxis().set_major_formatter(
        pylab.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plt.title(titlestring)

    plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='upper left', bbox_to_anchor=(0.01, 0.99))

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if cfg.OPEN_PLOTS is True:
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
    :param folder: String of plots-folder, in current directory
    :param file: String of filename
    :return: String of modified path
    """
    fname = files.create_path(folder, file)
    fname = fname + ".pdf"
    return fname


def open_plot(fname):
    """Opens a plot-file (normally a pdf).
    Works on linux and windows.
    :param fname: Path of the file (string)
    """
    # Windows:
    if os.name == "nt":
        os.system("start " + fname)
    # Linux:
    elif os.name == "posix":
        name = "/usr/bin/xdg-open " + fname
        os.system(name)
