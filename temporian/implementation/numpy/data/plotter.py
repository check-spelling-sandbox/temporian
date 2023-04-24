from typing import NamedTuple, Optional, Union, List, Any

from click import option
from temporian.implementation.numpy.data.event import NumpyEvent
from temporian.core.data import duration
import datetime

import numpy as np

DEFAULT_BACKEND = "matplotlib"


class Options(NamedTuple):
    """Options for plotting."""

    backend: str
    height_per_plot_px: int
    width_px: int
    max_points: Optional[int]
    min_time: Optional[duration.Timestamp]
    max_time: Optional[duration.Timestamp]
    max_num_plots: int


def plot(
    events: Union[List[NumpyEvent], NumpyEvent],
    indexes: Optional[Union[tuple, List[tuple]]] = None,
    backend: str = DEFAULT_BACKEND,
    width_px: int = 1024,
    height_per_plot_px: int = 150,
    max_points: Optional[int] = None,
    min_time: Optional[duration.Timestamp] = None,
    max_time: Optional[duration.Timestamp] = None,
    max_num_plots: int = 20,
):
    """Plots an event.

    Args:
        events: Single event, or list of events, to plot.
        indexes: The index of the event to plot. Use 'event.index' for the
            list of available indices. If index=None, plots all the indexes.
        backend: Plotting library to use.
        width_px: Width of the figure in pixel.
        height_per_plot_px: Height of each sub-plot (one per feature) in pixel.
        max_points: Maximum number of points to plot.
        min_time: If set, only plot events after min_time.
        max_time: If set, only plot events before min_time.
        max_num_plots: Maximum number of plots to display. If more plots are
          available, only plot the first "max_num_plots" ones and print a
          warning.
    """

    if not isinstance(events, list):
        events = [events]

    if len(events) == 0:
        raise ValueError("Events is empty")

    if indexes is None:
        indexes = events[0].index()
    elif isinstance(indexes, tuple):
        indexes = [indexes]

    for index in indexes:
        if not isinstance(index, tuple):
            raise ValueError("An index should be a tuple or a list of tuples")

    options = Options(
        backend=backend,
        width_px=width_px,
        height_per_plot_px=height_per_plot_px,
        max_points=max_points,
        min_time=min_time,
        max_time=max_time,
        max_num_plots=max_num_plots,
    )

    if backend not in BACKENDS:
        raise ValueError(
            f"Unknown plotting backend {backend}. Available "
            f"backends: {BACKENDS}"
        )

    return BACKENDS[backend](events=events, indexes=indexes, options=options)


def _plot_matplotlib(
    events: List[NumpyEvent], indexes: List[tuple], options: Options
):
    import matplotlib.pyplot as plt
    from matplotlib.cm import get_cmap

    colors = get_cmap("tab10").colors

    px = 1 / plt.rcParams["figure.dpi"]

    num_plots = 0
    for index in indexes:
        for event in events:
            if index not in event.data:
                raise ValueError(
                    f"Index '{index}' does not exist in event. Check the"
                    " available indexes with 'event.index' and provide one of"
                    " those index to the 'index' argument of 'plot'."
                    ' Alternatively, set "index=None" to select a random'
                    f" index value (e.g., {event.first_index_value()}."
                )
            num_features = len(event.feature_names())
            if num_features == 0:
                # We plot the sampling
                num_features = 1
            num_plots += num_features

    if num_plots > options.max_num_plots:
        print(
            f"The number of plots ({num_plots}) is larger than "
            f'"options.max_num_plots={options.max_num_plots}". Only the first '
            "plots will be printed."
        )
        num_plots = options.max_num_plots

    fig, axs = plt.subplots(
        num_plots,
        figsize=(
            options.width_px * px,
            options.height_per_plot_px * num_plots * px,
        ),
        squeeze=False,
    )

    plot_idx = 0
    for index in indexes:
        if plot_idx >= num_plots:
            break
        for event in events:
            if plot_idx >= num_plots:
                break

            title = str(index)

            feature_names = event.feature_names()

            xs = event.sampling.data[index]
            if options.max_points is not None and len(xs) > options.max_points:
                xs = xs[: options.max_points]

            if event.sampling.is_unix_timestamp:
                xs = [
                    datetime.datetime.fromtimestamp(x, tz=datetime.timezone.utc)
                    for x in xs
                ]

            if len(feature_names) == 0:
                # Plot the ticks

                ax = axs[plot_idx, 0]

                _matplotlib_sub_plot(
                    ax=ax,
                    xs=xs,
                    ys=np.zeros(len(xs)),
                    options=options,
                    color=colors[0],
                    name="[sampling]",
                    marker="+",
                    is_unix_timestamp=event.sampling.is_unix_timestamp,
                    title=title,
                )
                # Only print the index once
                title = None

                plot_idx += 1

            for feature_idx, feature_name in enumerate(feature_names):
                if plot_idx >= num_plots:
                    break

                ax = axs[plot_idx, 0]

                ys = event.data[index][feature_idx].data
                if (
                    options.max_points is not None
                    and len(ys) > options.max_points
                ):
                    ys = ys[: options.max_points]

                _matplotlib_sub_plot(
                    ax=ax,
                    xs=xs,
                    ys=ys,
                    options=options,
                    color=colors[feature_idx % len(colors)],
                    name=feature_name,
                    is_unix_timestamp=event.sampling.is_unix_timestamp,
                    title=title,
                )

                # Only print the index once
                title = None

                plot_idx += 1

    fig.tight_layout()
    return fig


def _matplotlib_sub_plot(
    ax, xs, ys, options, color, name, is_unix_timestamp, title, **wargs
):
    import matplotlib.ticker as ticker

    ax.plot(xs, ys, lw=0.5, color=color, **wargs)

    if options.min_time is not None or options.max_time is not None:
        args = {}
        if options.min_time is not None:
            args["left"] = (
                duration.convert_date_to_duration(options.min_time)
                if not is_unix_timestamp
                else options.min_time
            )
        if options.max_time is not None:
            args["right"] = (
                duration.convert_date_to_duration(options.max_time)
                if not is_unix_timestamp
                else options.max_time
            )
        ax.set_xlim(**args)

    ax.xaxis.set_tick_params(labelsize=8)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
    ax.xaxis.set_minor_locator(ticker.NullLocator())

    ax.set_ylabel(name, size=8)
    ax.yaxis.set_tick_params(labelsize=8)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(5))
    ax.yaxis.set_minor_locator(ticker.NullLocator())

    ax.grid(lw=0.4, ls="--", axis="x")
    if title:
        ax.set_title(title)


BACKENDS = {"matplotlib": _plot_matplotlib}