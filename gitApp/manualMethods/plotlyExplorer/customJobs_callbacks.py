from mongoDocuments import QueueObject, Checkpoint, Setup
from app import app
from globalVars import *

import hashlib
from datetime import datetime
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
            try:
                decoded_yaml = base64.b64decode(yamlContent.split(';base64,')[1].encode('utf-8')).decode('utf-8')
                yaml_color = 'black'
            except UnicodeDecodeError:
                decoded_yaml = 'BAD FILE'
                yaml_color = 'red'
            summary.append(html.P(decoded_yaml, style={'white-space': 'pre-wrap', 'color': yaml_color}))
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


@app.callback(Output('SubmitResponse', 'children'),
              [Input('submitJob', 'n_clicks')],
              [State('CustomJobName', 'value'),
               State('CustomSHAList', 'value'),
               State('YamlSelect', 'value'),
               State('YamlCustomUpload', 'filename'),
               State('YamlCustomUpload', 'contents'),
               State('YamlAvailable', 'value'),
               State('loginInfo', 'data')
               ])
def submitCallback(button, jobname, SHAs, yamlSelect, yamlUploadFileName, yamlUploadContent, yamlExisting, loginData):
    print('\n[CALLBACK] Submitting custom job')

    submitResponse = 'Submit Status:\n'

    if button == 0:
        return ''

    # Double Check log-in data. Button shouldn't even be visible if no user is logged in
    if loginData['user'] is None:
        return 'NO VALID USER LOGGED IN'

    # Check if jobname exists in db or is empty
    if jobname is None:
        return submitResponse + 'EMPTY JOB NAME'

    existing_jobnames = QueueObject.objects.distinct('job')
    if jobname in existing_jobnames:
        return submitResponse + 'JOB NAME ALREADY EXISTS'
    else:
        submitResponse += f'Job Name:\t{jobname}\n'

    # Check if Git SHAs are valid
    check_SHAs = []
    if SHAs is not None:
        for line in SHAs.splitlines():
            match = bool(re.match('[a-fA-F0-9]{40}$', line))
            if match:
                check_SHAs.append(line)
            else:
                return submitResponse + 'BAD SHA'
    else:
        return submitResponse + 'MISSING SHAs'

    # Existing YAML
    if yamlSelect == 'existing':
        if yamlExisting is not None:
            usedSetup = Setup.objects.get(yamlHash=yamlExisting)
            submitResponse += f'Yaml: {usedSetup.name}\n'
        else:
            return submitResponse + 'SELECT YAML'
    # Check yaml file if valid and if already uploaded via hash
    elif yamlSelect == 'uploaded':
        newSetup = Setup()
        newSetup.name = yamlUploadFileName
        decoded_yaml = base64.b64decode(yamlUploadContent.split(';base64,')[1].encode('utf-8')).decode('utf-8')
        # TODO: Strip white space before hashing / order lines
        yamlHash = hashlib.sha256(decoded_yaml.encode('utf-8')).hexdigest()
        newSetup.yamlHash = yamlHash
        existing_hashes = Setup.objects.distinct('yamlHash')
        if yamlHash in existing_hashes:
            del newSetup
            # TODO: Just select the corresponding setup
            return submitResponse + 'Trying to upload existing yaml. Please select from list instead of re-upload.'
        else:
            usedSetup = newSetup
            newSetup.active = False
            newSetup.uploadDate = datetime.utcnow()
            newSetup.save()  # This can lead to bad user experience if checkpoint upload fails
            submitResponse += f'Uploaded YAML: {yamlUploadFileName}'
    else:
        return 'BAD YAML SELECTION'

    # TODO: Check if checkpoint file is set / valid / uploaded

    # TODO: Kill setup if checkpoint fails

    # TODO: Upload Checkpoint to backend

    # TODO: Submit queue jobs
    for sha in check_SHAs:
        q = QueueObject()
        q.commitSHA = sha
        q.job = jobname
        q.customYaml = usedSetup
        q.jobuser = loginData['user']
        q.save()

    # TODO: Start worker

    return submitResponse


@app.callback(Output('CancelResponse', 'children'),
              [Input('cancelJob', 'n_clicks')],
              [State('CancelJobName', 'value'),
               State('loginInfo', 'data')])
def cancelCallback(button, jobname, loggedUser):
    print('\n[CALLBACK] Canceling custom job')

    cancelResponse = ''

    if button == 0:
        return ''

    if loggedUser['user'] is None:
        return 'Must be logged in to cancel jobs'

    # Check if jobs with jobname exist in queue
    existing_jobnames = QueueObject.objects.distinct('job')
    if jobname is not None and jobname in existing_jobnames:
        cancelResponse += f'Job {jobname} found.\n'
    else:
        return f'Job {jobname} is not in active Queue'

    # Cancel jobs
    objects = QueueObject.objects(job=jobname)
    num = len(objects)
    for q in objects:
        q.delete()

    cancelResponse += f'{num} tests deleted.'

    return cancelResponse
