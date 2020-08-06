import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np
import mongoengine as me
import os
import re

from mongoDocuments import Config, Result

app = dash.Dash(__name__)

# Empty Commit List of Dicts
dummyOptions = []

# Layout

app.layout = html.Div(children=[
    html.H1(children='Performance Explorer'),

    html.Div(children='''
        Interactively compare performance accross commits in the AutoPas GitHub Repo
    '''),

    html.Div(
        [html.Button('Refresh Commit List', id='refreshButton', n_clicks=0),
         html.Button('Reset', id='resetButton', n_clicks=0)]
    ),

    html.H2('1) Select commits to compare:'),
    html.Div(
        dcc.Dropdown('CommitList0', options=[k for k in dummyOptions],
                     placeholder='Select 1st Commit...',
                     style={
                         'font-family': 'monospace',
                     }),
        style={
            'width': '50%',
            'float': 'left'
        }
    ),
    html.Div(
        dcc.Dropdown('CommitList1', options=[k for k in dummyOptions],
                     placeholder='Select 2nd Commit...',
                     style={
                         'font-family': 'monospace',
                     }),
        style={
            'width': '50%',
            'float': 'right'
        }
    ),

    html.Div(
        [html.H2('2) Select setup to compare:'),

         dcc.Dropdown('Setups', options=[k for k in dummyOptions],
                      placeholder='Select Setup...',
                      style={
                          'font-family': 'monospace',
                      })]
    ),

    html.Div(
        [html.H2('3) Select Container to compare:'),

         dcc.Checklist('Container', options=[k for k in dummyOptions],
                       style={
                           'font-family': 'monospace',
                       })]
    ),

    html.H2(id='LoadText', children='Nothing to do'),
    html.Img(id='LoadingImg', src='', width='5%'),

    dcc.Interval('LoadCheck', interval=250, disabled=False),  # Continuously checking if load has succeeded
    html.Div(id='CurrentData', style={'display': 'none'}),

    html.Div(
        [
            html.H2('4) Plot:'),
            html.Button('Plot Comparison', id='plotButton', n_clicks=0, disabled=True)
        ]
    ),

    dcc.Graph(
        id='example-graph'
    ),

])


### Parsing available commits

@app.callback(
    [Output('CommitList0', 'options'),
     Output('CommitList0', 'value'),
     Output('CommitList1', 'options'),
     Output('CommitList1', 'value')],
    [Input('refreshButton', 'n_clicks')])
def reloadAvailableCommits(refreshClicks):
    print(f'\n[CALLBACK] refreshing commit list')

    uniqueSHAs = Config.objects().distinct(field='commitSHA')
    print(f'\tFound {len(uniqueSHAs)} unique SHAs')
    options = []

    for sha in uniqueSHAs:
        c = Config.objects(commitSHA=sha).first()
        options.append({'label': f'[{c.commitDate}: {sha[:8]}]  {c.commitMessage}', 'value': sha})

    sorted_options = sorted(options, key=lambda x: x['label'])

    return sorted_options, sorted_options[-2]['value'], sorted_options, sorted_options[-1]['value']


### Parsing available setups

@app.callback(
    [Output('Setups', 'options'),
     Output('Setups', 'value')],
    [Input('CommitList0', 'value'),
     Input('CommitList1', 'value')]
)
def updateSetups(sha0, sha1):
    print('\n[CALLBACK] Checking Setups')

    if sha0 is None or sha1 is None:
        print('\tSelection is None')
        return [], []

    print(f'\tComparing {sha0} vs. {sha1}')
    config0_all = Config.objects(commitSHA=sha0).order_by('-date')

    # Listing available setups

    possible_comparisons = []

    for conf0 in config0_all:
        conf1_avail = Config.objects(commitSHA=sha1, system=conf0.system, setup=conf0.setup).order_by('-date')
        for conf1 in conf1_avail:
            possible_comparisons.append({'label': f'{conf1.setup.name}: {conf1.system}',
                                         'value': f'{str(conf0.id)} # {str(conf1.id)}'})

    if len(possible_comparisons) != 0:
        return possible_comparisons, possible_comparisons[0]['value']
    else:
        return [], []


### Setting Container Buttons

def getConfigs(string):
    ids = re.findall('(\S+) # (\S+)', string)
    conf0 = Config.objects().get(id=ids[0][0])
    conf1 = Config.objects().get(id=ids[0][1])
    return conf0, conf1


@app.callback([Output('Container', 'options'),
               Output('Container', 'value')],
              [Input('Setups', 'value')])
