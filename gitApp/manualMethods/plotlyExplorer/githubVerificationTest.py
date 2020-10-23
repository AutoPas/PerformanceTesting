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
    html.Button('Submit Job', id='submitButton', n_clicks=0)
])


@app.callback(Output('outP', 'children'),
              [Input('loc', 'search')])
def showLoc(loc):
    try:
        code = re.findall('code=([^;&]+)', loc)[0]
    except IndexError:
        return f'no valid code {loc}'
    # Get Access Token
    r = requests.post('https://github.com/login/oauth/access_token', data={'client_id': os.environ['CLIENT_ID'],
                                                                           'client_secret': os.environ['CLIENT_SECRET'],
                                                                           'code': code,
                                                                           'redirect_uri': 'http://localhost:8050'})
    print(r.text)
    try:
        token = re.findall('token=([^;&]+)', r.text)[0]
    except IndexError:
        return f'bad access token: {r.text}'

    # Check User Name
    r = requests.get('https://api.github.com/user', headers={'Authorization': f'token {token}'})
    user = r.json()['login']
    print(user)
    r = requests.get(f'https://api.github.com/repos/AutoPas/AutoPas/collaborators/{user}', headers={'Authorization': f'token {token}',
                                                                    'Accept': 'application/vnd.github.v3+json'})
    if r.status_code == 204:
        return f'Congrats {user}, you can submit jobs'
    else:
        return f'Error {r.status_code} {r.text}'


@app.callback(Output('loc', 'href'),
              [Input('submitButton', 'n_clicks')])
def submit(button):
    if button != 0:
        return f'https://github.com/login/oauth/authorize/?client_id={os.environ["CLIENT_ID"]}&redirect_uri=http://localhost:8050'


if __name__ == '__main__':
    app.run_server(debug=True)