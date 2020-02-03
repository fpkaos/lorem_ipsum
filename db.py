import os
from flask import g
from flask_login import UserMixin
import mysql.connector as m
from werkzeug import generate_password_hash, check_password_hash, secure_filename

class DB:
    def __init__(self):
        self.app.teardown_appcontext(self.close_db)

    def connection(self):
        if 'db' not in g:
            g.db = self.connect()
        return g.db

    def connect(self):
        return m.connect(**self.config())

    def config(self):
        return {
            'user': self.app.config['MYSQL_USER'],
            'password': self.app.config['MYSQL_PASSWORD'],
            'host': self.app.config['MYSQL_HOST'],
            'database': self.app.config['MYSQL_DATABASE']
        }

    def close_db(self, e = None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

class Reg(DB):
    def is_exists(self):
        query = 'SELECT id FROM users WHERE login=%s'
        cursor = self.connection().cursor()
        cursor.execute(query, (self.login,))
        return bool(cursor.fetchone())

    def is_passwords_match(self):
        return bool(self.password == self.password_again)

    def create_user(self):
        cursor = self.connection().cursor()
        query = 'INSERT INTO users (login, password, full_name, role) VALUES (%s, %s, ".", 1)'
        cursor.execute(query, (self.login, self.password))
        self.connection().commit()

    def make_homedir(self):
        cursor = self.connection().cursor()
        query = 'SELECT id FROM users WHERE login=%s'
        cursor.execute(query, (self.login,))
        os.mkdir(f'/home/std/{cursor.fetchone()}')

    def __init__(self, login, password, password_again):
        self.login = login
        self.password = password
        self.password_again = password_again

        self.warn = 'User exists'
        self.success = False
        if not self.is_exists():
            if self.is_passwords_match():
                self.create_user()
                self.make_homedir()
                self.success = True
                return
            self.warn = 'Passwords doesn\'t match'
            return

class User(DB, UserMixin):
    def __init__(self, id=None, login=None, password=None):
        if id:
            query = 'SELECT id, password, login FROM users WHERE id=%s'
            cursor = self.connection().cursor()
            cursor.execute(query, (id,))
            try:
                self.id, self.password, self.login = cursor.fetchone()
                self.active = True
            except TypeError:
                return None

        elif login and password:
            query = 'SELECT id, password, login FROM users WHERE login=%s'
            cursor = self.connection().cursor()
            cursor.execute(query, (login,))
            try:
                self.id, self.password, self.login = cursor.fetchone()
                self.is_login = bool(self.password == password)
            except TypeError:
                self.is_login = False
        
    def save(self, doc):
        fs_name = secure_filename(doc.filename)
        doc.save(os.path.join(f'/home/std/{self.id}', fs_name))