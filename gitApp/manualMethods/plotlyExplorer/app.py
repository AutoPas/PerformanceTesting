import dash
import flask
import mongoengine as me
import os

me.connect('performancedb', host=os.environ['MONGOHOST'], username=os.environ['USERNAME'],
           password=os.environ['PASSWORD'])

server = flask.Flask(__name__)  # define flask app.server
app = dash.Dash(__name__, server=server)
