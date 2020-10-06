import datetime
import time

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import requests_util


def __process_and_write_candlelight(dates, openings, closes, highs, lows, file_path):
    fig = go.Figure(data=[go.Candlestick(x=dates,
                                         open=openings,
                                         high=highs,
                                         low=lows,
                                         close=closes)])
    fig.update_layout(
        autosize=False,
        width=1600,
        height=900,
        # title='Road to $.666',
        yaxis_title='ROT price (usdt)',
        xaxis_rangeslider_visible=False,
        yaxis_side="right",
        margin=go.layout.Margin(l=15, r=15, b=15, t=15)
    )
    fig.write_image(file_path, scale=4)
    plt.close()


# t_from and t_to should be numbers, not strings
def __calculate_resolution_from_time(t_from, t_to):
    delta = round(t_to - t_from)
    if delta < 7 * 3600:
        return 1
    elif delta < 13 * 3600:
        return 5
    elif delta < 24 * 3600:
        return 15
    else:
        return 60


def __preprocess_chartex_data(values, resolution):
    times_from_chartex = [datetime.datetime.fromtimestamp(round(x)) for x in values['t']]

    closes = [float(x) for x in values['c']]
    opens = [float(x) for x in values['o']]
    highs = [float(x) for x in values['h']]
    lows = [float(x) for x in values['l']]

    frequency = str(resolution) + "min"
    date_list = pd.date_range(start=times_from_chartex[0], end=times_from_chartex[-1], freq=frequency).to_pydatetime().tolist()

    last_index = 0
    missing_dates_count = 0
    for date in date_list:
        if date in times_from_chartex:
            last_index = times_from_chartex.index(date) + missing_dates_count
            pass
        else:
            index = last_index + 1
            price = closes[index - 1]
            closes.insert(index, price)
            highs.insert(index, price)
            lows.insert(index, price)
            opens.insert(index, price)
            last_index = last_index + 1
            missing_dates_count += 1
    return (date_list, opens, closes, highs, lows)


# t_from and t_to should be int epoch second
# return the last price
def print_candlestick(token, t_from, t_to, file_path):
    resolution = __calculate_resolution_from_time(t_from, t_to)

    values = requests_util.get_graphex_data(token, resolution, t_from, t_to).json()

    (date_list, opens, closes, highs, lows) = __preprocess_chartex_data(values, resolution)

    __process_and_write_candlelight(date_list, opens, closes, highs, lows, file_path)
    return closes[-1]
