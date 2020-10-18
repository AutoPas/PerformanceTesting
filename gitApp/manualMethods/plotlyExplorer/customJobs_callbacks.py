from mongoDocuments import Config, QueueObject, Checkpoint, Setup
from app import app
from globalVars import *

import re
import base64
from dash.dependencies import Input, Output, State, ALL
import dash_core_components as dcc
import dash_html_components as html


@app.callback([Output('YamlUploadDiv', 'style'),
               Output('YamlSelectDiv', 'style')],
              [Input('YamlSelect', 'value')])
def YamlOptionVisibility(yamlSelect):
    print('\n[CALLBACK] Yaml Option Select')
    if yamlSelect == 'uploaded':
        return {'display': 'block'}, {'display': 'none'}
    elif yamlSelect == 'existing':
        return {'display': 'none'}, {'display': 'block'}
    else:
        print('WRONG YAML SELECT OPTION IN CUSTOM JOB')
        return {}, {}


@app.callback(Output('YamlAvailable', 'options'),
              [Input('YamlSelect', 'value')])
def YamlAvailable(yamlSelect):
    if yamlSelect == 'existing':
        allSetups = Setup.objects()
        opts = []
        for setup in allSetups:
            opts.append({'label': f'{setup.name} {setup.uploadDate}', 'value': f'{setup.yamlHash}'})
        return opts
    else:
        return []


@app.callback(Output('YamlCustomUpload', 'children'),
              [Input('YamlCustomUpload', 'filename')])
def YamlUploadConfirm(uploadFilename):
    if uploadFilename is None:
        return ['Drag and Drop or ', html.A('Select a File')]
    else:
        return uploadFilename


@app.callback([Output('CheckpointUploadDiv', 'style'),
               Output('CheckpointSelectDiv', 'style')],
              [Input('CheckpointSelect', 'value')])
def CheckpointOptionVisibility(checkpointSelect):
    print('\n[CALLBACK] Checkpoint Option Select')
    if checkpointSelect == 'uploaded':
        return {'display': 'block'}, {'display': 'none'}
    elif checkpointSelect == 'existing':
        return {'display': 'none'}, {'display': 'block'}
    elif checkpointSelect == 'noCheckPoint':
        return {'display': 'none'}, {'display': 'none'}
    else:
        print('WRONG CHECKPOINT SELECT OPTION IN CUSTOM JOB')
        return {}, {}


@app.callback(Output('CheckpointAvailable', 'options'),
              [Input('CheckpointSelect', 'value')])
def ChecksAvailable(checkpointSelect):
    if checkpointSelect == 'existing':
        allCheckpoints = Checkpoint.objects()
        opts = []
        for check in allCheckpoints:
            opts.append({'label': f'{check.name} {check.uploadDate} {check.setup.name}', 'value': f'{check.id}'})
        return opts
    else:
        return []


@app.callback(Output('CheckpointCustomUpload', 'children'),
              [Input('CheckpointCustomUpload', 'filename')])
def CheckpointUploadConfirm(uploadFilename):
    if uploadFilename is None:
        return ['Drag and Drop or ', html.A('Select a File')]
    else:
        return uploadFilename


@app.callback(Output('JobSummary', 'children'),
              [Input('CustomJobName', 'value'),
               Input('CustomSHAList', 'value'),
               Input('YamlSelect', 'value'),
               Input('YamlCustomUpload', 'filename'),
               Input('YamlCustomUpload', 'contents'),
               Input('YamlAvailable', 'value'),
               Input('CheckpointSelect', 'value'),
               Input('CheckpointCustomUpload', 'filename'),
               Input('CheckpointCustomUpload', 'contents'),
               Input('CheckpointAvailable', 'value'),
               ])
def JobSummary(jobname, SHAs,
               yamlSelect, yamlFileName, yamlContent, yamlExisting,
               checkpointSelect, checkFileName, checkContent, checkExisting):

    summary = [html.H3('Jobname: ')]
    if jobname is not None:
        summary.append(html.P(jobname))
    else:
        summary.append(html.P('Job Name Missing', style={'color': 'red'}))

    summary.append(html.H3('Git SHAs to test: '))
    if SHAs is not None:
        goodSHAs = True
        for line in SHAs.splitlines():
            match = bool(re.match('[a-fA-F0-9]{40}$', line))
            if not match:
                summary.append(html.P(f'Bad SHA {line}', style={'color': 'red'}))
                goodSHAs = False
        if goodSHAs:
            summary.append(html.P(SHAs, style={'white-space': 'pre-line'}))
    else:
        summary.append(html.P('Git SHAs Missing', style={'color': 'red'}))

    summary.append(html.H3('Selected YAML Setup: '))
    if yamlSelect == 'uploaded':
        if yamlFileName is not None:
            summary.append(html.P(yamlFileName))
            summary.append(html.P(base64.b64decode(yamlContent.split(';base64,')[1].encode('utf-8')).decode('utf-8'), style={'white-space': 'pre-wrap'}))
        else:
            summary.append(html.P('Upload YAML File or select existing', style={'color': 'red'}))
    elif yamlSelect == 'existing':
        if yamlExisting is not None:
            yaml = Setup.objects.get(yamlHash=yamlExisting)
            summary.append(html.P(yaml.name))
            summary.append(html.P(yaml.yaml, style={'white-space': 'pre-wrap'}))
        else:
            summary.append(html.P('Upload YAML File or select existing', style={'color': 'red'}))

    if 'noCheckPoint' not in checkpointSelect:
        summary.append(html.H3('Selected Checkpoint: '))

        if checkpointSelect == 'uploaded':
            if checkFileName is not None:
                summary.append(html.P(checkFileName))
            else:
                summary.append(html.P('Upload Checkpoint File or select existing', style={'color': 'red'}))
        elif checkpointSelect == 'existing':
            if checkExisting is not None:
                checkpoint = Checkpoint.objects.get(id=checkExisting)
                summary.append(html.P(checkpoint.name))
            else:
                summary.append(html.P('Upload Checkpoint File or select existing', style={'color': 'red'}))

    return summary


# TODO: Submit Callback including validity checks for yamlHash etc. and feedback on submission
# TODO: Cancel Callback including feedback