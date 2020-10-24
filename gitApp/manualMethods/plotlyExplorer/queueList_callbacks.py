from app import app
from mongoDocuments import QueueObject

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL


@app.callback(Output('QueueTable', 'children'),
              [Input('refreshQueue', 'n_clicks')])
def FillList(refresh):

    queue = QueueObject.objects.all()

    qList = []
    qList.append(html.Tr(children=[
        html.Th('Jobname'),
        html.Th('User'),
        html.Th('SHA'),
        html.Th('Yaml')
    ]))
    for q in queue:
        text = f'Job: {q.job}\t SHA: {q.commitSHA}'

        try:
            yaml = f'{q.customYaml.name} {q.customYaml.uploadDate}'
        except AttributeError:
            yaml = 'Current Active'
        row = html.Tr(children=[
            html.Td(q.job),
            html.Td(q.jobuser),
            html.Td(q.commitSHA),
            html.Td(yaml)
        ])
        qList.append(row)

    return qList
