"""Function(s) for plotting

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import matplotlib
import matplotlib.pyplot as plt
from . import plotting
from .. import analysis


def plot_forex_rates(forexobjdict, fname, titlestr, analyzer, config):
    """Plot the forex rates.
    The forex-objects are stored in a dictionary, whose keys are the strings of the currencies, e.g., "USD".
    :param forexobjdict: Dictionary with the forex-objects
    :param fname: String of the filename of the plot
    :param titlestr: String of the title of the plot
    """

    # Get the full path of the file:
    fname = plotting.modify_plot_path(config.PLOTS_FOLDER, fname)

    plotting.configure_lineplot(config)
    fig = plt.figure()
    ax = fig.add_subplot(111)  # Only one plot

    colorlist = plotting.create_colormap("rainbow", len(forexobjdict), False)
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
            linelabel = f"{obj.get_currency()} Moving Avg"
            ax.plot(x_ma, y_ma, alpha=1.0, zorder=3, clip_on=False, color=colorlist[i], marker='',
                    label=linelabel, dashes=config.DASHES_MA)
        i += 1

    plt.legend(fancybox=True, shadow=True, ncol=1, framealpha=1.0, loc='best')

    ax.set_xlabel("Dates")
    ax.set_ylabel(f"Exchange Rates with {config.BASECURRENCY}")
    plt.title(titlestr)

    # Nicer date-plotting:
    fig.autofmt_xdate()
    ax.fmt_xdata = matplotlib.dates.DateFormatter('%d.%m.%Y')

    # PDF Export:
    plt.savefig(fname)

    if config.OPEN_PLOTS is True:
        plotting.open_plot(fname)
