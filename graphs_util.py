import datetime
import time

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import requests_util
import numpy as np
import plotly.io as pio

INCREASING_COLOR = '#228B22'
DECREASING_COLOR = '#FF0000'


def __moving_average(interval, window_size=10):
    window = np.ones(int(window_size)) / float(window_size)
    return np.convolve(interval, window, 'same')


# Visualisation inspired by https://chart-studio.plotly.com/~jackp/17421/plotly-candlestick-chart-in-python/#/
# Huge thanks to the author!
def __process_and_write_candlelight(dates, openings, closes, highs, lows, volumes, file_path):
    data = [dict(
        type='candlestick',
        open=openings,
        high=highs,
        low=lows,
        close=closes,
        x=dates,
        yaxis='y2',
        name='GS',
        increasing=dict(line=dict(color=INCREASING_COLOR)),
        decreasing=dict(line=dict(color=DECREASING_COLOR)),
    )]

    layout = dict()

    fig = dict(data=data, layout=layout)

    fig['layout'] = dict()
    fig['layout']['plot_bgcolor'] = 'rgb(250, 250, 250)'
    fig['layout']['autosize'] = False
    fig['layout']['width'] = 1600
    fig['layout']['height'] = 900
    fig['layout']['xaxis'] = dict(rangeslider=dict(visible=False))
    fig['layout']['yaxis'] = dict(domain=[0, 0.2], showticklabels=False)
    fig['layout']['yaxis2'] = dict(domain=[0.2, 1], title='ROT price ($)', side='right')
    fig['layout']['showlegend'] = False
    fig['layout']['margin'] = dict(t=15, b=15, r=15, l=15)

    mv_y = __moving_average(closes)
    mv_x = list(dates)

    # Clip the ends
    mv_x = mv_x[5:-5]
    mv_y = mv_y[5:-5]

    fig['data'].append(dict(x=mv_x, y=mv_y, type='scatter', mode='lines',
                            line=dict(width=1),
                            marker=dict(color='#E377C2'),
                            yaxis='y2', name='Moving Average'))

    colors_volume = []

    for i in range(len(closes)):
        if i != 0:
            if closes[i] > closes[i - 1]:
                colors_volume.append(INCREASING_COLOR)
            else:
                colors_volume.append(DECREASING_COLOR)
        else:
            colors_volume.append(DECREASING_COLOR)

    fig['data'].append(dict(x=dates, y=volumes,
                            marker=dict(color=colors_volume),
                            type='bar', yaxis='y', name='Volume'))

    pio.write_image(fig=fig, file=file_path, scale=4)


# t_from and t_to should be numbers, not strings
def __calculate_resolution_from_time(t_from, t_to):
    delta = round(t_to - t_from)
    if delta < 7 * 3600:
        return 1
    elif delta < 13 * 3600:
        return 5
    elif delta < 24 * 3600:
        return 15
    elif delta < 24 * 3600 * 7 + 100:
        return 30
    else:
        return 60


def __preprocess_chartex_data(values, resolution):
    times_from_chartex = [datetime.datetime.fromtimestamp(round(x)) for x in values['t']]

    closes = [float(x) for x in values['c']]
    opens = [float(x) for x in values['o']]
    highs = [float(x) for x in values['h']]
    lows = [float(x) for x in values['l']]
    volumes = [float(x) for x in values['v']]

    frequency = str(resolution) + "min"
    date_list = pd.date_range(start=times_from_chartex[0], end=times_from_chartex[-1],
                              freq=frequency).to_pydatetime().tolist()

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
            volumes.insert(index, 0.0)
            last_index = last_index + 1
            missing_dates_count += 1
    return (date_list, opens, closes, highs, lows, volumes)


# t_from and t_to should be int epoch second
# return the last price
def print_candlestick(token, t_from, t_to, file_path):
    resolution = __calculate_resolution_from_time(t_from, t_to)

    values = requests_util.get_graphex_data(token, resolution, t_from, t_to).json()

    (date_list, opens, closes, highs, lows, volumes) = __preprocess_chartex_data(values, resolution)

    __process_and_write_candlelight(date_list, opens, closes, highs, lows, volumes, file_path)
    return closes[-1]

#
# def main():
#     token = "MAGGOT"
#     t_to = int(time.time())
#     t_from = t_to - 3600 * 12
#     print_candlestick(token, t_from, t_to, "testaaa.png")
#
#
# if __name__ == '__main__':
#     main()
