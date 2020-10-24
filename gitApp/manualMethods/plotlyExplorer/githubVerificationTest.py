import requests
import re
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='Hello Nobody'),
    dcc.Location(id='loc'),
    html.P(id='outP'),
    html.Button('Login', id='loginButton', n_clicks=0),
    dcc.Store(id='loginInfo', storage_type='session', data={'user': None, 'status': None}),
])


@app.callback([Output('outP', 'children'),
               Output('loginButton', 'children')],
              [Input('loginInfo', 'data')])
def showStatusAndLoginOption(data):
    if data['user'] is None:
        if data['status'] is None:
            return ['Please login via GitHub', 'Login']
        else:
            return [f'Please login via GitHub ({data["status"]})', 'Login']
    else:
        return [f'Logged in as: {data["user"]}', 'Logout']


@app.callback(Output('loc', 'href'),
              [Input('loginButton', 'n_clicks')],
              [State('loginInfo', 'data')])
def loginButton(button, data):
    if button != 0 and data['user'] is None:
        return f'https://github.com/login/oauth/authorize/?client_id={os.environ["CLIENT_ID"]}&redirect_uri=http://localhost:8050'


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
        noUser['status'] = 'Not authorized yet'
        return noUser
    # Get Access Token
    r = requests.post('https://github.com/login/oauth/access_token', data={'client_id': os.environ['CLIENT_ID'],
                                                                           'client_secret': os.environ['CLIENT_SECRET'],
                                                                           'code': code,
                                                                           'redirect_uri': 'http://localhost:8050'})
    print(r.text)
    try:
        token = re.findall('token=([^;&]+)', r.text)[0]
    except IndexError:
        print(f'bad access token: {r.text}')
        noUser['status'] = 'Bad Access Token'
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


# @app.callback(Output('loginInfo', 'data'),
#               [Input('loginButton', 'n_clicks')],
#               [State('loginInfo', 'data')])
# def logout(button, data):
#     if button != 0 and data is not None:
#         return {'user': None}
#     else:
#         return data


if __name__ == '__main__':
    app.run_server(debug=True)