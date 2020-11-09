from app import app
from mongoDocuments import QueueObject, Config

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL


@app.callback(Output('QueueTable', 'children'),
              [Input('queueRefreshTimer', 'n_intervals')])
def FillList(timer):

    queue = QueueObject.objects.all()

    qList = []
    qList.append(html.Tr(children=[
        html.Th('Jobname'),
        html.Th('User'),
        html.Th('SHA'),
        html.Th('Yaml'),
        html.Th('Checkpoint'),
        html.Th('Status')
    ]))
    for q in queue:

        try:
            yaml = f'{q.customYaml.name} {q.customYaml.uploadDate}'
        except AttributeError:
            yaml = 'Current Active'
        try:
            checkpoint = f'{q.customCheckpoint.name} {q.customCheckpoint.uploadDate}'
        except AttributeError:
            checkpoint = 'None'
        try:
            status = f'Running: {q.running} Status: {q.status}'
        except AttributeError:
            status = f'Running: {q.running}'

        row = html.Tr(children=[
            html.Td(q.job),
            html.Td(q.jobuser),
            html.Td(q.commitSHA),
            html.Td(yaml),
            html.Td(checkpoint),
            html.Td(status)
        ])
        qList.append(row)

    return qList



@app.callback(Output('FailureTable', 'children'),
              [Input('queueRefreshTimer', 'n_intervals')])
def FillFailureList(timer):

    failures = Config.objects(failure__exists=True)

    fList = []
    fList.append(html.Tr(children=[
        html.Th('SHA'),
        html.Th('Failure')
    ]))
    for q in failures:

        row = html.Tr(children=[
            html.Td(q.commitSHA),
            html.Td(q.failure),
        ])
        fList.append(row)

    return fList