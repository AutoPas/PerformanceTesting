from app import app
from mongoDocuments import Config, Result, Setup
from globalVars import *

from dash.dependencies import Input, Output, State, ALL
import pandas as pd
import mongoengine as me
import time
import json
import plotly.express as px

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
    Output('SliderSpeedups', 'data'),
    [Input('BaseSetup', 'value')],
    [State('SliderDict', 'data'),
     State('CommitSlider', 'value')]
)
def _ComputeSpeedupTimeline(config, sliderDict, sliderPos):

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
        compData.append(df.to_json())

    print(f'\tAggregated all results: {time.time() - start} seconds')

    return [base_df.to_json(), compData]


@app.callback(Output('TimeLine', 'figure'),
              [Input('SliderSpeedups', 'data')])
def _updateFigure(data):

    print('[CALLBACK] Plotting Timeline')

    start = time.time()

    base_df = pd.read_json(data[0])
    compData = [pd.read_json(d) for d in data[1]]

    # TODO: actually check for correct config
    y = [c.iloc[0].minTime for c in compData]
    x = [i for i in range(len(y))]

    fig = px.line(x=x, y=y)

    print(f'\tPlotting took {time.time() - start} seconds')

    return fig
