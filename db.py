
from flask import g
from flask_login import UserMixin
import mysql.connector as m
from werkzeug.security import generate_password_hash, check_password_hash


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