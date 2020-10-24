import dash_core_components as dcc
import dash_html_components as html

# Callback file imports
import one_v_one_callbacks
import timeline_callbacks
import single_callbacks
import customJobs_callbacks
import verification_callbacks
import queueList_callbacks
from globalVars import *


# Layout

# TODO: Documentation

def getDynamicOptionTemplate(i, value, width, tab):
    return html.Div(
        [html.H2(f'{value}:'),
         dcc.Checklist(id={'type': f'dynamic{tab}', 'id': value},
                       options=[k for k in dummyOptions],
                       labelStyle={'display': 'block'},
                       style={
                           'font-family': 'monospace',
                       })],
        style={
            'width': f'{width}%',
            'background-color': COLORS[i],
            'color': 'white',
            'float': 'left',
            'padding': '.3%',
            'box-sizing': 'border-box'
        }
    )


def makeLayout():
    return html.Div(children=[
        dcc.Location(id='loc'),  # Check URL for Git Auth
        dcc.Store(id='loginInfo', storage_type='session', data={'user': None, 'status': None}),  # Used for Git Auth

        html.H1(children='Performance Explorer'),

        html.Div(children=[
            html.Div(children=[
                dcc.Markdown(
                    'Interactively compare performance across commits in the [AutoPas](https://github.com/AutoPas/AutoPas) GitHub Repo\n'
                    'Working with data from [AutoPas-PerformanceTesting](https://github.com/AutoPas/PerformanceTesting)',
                    style={'whiteSpace': 'pre'}),
                html.Button('Refresh Commit List', id='refreshButton', n_clicks=0),
                html.Br(), ]),

        ], style={'float': 'left'}),
        html.Div(children=[
            html.Button('Login', id='loginButton', n_clicks=0),
            html.P(id='loginResponse'),
            html.Br(),
        ], style={'float': 'right'}),
        html.Br(style={'clear': 'left'}),

        dcc.Tabs(id='tabs', value='tab2', children=[
            dcc.Tab(label='1v1 Compare', value='tab0',
                    children=html.Div([
                        html.Div([
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
                        ],
                            style={
                                'width': '100%',
                                'float': 'left',
                                'background-color': '#F5F0F6'
                            }),
                        html.Br(),

                        html.Div(
                            [html.H2('2) Select setup to compare:'),

                             dcc.Dropdown('Setups', options=[k for k in dummyOptions],
                                          placeholder='Select Setup...',
                                          style={
                                              'font-family': 'monospace',
                                          })],
                            style={
                                'width': '100%',
                                'float': 'left',
                                'background-color': '#F5F0F6',
                                'padding-bottom': '1%'
                            }
                        ),
                        html.Br(),

                        html.Div(
                            #### Dynamic Parts ####
                            [getDynamicOptionTemplate(i, k, 100 / (len(DYNAMIC_OPTIONS) + 1), tab=0) for i, k in
                             enumerate(DYNAMIC_OPTIONS)],
                            #### Dynamic Parts ####
                        ),

                        html.Div(
                            [html.H2('3) Coloring:'),

                             dcc.RadioItems('Coloring', options=[k for k in dummyOptions],
                                            labelStyle={'display': 'block'},
                                            style={
                                                'font-family': 'monospace',
                                            })],
                            style={
                                'width': f'{100 / (len(DYNAMIC_OPTIONS) + 1)}%',
                                'background-color': COLORS[len(DYNAMIC_OPTIONS)],
                                'float': 'left',
                                'padding': '.3%',
                                'box-sizing': 'border-box'
                            }
                        ),
                        html.Br(style={'clear': 'left'}),

                        html.H2(id='LoadText', children='Nothing to do'),
                        html.Img(id='LoadingImg', src='', width='5%'),

                        dcc.Interval('LoadCheck', interval=250, disabled=False),
                        # Continuously checking if load has succeeded
                        # TODO: Replace this with dcc.Store
                        html.Div(id='CurrentData', style={'display': 'none'}),

                        html.Div(
                            [
                                html.H2('4) Plot:', id='PlotTitle'),
                            ]
                        ),

                        dcc.Graph(
                            id='CompareGraph'
                        ),

                    ])),
            dcc.Tab(label='Compare over time', value='tab1',
                    children=html.Div([
                        html.Div(
                            [
                                # TODO: SLIDER VIEW AND BETTER VERTICAL LAYOUT
                                dcc.RangeSlider(
                                    id='CommitSlider',
                                    min=0,
                                    max=9,
                                    marks={i: 'Label {}'.format(i) for i in range(10)},
                                    value=[4, 5],
                                    pushable=1,
                                    vertical=True,
                                    verticalHeight=400
                                ),
                                dcc.Store(id='SliderDict', data=None),
                                dcc.Store(id='SliderData', data=None),
                                dcc.Store(id='LoadTarget', data=None),
                                dcc.Store(id='CurrentLoad', data=None),
                                dcc.Interval(id='TimelineInterval', interval=250, disabled=False)
                            ],
                            style={'font-family': 'monospace',
                                   'width': '100%',
                                   'white-space': 'pre'}
                        ),

                        html.Div(
                            dcc.Dropdown('BaseSetup', options=[k for k in dummyOptions],
                                         placeholder='Select Setup...',
                                         style={
                                             'font-family': 'monospace',
                                         }),
                            style={
                                'width': '100%',
                                'float': 'left',
                                'background-color': '#F5F0F6',
                                'padding-bottom': '1%'
                            }
                        ),
                        html.Br(),

                        html.Div(
                            #### Dynamic Parts ####
                            [getDynamicOptionTemplate(i, k, 100 / (len(DYNAMIC_OPTIONS)), tab=1) for i, k in
                             enumerate(DYNAMIC_OPTIONS)],
                            #### Dynamic Parts ####
                        ),
                        html.Br(style={'clear': 'left'}),

                        html.Div(
                            [
                                html.H2('Plot:', id='TimelinePlotDiv'),
                                html.Button(children='Button not active yet',
                                            id='TimelinePlotButton',
                                            disabled=True)
                            ]
                        ),

                        dcc.Graph(
                            id='TimeLine'
                        )])),
            dcc.Tab(label='Single view', value='tab2',
                    children=[
                        html.Div([
                            html.H2('1) Select commits to compare:'),
                            html.Div(
                                [
                                    dcc.Dropdown('CommitListSingle', options=[k for k in dummyOptions],
                                                 placeholder='Select Commit...',
                                                 style={
                                                     'font-family': 'monospace',
                                                 })
                                ],
                                style={
                                    'width': '100%',
                                    'float': 'left',
                                }
                            )],
                            style={
                                'width': '100%',
                                'float': 'left',
                                'background-color': '#F5F0F6'
                            }),
                        html.Br(),

                        html.Div(
                            [html.H2('2) Select setup to compare:'),

                             dcc.Dropdown('SetupSingle', options=[k for k in dummyOptions],
                                          placeholder='Select Setup...',
                                          style={
                                              'font-family': 'monospace',
                                          })],
                            style={
                                'width': '100%',
                                'float': 'left',
                                'background-color': '#F5F0F6',
                                'padding-bottom': '1%'
                            }
                        ),
                        html.Br(),

                        html.Div(
                            #### Dynamic Parts ####
                            [getDynamicOptionTemplate(i, k, 100 / (len(DYNAMIC_OPTIONS) + 1), tab=2) for i, k in
                             enumerate(DYNAMIC_OPTIONS)],
                            #### Dynamic Parts ####
                        ),

                        html.Div(
                            [html.H2('3) Grouping:'),

                             dcc.RadioItems('GroupingSingle', options=[k for k in dummyOptions],
                                            labelStyle={'display': 'block'},
                                            style={
                                                'font-family': 'monospace',
                                            })],
                            style={
                                'width': f'{100 / (len(DYNAMIC_OPTIONS) + 1)}%',
                                'background-color': COLORS[len(DYNAMIC_OPTIONS)],
                                'float': 'left',
                                'padding': '.3%',
                                'box-sizing': 'border-box'
                            }
                        ),
                        html.Br(style={'clear': 'left'}),
                        dcc.Store(id='SingleData', data=None),

                        html.Div(
                            [
                                html.H2('4) Plot, please wait:', id='PlotTitleSingle'),
                            ]
                        ),

                        dcc.Graph(
                            id='SingleGraph'
                        ),

                    ]
                    ),
            dcc.Tab(label='Submit Job', value='tab3', children=[
                html.Div(children=[
                    html.H1('Submit Custom Jobs to the worker queue (if logged in).'),

                    # Hide div if not logged in
                    html.Div(id='submissionDiv', children=[
                        html.H2('1) Job Name:'),
                        dcc.Input(id='CustomJobName', placeholder='CUSTOM JOB NAME', required=True, debounce=False),
                        html.H2('2) Git SHAs to test (1 per line):'),
                        dcc.Textarea(id='CustomSHAList', placeholder='Custom SHAs',
                                     required=True,
                                     style={'width': '40em',
                                            'height': '6em'}),
                        html.H2('3) Upload Yaml Config OR select from list of available:'),
                        dcc.RadioItems(id='YamlSelect', options=[{'label': 'Upload YAML File', 'value': 'uploaded'},
                                                                 {'label': 'Existing YAML', 'value': 'existing'}],
                                       value='existing', labelStyle={'display': 'inline-block'}),
                        html.Div(id='YamlUploadDiv', children=[
                            html.H3('Upload YAML config file to use:'),
                            dcc.Upload(id='YamlCustomUpload', multiple=False, children=[],
                                       style={
                                           'width': '100%',
                                           'height': '60px',
                                           'lineHeight': '60px',
                                           'borderWidth': '1px',
                                           'borderStyle': 'dashed',
                                           'borderRadius': '5px',
                                           'textAlign': 'center',
                                           # 'display': 'block'
                                       }),
                        ]),
                        html.Div(id='YamlSelectDiv', children=[
                            html.H3('Choose from existing YAML files'),
                            dcc.Dropdown(id='YamlAvailable', options=[]),
                        ]),
                        html.H2('4) OPTIONAL: Upload Checkpoint file OR select from list of available:'),
                        dcc.RadioItems(id='CheckpointSelect',
                                       options=[{'label': 'No Checkpoint', 'value': 'noCheckPoint'},
                                                {'label': 'Upload Checkpoint File',
                                                 'value': 'uploaded'},
                                                {'label': 'Existing Checkpoint',
                                                 'value': 'existing'},
                                                ],
                                       value='noCheckPoint', labelStyle={'display': 'inline-block'}),
                        html.Div(id='CheckpointUploadDiv', children=[
                            html.H3('Upload Checkpoint File to use:'),
                            dcc.Upload(id='CheckpointCustomUpload', multiple=False, children=[],
                                       style={
                                           'width': '100%',
                                           'height': '60px',
                                           'lineHeight': '60px',
                                           'borderWidth': '1px',
                                           'borderStyle': 'dashed',
                                           'borderRadius': '5px',
                                           'textAlign': 'center',
                                           # 'display': 'block'
                                       }),
                        ]),
                        html.Div(id='CheckpointSelectDiv', children=[
                            html.H3('Choose from existing Checkpoint files'),
                            dcc.Dropdown(id='CheckpointAvailable', options=[]),
                        ]),
                        html.Br(),
                        html.H1('Job Summary:'),
                        html.P(id='JobSummary', children=[]),
                        html.Button('Submit Job', id='submitJob', n_clicks=0),
                        html.P(id='SubmitResponse', children=[], style={'white-space': 'pre-wrap'}),
                    ],
                             style={'display': 'none'}),
                ],
                    style={'text-align': 'center'}
                )
            ]),

            # TODO: Show yaml in queue

            dcc.Tab(label='Current Queue', value='tab4', children=[
                html.Div(children=[
                    html.Br(),
                    html.Button('Refresh Queue', id='refreshQueue', n_clicks=0),
                    html.Table(id='QueueTable', children=[], style={'margin': '0 auto'}),
                    html.Br(),
                    html.H1('Cancel Job:'),
                    dcc.Input(id='CancelJobName', placeholder='CUSTOM JOB NAME', debounce=True),
                    html.Button('Cancel Job', id='cancelJob', n_clicks=0),
                    html.P(id='CancelResponse', children=[])
                ], style={'text-align': 'center'}
                )
            ]),

        ]),

    ],
        style={
            'font-family': 'sans-serif',
        })
