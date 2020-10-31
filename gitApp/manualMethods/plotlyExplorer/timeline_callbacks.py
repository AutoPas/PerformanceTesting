from app import app
from mongoDocuments import Config, Result, Setup
from globalVars import *

from dash.dependencies import Input, Output, State, ALL
import pandas as pd
import mongoengine as me
import time
import json
import plotly.express as px
import plotly.graph_objects as go
from multiprocessing import Pool
from functools import partial
import random


@app.callback(
    [Output('CommitSlider', 'marks'),
     Output('CommitSlider', 'value'),
     Output('CommitSlider', 'max'),
     Output('SliderDict', 'data')],
    [Input('refreshButton', 'n_clicks')])
def _setSliderLabels(refreshClicks):
    print(f'\n[CALLBACK] refreshing commit list for {refreshClicks}th time')

    uniqueSHAs = Config.objects().distinct(field='commitSHA')
    print(f'\tFound {len(uniqueSHAs)} unique SHAs')
    options = pd.DataFrame(columns=['SHA', 'CommitDate'])

    for sha in uniqueSHAs:
        c = Config.objects(commitSHA=sha).first()
        options = options.append({'SHA': sha, 'CommitDate': c.commitDate, 'commitMessage': c.commitMessage},
                                 ignore_index=True)

    options = options.sort_values('CommitDate')

    marks = {}
    for i, o in enumerate(options.iterrows()):
        message = o[1].commitMessage.replace('\n', ' ')
        marks[i] = f'{o[1].SHA[0:6]} {message}'
    return marks, [len(marks) - 4, len(marks) - 1], len(marks) - 1, options.to_json()


@app.callback([Output('BaseSetup', 'options'),
               Output('BaseSetup', 'value')],
              [Input('CommitSlider', 'value')],
              [State('SliderDict', 'data')])
def _setSetup(sliderPos, sliderDict):

    low_i = sliderPos[0]
    parsedSlider = pd.read_json(sliderDict)
    baseSHA = parsedSlider.iloc[low_i].SHA

    availConfigs = Config.objects(commitSHA=baseSHA)

    possibleSetups = []

    for conf in availConfigs:

        failure = True if conf.failure is not None else False

        if conf.setup is None:
            continue

        if failure:
            possibleSetups.append(
                {'label': f'{conf.setup.name}: {conf.system} [{conf.failure}]',
                 'value': f'{str(conf.id)}',
                 'disabled': failure})
        else:
            possibleSetups.append(
                {'label': f'{conf.setup.name}: {conf.system} Run date [{conf.date}]',
                 'value': f'{str(conf.id)}',
                 'disabled': failure})

    if len(possibleSetups) != 0:
        return possibleSetups, possibleSetups[0]['value']

    return [], []


@app.callback(Output('LoadTarget', 'data'),
              [Input('CommitSlider', 'value'),
               Input('BaseSetup', 'value')])
def _storeSetupTarget(sliderVal, setupVal):
    return [sliderVal, setupVal]


def _makeDynamicFunction(keyword):
    @app.callback([Output({'type': 'dynamic1', 'id': keyword}, 'options'),
                   Output({'type': 'dynamic1', 'id': keyword}, 'value')],
                  [Input('BaseSetup', 'value')])
    def _dynFunction(setup):

        if setup is None or setup == []:
            return [], []

        conf = Config.objects.get(id=setup)
        options = Result.objects(config=conf).distinct(f'dynamic_{keyword}')

        checkboxes = []
        selected = []

        for value in options:
            checkboxes.append({'label': value, 'value': value})
            selected.append(value)

        return sorted(checkboxes, key=lambda c: c['label']), sorted(selected)

    return _dynFunction


for k in DYNAMIC_OPTIONS:
    _function = _makeDynamicFunction(k)
    _function.__name__ = f'dynamicCallback_{k}'


def _makeResultFrame(results: me.QuerySet):
    """
    Cleaner but slower than aggregate_results in globalVars
    """
    start = time.time()

    lines = [pd.json_normalize(json.loads(r.to_json())) for r in results]
    df = pd.concat(lines, ignore_index=True).drop(columns=['_id.$oid', 'config.$oid'])

    print(f'Returned Frame in: {time.time()-start} seconds for {len(lines)}')
    return df


