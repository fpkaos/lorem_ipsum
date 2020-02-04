import logging
import flask
import flask_login
from flask_login import LoginManager, current_user, logout_user, login_user
from flask import request, session, redirect, url_for, render_template, send_from_directory
import db

logging.basicConfig(filename='/home/std/log', level=logging.DEBUG)

app = flask.Flask(__name__)
application = app
#change path to your config file
app.config.from_pyfile('../config.py')
db.DB.app = app

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.anonymous_user = db.Anonymous

def ext(filename):
    return filename.rsplit('.', 1)[1]

@login_manager.user_loader
def load_user(user_id):
    return db.User(id=user_id)

@app.route('/', methods=['GET'])
def index():
    logging.info(current_user)
    return render_template('index.html', docs=current_user.main_table())

@app.route('/', methods=['POST'])
def reg():
    login = request.form['login']
    password = request.form['password']
    password_again = request.form['password_again']

    reg = db.Reg(login, password, password_again)
    if reg.success:
        user = db.User(login=login, password=password)
        login_user(user)
        return redirect(url_for('account', id=user.id))
    else:
        return redirect(url_for('index', warn=reg.warn))

@flask_login.login_required
@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/sign_in', methods=['GET'])
def sign_in():
    return render_template('sign_in.html')

@app.route('/sign_in', methods=['POST'])
def auth():
    user = db.User(login=request.form['login'], 
                    password=request.form['password'])
    if user.is_login:
        login_user(user)
        return redirect(url_for('account', id=user.id))
    else:
        return render_template('sign_in.html', 
                                warn='Incorrect login or password')

@flask_login.login_required
@app.route('/account/<int:id>/', methods=['GET'])
def account(id):
    if current_user.id == id:
        return render_template('account.html', docs=current_user.get_files())
    flask.abort(404)

@flask_login.login_required
@app.route('/account/<int:id>/', methods=['POST'])
def file_managment(id):
    doc = request.files.get('new_doc')
    if doc:
        ext = ext(doc.filename)
        #mv to the config
        allowed = bool(ext in {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}) 
        if allowed:
            current_user.save(doc, ext)
    return redirect(url_for('account', id=id))
    
@app.route('/download/<int:id>/<filename>')
def download(id, filename):
    doc = db.File(id, filename)
    doc.get_visibility()
    if doc.visibility:
        return send_from_directory(f'/home/std/{id}', filename)
    try:
        if current_user.id == id:
            return send_from_directory(f'/home/std/{id}', filename)
    except AttributeError:
            abort(404)

@flask_login.login_required
@app.route('/delete/<int:id>/<filename>')
def delete(id, filename):
    if current_user.id == id:
        f = db.File(id, filename)
        current_user.delete(f)
        return redirect(url_for('account', id=id, msg='File deleted'))
    abort(404)

@flask_login.login_required
@app.route('/change_visibility/<int:id>/<filename>')
def vis(id, filename):
    if current_user.id == id:
        db.File(id, filename).switch(int(request.args.get('val')))
        return redirect(url_for('account', id=id, msg='Visibility changed'))
    abort(404)

@flask_login.login_required
@app.route('/edit/<int:id>/<filename>', methods=['GET'])
def edit(id, filename):
    if current_user.id == id:
        doc = db.File(id, filename)
        doc.get_human_name()
        doc.get_description()
        return render_template('edit.html', doc=doc)
    abort(404)

@flask_login.login_required
@app.route('/edit/<int:id>/<filename>', methods=['POST'])
def edit_post(id, filename):
    if current_user.id == id:
        doc = db.File(id, filename)
        doc.update_description(request.form.get('description'))
        return redirect(url_for('account', id=id, msg='File changed'))
    abort(404)

@flask_login.login_required
@app.route('/upvote/<int:fid>/')
def upvote(fid):
    current_user.upvote(fid)
    return redirect(url_for('index'))

@flask_login.login_required
@app.route('/downvote/<int:fid>/')
def downvote(fid):
    current_user.downvote(fid)
    return redirect(url_for('index'))
