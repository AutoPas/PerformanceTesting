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
# fig = px.line(x=[0, 1, 2], y=[0, 1, -1])

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
    print(f'Found {len(uniqueSHAs)} unique SHAs')
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
        print('Selection is None')
        return [], []

    print(f'Comparing {sha0} vs. {sha1}')
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
    conf0 = Config.objects(id=ids[0][0]).first()
    conf1 = Config.objects(id=ids[0][1]).first()
    return conf0, conf1


@app.callback([Output('Container', 'options'),
               Output('Container', 'value'),
               Output('plotButton', 'disabled')],
              [Input('Setups', 'value')])
def availableContainer(setups):
    print('[CALLBACK] Checking Container Types')
    print('SETUPS', setups)

    if setups is not None and len(setups) != 0:

        conf0, conf1 = getConfigs(setups)

        print(f'Getting Container for:\n'
              f'{conf0.name}\n'
              f'{conf1.name}\n')

        # TODO: Watch out for keyword change, as this is a dynamic key
        cont0 = Result.objects(config=conf0).distinct('dynamic_Container')
        cont1 = Result.objects(config=conf1).distinct('dynamic_Container')
        overlap = set(cont0) & set(cont1)

        checkboxes = []
        selected = []

        for container in overlap:
            checkboxes.append({'label': container, 'value': container})
            selected.append(container)

        return [sorted(checkboxes, key=lambda c: c['label']), sorted(selected), False]

    else:
        return [], [], True


@app.callback(
    Output('example-graph', 'figure'),
    [Input('plotButton', 'n_clicks')],
    [State('Setups', 'value'),
     State('Container', 'value')]
)
def plotComparison(click, setups, container):
    print('\n[CALLBACK] Plotting Comparison')

    print(setups)
    if setups is None:
        return px.line(x=[0], y=[0])
    else:

        conf0, conf1 = getConfigs(setups)
        # Get all results for config
        results0 = Result.objects(config=conf0)
        results1 = Result.objects(config=conf1)

        x = []
        y = []
        z = []
        w = []
        v = []

        for r in results0:

            if r.dynamic_Container in container:

                x.append(r.dynamic_Container)
                y.append(r.meanTime)
                z.append(r.dynamic_DataLayout)
                w.append(r.dynamic_Newton3)
                v.append('c0')

        for r in results1:

            if r.dynamic_Container in container:

                x.append(r.dynamic_Container)
                y.append(r.meanTime)
                z.append(r.dynamic_DataLayout)
                w.append(r.dynamic_Newton3)
                v.append('c1')


        df = pd.DataFrame(
            {
                'container': x,
                'time': y,
                'layout': z,
                'newton3': w,
                'commit': v
            }
        )

        return px.bar(df, x='container', y='time', color='commit', barmode='group')


if __name__ == '__main__':
    me.connect('performancedb', host='localhost:30017', username=os.environ['USERNAME'],
               password=os.environ['PASSWORD'])

    app.run_server(debug=True)