def availableContainer(setups):
    print('\n[CALLBACK] Checking Container Types')
    print('\tSETUPS', setups)

    if setups is not None and len(setups) != 0:

        conf0, conf1 = getConfigs(setups)

        print(f'\tGetting Container for:\n'
              f'\t{conf0.name}\n'
              f'\t{conf1.name}\n')

        # TODO: Watch out for keyword change, as this is a dynamic key
        cont0 = Result.objects(config=conf0).distinct('dynamic_Container')
        cont1 = Result.objects(config=conf1).distinct('dynamic_Container')
        overlap = set(cont0) & set(cont1)

        checkboxes = []
        selected = []

        for container in overlap:
            checkboxes.append({'label': container, 'value': container})
            selected.append(container)

        return sorted(checkboxes, key=lambda c: c['label']), sorted(selected)

    else:
        return [], []



@app.callback(
    [Output('LoadingImg', 'src'),
     Output('LoadText', 'children'),
     Output('plotButton', 'disabled')],
    [Input('LoadCheck', 'n_intervals')],
    [State('CurrentData', 'children'),
     State('Setups', 'value')]
)
def updateImg(n, data, setups):
    """
    Triggered on setup change, this callback sets the loading state


    Returns:
        loading url
    """

    if setups is None or setups == []:
        return '', '', True
    else:
        if data is None:
            return 'https://media.giphy.com/media/sSgvbe1m3n93G/giphy.gif', f'Loading Results and computing speedups', True

        setupsLoaded = data[1]
        setupsTarget = setups

        if setupsLoaded == setupsTarget:
            return '', f'Speedups computed, ready to plot', False
        else:
            return 'https://media.giphy.com/media/sSgvbe1m3n93G/giphy.gif', f'Loading Results and computing speedups', True


@app.callback(
    Output('CurrentData', 'children'),
    [Input('Setups', 'value')],
)
def Z_retrieveDataAndBuildSpeedupTable(setups):
    print('\n[CALLBACK] Retrieving Data')

    if setups is None or setups == []:
        return [None, None]

    conf0, conf1 = getConfigs(setups)
    # Get all results for both configs
    results0 = Result.objects(config=conf0).batch_size(1000).exclude('measurements')
    results1 = Result.objects(config=conf1).batch_size(1000).exclude('measurements')

    missing_results = 0

    def aggregate_results(results: me.QuerySet) -> pd.DataFrame:
        """
        Aggregate Results into pandas Dataframe
        Args:
            results: queryset

        Returns:
            df: Dataframe
        """

        df = pd.DataFrame()

        for r in results:
            data = r.__dict__
            data['meanTime'] = r.meanTime
            df = df.append(r.__dict__, ignore_index=True)

        df = df.drop(columns=['_cls', '_dynamic_lock', '_fields_ordered'])
        return df

    df0 = aggregate_results(results0)
    df1 = aggregate_results(results1)

    def calculate_speedup(data0: pd.DataFrame, data1: pd.DataFrame) -> pd.DataFrame:
        """
        Return Dataframe containing all matched configs and the speedup

        Args:
            data0: aggregated result dataframe commit0
            data1: aggregated result dataframe commit1

        Returns:
            table: dataframe with speedup table
        """

        quantity = 'meanTime'
        all_data1_configs = data1.drop(columns=quantity)  # Drop column for matching
        table = all_data1_configs.copy()

        for i_search in range(len(data0)):
            search_config = data0.loc[i_search, data0.columns != quantity]  # Select row except time column
            full_match = (all_data1_configs == search_config).all(axis=1)  # Checks against all df1 rows and marks if full row matches df0 row, except z column
            i_match = full_match[full_match == True].index[0]  # Get index of the full match in data1

            speedup = data1.loc[i_match, quantity] / data0.loc[i_search, quantity]
            label = ''.join(str(v) + ' ' for v in data1.loc[i_match, :].values)
            table.loc[i_match, 'speedup'] = speedup
            table.loc[i_match, 'label'] = label

        return table

    speedupTable = calculate_speedup(df0, df1).sort_values('speedup')

    return [speedupTable.to_json(), setups]



@app.callback(
    Output('example-graph', 'figure'),
    [Input('plotButton', 'n_clicks')],
    [State('Container', 'value'),
     State('CurrentData', 'children')]
)
def plotComparison(click, container, data):
    print('\n[CALLBACK] Plotting Comparison')

    if data is None:
        return px.line(x=[0], y=[0])

    speedupTable = pd.read_json(data[0])

    return px.bar(speedupTable, x='speedup', y='label', color='dynamic_Container', orientation='h')


if __name__ == '__main__':
    me.connect('performancedb', host='localhost:30017', username=os.environ['USERNAME'],
               password=os.environ['PASSWORD'])

    app.run_server(debug=True)
