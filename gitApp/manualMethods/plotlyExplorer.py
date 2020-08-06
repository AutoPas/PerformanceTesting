import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import mongoengine as me
import os
import re
import time

from mongoDocuments import Config, Result

app = dash.Dash(__name__)

# Empty Commit List of Dicts
dummyOptions = []

COLORS = ['#7FB7BE', '#D3F3EE', '#DEDEDF', '#E9C9D0', '#F4B4C1', '#FF9FB2']
DYNAMIC_OPTIONS = ['Container', 'Traversal', 'LoadEstimator', 'DataLayout', 'Newton3']


# Layout

def getDynamicOptionTemplate(i, value, width):
    return html.Div(
                [html.H2(f'{value}:'),
                 dcc.Checklist(id=value,
                               options=[k for k in dummyOptions],
                               labelStyle={'display': 'block'},
                               style={
                                   'font-family': 'monospace',
                               })],
                style={
                    'width': f'{width}%',
                    'background-color': COLORS[i],
                    'float': 'left'
                }
            )


app.layout = html.Div(children=[
    html.H1(children='Performance Explorer'),

    html.Div(children='''
        Interactively compare performance accross commits in the AutoPas GitHub Repo
    '''),

    html.Div(
        [html.Button('Refresh Commit List', id='refreshButton', n_clicks=0)]
    ),

    html.H2('1) Select commits to compare:'),
    html.Div(
        [
            html.P('Base Commit:', style={'font-weight': 'bold'}),
            dcc.Dropdown('CommitList0', options=[k for k in dummyOptions],
                         placeholder='Select 1st Commit...',
                         style={
                             'font-family': 'monospace',
                         })
        ],
        style={
            'width': '50%',
            'float': 'left'
        }
    ),
    html.Div(
        [
            html.P('Compare Commit:', style={'font-weight': 'bold'}),
            dcc.Dropdown('CommitList1', options=[k for k in dummyOptions],
                         placeholder='Select 2nd Commit...',
                         style={
                             'font-family': 'monospace',
                         })
        ],
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

    #### Dynamic Parts ####
    *[getDynamicOptionTemplate(i, k, 100/(len(DYNAMIC_OPTIONS)+1)) for i, k in enumerate(DYNAMIC_OPTIONS)],
    #### Dynamic Parts ####

    html.Div(
        [html.H2('3) Coloring:'),

         dcc.RadioItems('Coloring', options=[k for k in dummyOptions],
                        labelStyle={'display': 'block'},
                        style={
                            'font-family': 'monospace',
                        })],
        style={
            'width': f'{100/(len(DYNAMIC_OPTIONS)+1)}%',
            'background-color': COLORS[len(DYNAMIC_OPTIONS)],
            'float': 'left'
        }
    ),
    html.Br(style={'clear': 'left'}),

    html.H2(id='LoadText', children='Nothing to do'),
    html.Img(id='LoadingImg', src='', width='5%'),

    dcc.Interval('LoadCheck', interval=250, disabled=False),  # Continuously checking if load has succeeded
    html.Div(id='CurrentData', style={'display': 'none'}),

    html.Div(
        [
            html.H2('4) Plot:', id='PlotTitle'),
        ]
    ),

    dcc.Graph(
        id='CompareGraph'
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
    print(f'\n[CALLBACK] refreshing commit list for {refreshClicks}th time')

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
    ids = re.findall(r'(\S+) # (\S+)', string)
    conf0 = Config.objects().get(id=ids[0][0])
    conf1 = Config.objects().get(id=ids[0][1])
    return conf0, conf1


def getOverLap(keyword, setups):
    print(f'\n[CALLBACK] Checking Types for {keyword}')
    print('\tSETUPS', setups)

    if setups is not None and len(setups) != 0:

        conf0, conf1 = getConfigs(setups)

        print(f'\tGetting {keyword} for:\n'
              f'\t{conf0.name}\n'
              f'\t{conf1.name}\n')

        # TODO: Watch out for keyword change, as this is a dynamic key
        opt0 = Result.objects(config=conf0).distinct(f'dynamic_{keyword}')
        opt1 = Result.objects(config=conf1).distinct(f'dynamic_{keyword}')
        overlap = set(opt0) & set(opt1)

        checkboxes = []
        selected = []

        for value in overlap:
            checkboxes.append({'label': value, 'value': value})
            selected.append(value)

        return sorted(checkboxes, key=lambda c: c['label']), sorted(selected)

    else:
        return [], []


def _makeDynamicFunction(value):
    @app.callback([Output(k, 'options'),
                   Output(k, 'value')],
                  [Input('Setups', 'value')])
    def _dynFunction(setups):
        return getOverLap(value, setups)
    return _dynFunction


for k in DYNAMIC_OPTIONS:
    _function = _makeDynamicFunction(k)
    _function.__name__ = f'dynamicCallback_{k}'


@app.callback([Output('Coloring', 'options'),
               Output('Coloring', 'value')],
              [Input('Setups', 'value')])
def availableColoring(setups):
    opt_dict = [{'label': k, 'value': k} for k in DYNAMIC_OPTIONS]
    return opt_dict, DYNAMIC_OPTIONS[0]


@app.callback(
    [Output('LoadingImg', 'src'),
     Output('LoadText', 'children'),
     Output('LoadCheck', 'disabled')],
    [Input('LoadCheck', 'n_intervals'),
     Input('Setups', 'value')],
    [State('CurrentData', 'children')]
)
def updateImg(n, setups, data):
    """
    Triggered on setup change, this callback sets the loading state


    Returns:
        loading url
    """

    if setups is None or setups == []:
        return '', '', False
    else:
        if data is None:
            return 'https://media.giphy.com/media/sSgvbe1m3n93G/giphy.gif', f'Loading Results and computing speedups', False

        setupsLoaded = data[1]
        setupsTarget = setups

        if setupsLoaded == setupsTarget:
            return '', f'Speedups computed, ready to plot', True
        else:
            return 'https://media.giphy.com/media/sSgvbe1m3n93G/giphy.gif', f'Loading Results and computing speedups', False


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
    results0 = Result.objects(config=conf0).hint('config_hashed')
    results1 = Result.objects(config=conf1).hint('config_hashed')

    missing_results = 0

    start = time.time()

    def aggregate_results(results: me.QuerySet) -> pd.DataFrame:
        """
        Aggregate Results into pandas Dataframe
        Args:
            results: queryset

        Returns:
            df: Dataframe
        """

        temp_dict = {}

        for i, r in enumerate(results):
            data = r.__dict__
            data['meanTime'] = r.meanTime
            temp_dict[i] = data

        df = pd.DataFrame.from_dict(temp_dict)
        df = df.drop(['_cls', '_dynamic_lock', '_fields_ordered'])
        df = df.transpose()
        return df

    df0 = aggregate_results(results0)
    df1 = aggregate_results(results1)

    print(f'\tAggregated in {(time.time() - start)} seconds')

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
        # TODO: watch out for no matches when adding other timing quants into dataframe
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
    [Output('CompareGraph', 'figure'),
     Output('PlotTitle', 'children')],
    [Input('CurrentData', 'children'),
     Input('Container', 'value'),
     Input('Traversal', 'value'),
     Input('DataLayout', 'value'),
     Input('Newton3', 'value'),
     Input('Coloring', 'value'),
     ]
)
def plotComparison(data, container, traversal, datalayout, newton3, coloring):
    print('\n[CALLBACK] Plotting Comparison')

    if data is None or container == []:
        return px.line(x=[0], y=[0]), '4) Plot:'

    speedupTable = pd.read_json(data[0])

    filtered_by_container = speedupTable[speedupTable['dynamic_Container'].isin(container)]
    filtered_by_traversal = filtered_by_container[filtered_by_container['dynamic_Traversal'].isin(traversal)]
    filtered_by_datalayout = filtered_by_traversal[filtered_by_traversal['dynamic_DataLayout'].isin(datalayout)]
    filtered_by_newton3 = filtered_by_datalayout[filtered_by_datalayout['dynamic_Newton3'].isin(newton3)]

    finalSet = filtered_by_newton3

    print(f'\tFiltered Set: {len(finalSet)}/{len(speedupTable)}')

    fig = px.bar(finalSet,
                 x='speedup',
                 y='label',
                 color=f'dynamic_{coloring}',
                 orientation='h')

    fig.add_shape(
        dict(
            type='line',
            x0=1,
            y0=0,
            x1=1,
            y1=len(finalSet),
            line=dict(
                color='Black',
                width=3,
            )
        )
    )

    fig.update_layout(height=max(10 * len(finalSet), 200),
                      width=1800)
    fig.update_yaxes(automargin=True)


    return fig, f'Plotting Filtered Set: {len(finalSet)}/{len(speedupTable)}'


if __name__ == '__main__':
    me.connect('performancedb', host='localhost:30017', username=os.environ['USERNAME'],
               password=os.environ['PASSWORD'])

    app.run_server(debug=True)
