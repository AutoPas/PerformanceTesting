import dash_core_components as dcc
import dash_html_components as html

# Callback file imports
import one_v_one_callbacks
import timeline_callbacks
import single_callbacks
from globalVars import *

# Layout

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
    html.H1(children='Performance Explorer'),

    html.Div(children=[
        dcc.Markdown(
            'Interactively compare performance across commits in the [AutoPas](https://github.com/AutoPas/AutoPas) GitHub Repo\n'
            'Working with data from [AutoPas-PerformanceTesting](https://github.com/AutoPas/PerformanceTesting)',
            style={'whiteSpace': 'pre'}),
        html.Button('Refresh Commit List', id='refreshButton', n_clicks=0)]),

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
                        [getDynamicOptionTemplate(i, k, 100/(len(DYNAMIC_OPTIONS)+1), tab=0) for i, k in enumerate(DYNAMIC_OPTIONS)],
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

                    dcc.Interval('LoadCheck', interval=250, disabled=False), # Continuously checking if load has succeeded
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
                )
    ]),

    ],
        style={
            'font-family': 'sans-serif',
        })
