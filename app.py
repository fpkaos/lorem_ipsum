import logging
import os
import flask
import flask_login
from werkzeug.utils import secure_filename
from flask import request, session, redirect, url_for, render_template, send_from_directory
import utils

app = flask.Flask(__name__)
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

@app.route('/account/<int:id>/', methods=['GET'])
def account(id):
    if True: #session['id'] == id
        return render_template('account.html')
    flask.abort(404)

@app.route('/account/<int:id>/', methods=['POST'])
def file_managment(id):
    logging.info(request.files.get('new-doc'))
    doc = request.files.get('new-doc')
    if doc and utils.allowed_file(doc.filename):
        fs_name = secure_filename(doc.filename)
        #replace /home/std/ to session['home']
        doc.save(os.path.join(f'/home/std/{id}', fs_name))
    return render_template('account.html')

@app.route('/account/<int:id>/<filename>')
def uploaded_file(filename):
    return send_from_directory('/home/std/',filename)
