from mongoDocuments import Config, Result
from app import app
from globalVars import *

import time
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State, ALL


@app.callback(
    [Output('SetupSingle', 'options'),
     Output('SetupSingle', 'value')],
    [Input('CommitListSingle', 'value')]
)
def updateSetups(sha):
    print('\n[CALLBACK] Checking Setups for Single')

    if sha is None:
        print('\tSelection is None')
        return [], []

    print(f'\tChecking {sha}')
    config_all = Config.objects(commitSHA=sha).order_by('-date')

    setups = []
    # Listing available setups
    for conf in config_all:

        failure = True if conf.failure is not None else False

        if failure:
            setups.append(
                {'label': f'{conf.setup.name}: {conf.system} [{conf.failure}]',
                 'value': f'{str(conf.id)}',
                 'disabled': failure})
        else:
            setups.append(
                {'label': f'{conf.setup.name}: {conf.system} Run dates [{conf.date}]',
                 'value': f'{str(conf.id)}',
                 'disabled': failure})

    if len(setups) != 0:
        for setup in setups:
            if not setup['disabled']:
                return setups, setup['value']
        return setups, []
    else:
        return [], []


def getOptions(keyword, setup):
    print(f'\n[CALLBACK] Checking Types for {keyword}')
    print('\tSETUPS', setup)
    conf = Config.objects().get(id=setup)
    opts = Result.objects(config=conf).distinct(f'dynamic_{keyword}')
    checkboxes = []
    selected = []
    for val in opts:
        checkboxes.append({'label': val, 'value': val})
        selected.append(val)

    return sorted(checkboxes, key=lambda c: c['label']), sorted(selected)


def _makeDynamicFunction(value):
    @app.callback([Output({'type': 'dynamic2', 'id': value}, 'options'),
                   Output({'type': 'dynamic2', 'id': value}, 'value')],
                  [Input('SetupSingle', 'value')])
    def _dynFunction(setups):
        return getOptions(value, setups)
    return _dynFunction


for k in DYNAMIC_OPTIONS:
    _function = _makeDynamicFunction(k)
    _function.__name__ = f'dynamicCallback_{k}'


@app.callback([Output('GroupingSingle', 'options'),
               Output('GroupingSingle', 'value')],
              [Input('SetupSingle', 'value')])
def availableColoring(setups):
    opt_dict = [{'label': k, 'value': k} for k in DYNAMIC_OPTIONS]
    return opt_dict, DYNAMIC_OPTIONS[0]


@app.callback(Output('SingleData', 'data'),
              [Input('SetupSingle', 'value')])
def singleResults(setup):
    print('\n[CALLBACK] Single Results')

    # Retrieve data
    start = time.time()

    conf = Config.objects().get(id=setup)
    results = Result.objects(config=conf).hint('config_hashed')
    df = aggregate_results(results)
    print(f'\tAggregated singles in {(time.time() - start)} seconds')

    return [df.to_json(), f'{conf.commitSHA[0:8]}: {conf.commitMessage}']


@app.callback([Output('SingleGraph', 'figure'),
               Output('PlotTitleSingle', 'children')],
              [Input('SingleData', 'data'),
               Input('GroupingSingle', 'value'),
               Input({'type': 'dynamic2', 'id': ALL}, 'value')])
def singlePlot(data, coloring, dynamicSelectors):
    print('\n[CALLBACK] Single Plotting')

    if data is None or dynamicSelectors == []:
        return px.line(x=[0], y=[0]), '4) Plot:'

    filtered = pd.read_json(data[0])
    for option, values in zip(DYNAMIC_OPTIONS, dynamicSelectors):
        filtered = filtered[filtered[f'dynamic_{option}'].isin(values)]

    setup = data[1]
    fig = px.box(filtered, x=f'dynamic_{coloring}', y='minTime', color='dynamic_Container', points='all', hover_name='minTime', hover_data=[f'dynamic_{opt}' for opt in DYNAMIC_OPTIONS])

    fig.update_layout(height=900,
                      width=1800,
                      font_family="monospace")
    fig.update_yaxes(automargin=True)

    return fig, f'4) Plot for {setup}'