@app.callback(
    [Output('SliderData', 'data'),
     Output('CurrentLoad', 'data')],
    [Input('BaseSetup', 'value')],
    [State('SliderDict', 'data'),
     State('CommitSlider', 'value')]
)
def _aggregateResults(config, sliderDict, sliderPos):
    print('[CALLBACK] Getting Results')

    if config is None or config == []:
        return None, None

    start = time.time()

    parsedSlider = pd.read_json(sliderDict)

    baseConf = Config.objects().get(id=config)
    baseRes = Result.objects(config=baseConf)

    base_df = aggregate_results(baseRes)

    compData = []

    for i in range(sliderPos[0]+1, sliderPos[1]+1):

        # Get Matching Config for other SHA
        sha = parsedSlider.iloc[i].SHA
        try:
            conf = Config.objects().get(commitSHA=sha, setup=baseConf.setup)
        except me.MultipleObjectsReturned:
            conf = Config.objects(commitSHA=sha, setup=baseConf.setup).order_by('-id').first()
        except me.DoesNotExist:
            continue

        # Get Results
        df = aggregate_results(Result.objects(config=conf))
        print(f'\t{len(df)}')
        if len(df) != 0:
            compData.append(df.to_json())

    print(f'\tAggregated all results: {time.time() - start} seconds')

    return [base_df.to_json(), compData], [sliderPos, config]


@app.callback([Output('TimelinePlotButton', 'disabled'),
               Output('TimelinePlotButton', 'children')],
              [Input('TimelineInterval', 'n_intervals')],
              [State('CurrentLoad', 'data'),
               State('LoadTarget', 'data')])
def _setButton(interval, current, target):

    if current is None or target is None:
        return True, 'Selection is not valid for plotting'

    if current == target:
        return False, 'Start Plot (could take some time, depending on timeline)'  # Slider Data was updated, plotting can happen
    else:
        return True, 'Please wait for data to finish loading for selected configuration'  # Setup was changed, wait for SliderData update


def _matchAndComputeSpeedup(data, base_line):
    matchingTable = (data == base_line).sum(axis=1)

    # TODO: Change 6 to sum of dynamic lines
    matchedLine = data.loc[matchingTable == 6]

    # TODO: Catch more than 1 value error
    speedups = (base_line.minTime / matchedLine.minTime).values
    if len(speedups) == 1:
        return speedups[0]
    else:
        print(speedups)
        raise RuntimeError(f'More than one row matched Search Criteria: {len(speedups)} found!')


@app.callback(Output('TimeLine', 'figure'),
              [Input('TimelinePlotButton', 'n_clicks')],
              [State('SliderData', 'data'),
               State({'type': 'dynamic1', 'id': ALL}, 'value'),
               State('SliderDict', 'data'),
               State('CommitSlider', 'value')])
def _updateFigure(click, data, dynamicSelectors, sliderDict, sliderPos):

    print('[CALLBACK] Plotting Timeline')

    start = time.time()

    if sliderDict is None:
        return go.Figure()

    parsedSlider = pd.read_json(sliderDict)

    filtered_base = pd.read_json(data[0])
    filtered_comp = [pd.read_json(d) for d in data[1]]
    lenAll = len(filtered_base)

    for option, values in zip(DYNAMIC_OPTIONS, dynamicSelectors):
        filtered_base = filtered_base[filtered_base[f'dynamic_{option}'].isin(values)]
        filtered_comp = [df[df[f'dynamic_{option}'].isin(values)] for df in filtered_comp]

    print(f'\tFiltered Set: {len(filtered_base)}/{lenAll}')

    fig = go.Figure()

    speedups = []

    pool = Pool(4)

    # TODO: Add coloring radio buttons
    avContainer = filtered_base['dynamic_Container'].unique()
    col = lambda: random.randint(0, 255)
    colors = {cont: f'#{col():02x}{col():02x}{col():02x}' for cont in avContainer}

    # Match configs and build lines
    for i in range(len(filtered_base)):
        base_line = filtered_base.iloc[i]

        # Check for matching line in all dataframes
        func = partial(_matchAndComputeSpeedup, base_line=base_line)
        conf_speedup = pool.map(func, filtered_comp)

        fig.add_trace(go.Scatter(x=[i for i in range(len(filtered_comp))],
                                 y=conf_speedup,
                                 mode='lines+markers',
                                 opacity=.5,
                                 name=str(base_line),
                                 hovertext=str(base_line),
                                 line=dict(color=colors[base_line['dynamic_Container']])))

        speedups.append(conf_speedup)

    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=[i for i in range(len(filtered_comp))],
            ticktext=[parsedSlider.iloc[i] for i in range(sliderPos[0], sliderPos[1])]
        ),
        width=1900,
        height=1000,
        showlegend=False
    )

    pool.close()

    print(f'\tPlotting took {time.time() - start} seconds')

    return fig
