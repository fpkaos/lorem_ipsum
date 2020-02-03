import flask
import flask_login
from flask import Flask, request, session, redirect, url_for, render_template

app = Flask(__name__)
application = app

app.config.from_pyfile('config.py')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def reg():
    return render_template('index.html')

@app.route('/sign_in', methods=['GET'])
def sign_in():
    return render_template('sign_in.html')

@app.route('/sign_in', methods=['POST'])
def auth():
    return redirect(url_for('account'))

@app.route('/account', methods=['GET'])
def account():
    return render_template('account.html')
