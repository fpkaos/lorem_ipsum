import flask
import flask_login
from flask import Flask, request, session, redirect, url_for, render_template

app = Flask(__name__)
application = app
app.debug = True
#app.config.from_pyfile('config.py')

@app.route('/')
def index():
    return render_template('index.html')