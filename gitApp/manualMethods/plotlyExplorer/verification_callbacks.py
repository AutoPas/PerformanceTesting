from app import app
from globalVars import *

import requests
import re
import os
import dash
from dash.dependencies import Input, Output, State, ALL


@app.callback([Output('loginResponse', 'children'),
               Output('loginButton', 'children'),
               Output('submissionDiv', 'style')],
              [Input('loginInfo', 'data')])
def showStatusAndLoginOption(data):
    if data['user'] is None:
        if data['status'] is None:
            return ['Please login via GitHub', 'Login', {'display': 'none'}]
        else:
            return [f'Please login via GitHub ({data["status"]})', 'Login', {'display': 'none'}]
    else:
        return [f'Logged in as: {data["user"]}', 'Logout', {'display': 'block'}]


@app.callback(Output('loc', 'href'),
              [Input('loginButton', 'n_clicks')],
              [State('loginInfo', 'data')])
def loginButton(button, data):
    if button != 0 and data['user'] is None:
        return f'https://github.com/login/oauth/authorize/?client_id={os.environ["CLIENT_ID"]}&redirect_uri={os.environ["CALLBACK_URI"]}'


@app.callback(Output('loginInfo', 'data'),
              [Input('loc', 'search'),
               Input('loginButton', 'n_clicks')],
              [State('loginInfo', 'data')])
def processGitLogin(loc, button, data):
    ctx = dash.callback_context

    triggered = ctx.triggered[0]['prop_id']
    if 'loginButton' in triggered and data['user'] is not None:
        return {'user': None, 'status': f'Logged out {data["user"]}'}

    if loc is None or loc is '' or data['user'] is not None:
        return data

    noUser = {'user': None}
    try:
        code = re.findall('code=([^;&]+)', loc)[0]
    except IndexError:
        print(f'no valid code {loc}')
        noUser['status'] = 'Not authorized yet, try again'
        return noUser
    # Get Access Token
    r = requests.post('https://github.com/login/oauth/access_token', data={'client_id': os.environ['CLIENT_ID'],
                                                                           'client_secret': os.environ['CLIENT_SECRET'],
                                                                           'code': code,
                                                                           'redirect_uri': os.environ["CALLBACK_URI"]})
    print(r.text)
    try:
        token = re.findall('token=([^;&]+)', r.text)[0]
    except IndexError:
        print(f'bad access token: {r.text}')
        noUser['status'] = 'Bad Access Token, try again'
        return noUser

    # Check User Name
    r = requests.get('https://api.github.com/user', headers={'Authorization': f'token {token}'})
    user = r.json()['login']
    print(user)
    r = requests.get(f'https://api.github.com/repos/AutoPas/AutoPas/collaborators/{user}', headers={'Authorization': f'token {token}',
                                                                    'Accept': 'application/vnd.github.v3+json'})
    if r.status_code == 204:
        print(f'Congrats {user}, you can submit jobs')
        return {'user': user, 'status': None}
    else:
        print(f'Error {r.status_code} {r.text}')
        noUser['status'] = f'Insufficient Privileges on AutoPas for user: {user}'
        return noUser
