import os
import random
from flask import g
from flask_login import UserMixin, AnonymousUserMixin
import mysql.connector as m
from werkzeug import generate_password_hash, check_password_hash, secure_filename

import logging

logging.basicConfig(filename='/home/std/log',level=logging.DEBUG)

def unic_filename():
    return hex(random.randint(10**10, 10**20)).strip('0x')

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

    def main_table(self):
        query = '''
        SELECT service_users.id owner, fs_name, name, visibility, description, votes, login, files.id fid FROM `files` INNER JOIN `service_users` ON files.owner = service_users.id INNER JOIN sum_votes ON files.id = sum_votes.fid WHERE files.visibility = 1 ORDER BY votes DESC
        '''
        cursor = self.connection().cursor()
        cursor.execute(query)
        return [File(*i) for i in cursor.fetchall()]


class File(DB):
    def __init__(self, owner, fs_name, name=None, visibility=0, description=None, votes=None, login=None, fid=None):
        self.fs_name = fs_name
        self.name = name
        self.owner = owner
        self.visibility = visibility
        self.description = description
        self.votes = votes
        self.login = login
        self.fid = fid
    
    def download_info():
        query = 'SELECT visibility FROM files WHERE owner=%s AND fs_name=%s'
        cursor = self.connection().cursor()
        cursor.execute(query, (self.owner, self.fs_name))
        self.visibility = cursor.fetchone()[0]

    def switch(self, val):
        if val in range(0,2):
            query = 'UPDATE files SET visibility=%s WHERE owner=%s AND fs_name=%s'
            cursor = self.connection().cursor()
            cursor.execute(query, (val, self.owner, self.fs_name))
            self.connection().commit()

    def get_human_name(self):
        query = 'SELECT name FROM files WHERE owner=%s AND fs_name=%s'
        cursor = self.connection().cursor()
        cursor.execute(query, (self.owner, self.fs_name))
        self.name = cursor.fetchone()[0]

    def get_description(self):
        query = 'SELECT description FROM files WHERE owner=%s AND fs_name=%s'
        cursor = self.connection().cursor()
        cursor.execute(query, (self.owner, self.fs_name))
        self.description = cursor.fetchone()[0]

    def get_visibility(self):
        query = 'SELECT visibility FROM files WHERE owner=%s AND fs_name=%s'
        cursor = self.connection().cursor()
        cursor.execute(query, (self.owner, self.fs_name))
        self.visibility = cursor.fetchone()[0]

    def update_description(self, description):
        query = 'UPDATE files SET description=%s WHERE owner=%s AND fs_name=%s'
        logging.info(description)
        if description:
            cursor = self.connection().cursor()
            cursor.execute(query, (description, self.owner, self.fs_name))
            self.connection().commit()
            

class Reg(DB):
    def is_exists(self, login):
        query = 'SELECT id FROM service_users WHERE login=%s'
        cursor = self.connection().cursor()
        cursor.execute(query, (login,))
        return bool(cursor.fetchone())

    def is_passwords_match(self, password, password_again):
        return bool(password == password_again)

    def create_user(self, login, password):
        cursor = self.connection().cursor()
        query = 'INSERT INTO service_users (login, password) VALUES (%s, %s)'
        cursor.execute(query, (login, password))
        self.connection().commit()

    def make_homedir(self, login):
        cursor = self.connection().cursor()
        query = 'SELECT id FROM service_users WHERE login=%s'
        cursor.execute(query, (login,))
        os.mkdir(f'/home/std/{cursor.fetchone()[0]}')

    def __init__(self, login, password, password_again):
        self.warn = 'User exists'
        self.success = False
        if not self.is_exists(login):
            if self.is_passwords_match(password, password_again):
                self.create_user(login, generate_password_hash(password))
                self.make_homedir(login)
                self.success = True
                return
            self.warn = 'Passwords doesn\'t match'
            return

class Anonymous(DB, AnonymousUserMixin):
    def __init__(self):
        pass

class User(DB, UserMixin):
    def __init__(self, id=None, login=None, password=None):
        if id:
            query = 'SELECT * FROM service_users WHERE id=%s'
            cursor = self.connection().cursor()
            cursor.execute(query, (id,))
            try:
                self.id, self.login, self.password = cursor.fetchone()
                self.active = True
                self.get_voted()
            except TypeError:
                return None

        elif login and password:
            query = 'SELECT * FROM service_users WHERE login=%s'
            cursor = self.connection().cursor()
            cursor.execute(query, (login,))
            try:
                self.id, self.login, self.password = cursor.fetchone()
                self.is_login = check_password_hash(self.password, password)
                self.get_voted()
            except TypeError:
                self.is_login = False

    def insert_file(self, doc, fs_name):
        query = 'INSERT INTO files (fs_name, name, visibility, description, owner) VALUES (%s, %s, %s, %s, %s)'
        cursor = self.connection().cursor()
        values = (fs_name, secure_filename(doc.filename), 0, '', self.id)
        cursor.execute(query, values)
        self.connection().commit()

    def get_fid(self, fs_name):
        cursor = self.connection().cursor()
        query = 'SELECT id FROM files WHERE owner=%s AND fs_name=%s'
        cursor.execute(query, (self.id, fs_name))
        return cursor.fetchone()[0]

    def init_votes(self, fid):
        cursor = self.connection().cursor()
        query = 'INSERT INTO `votes`(`vote`, `voter`, `doc`) VALUES (%s, %s, %s)'
        cursor.execute(query, (0, self.id, fid))
        self.connection().commit()

    def make_fs_name(self, ext):
        fs_name = unic_filename()
        files = os.listdir(f'/home/std/{self.id}')
        while fs_name in files:
            fs_name = unic_filename() 
        return '.'.join([fs_name, ext])

    def save(self, doc, ext):
        fs_name = self.make_fs_name(ext)
        doc.save(os.path.join(f'/home/std/{self.id}', fs_name))
        self.insert_file(doc, fs_name)
        self.init_votes(self.get_fid(fs_name))

    def get_files(self):
        query = 'SELECT fs_name, name, visibility, description FROM files WHERE owner=%s'
        cursor = self.connection().cursor()
        cursor.execute(query, (self.id,))
        return [File(self.id, *i) for i in cursor.fetchall()]

    def delete(self, f):
        os.remove(f'/home/std/{self.id}/{f.fs_name}')
        query = 'DELETE FROM votes WHERE doc=%s'
        cursor = self.connection().cursor()
        cursor.execute(query, (f.fid,))
        self.connection().commit()

        query = 'DELETE FROM files WHERE owner=%s AND fs_name=%s'
        cursor = self.connection().cursor()
        cursor.execute(query, (self.id, f.fs_name))
        self.connection().commit()

    def get_voted(self):
        query = 'SELECT doc fid, vote FROM votes WHERE voter = %s'
        cursor = self.connection().cursor(named_tuple = True)
        cursor.execute(query, (self.id,))
        self.voted = dict(cursor.fetchall())

    def upvote(self, fid):
        if self.voted.get(fid) in range(-1,2):
            query = 'UPDATE votes SET vote=%s WHERE voter=%s AND doc=%s'
        else:
            query = 'INSERT INTO votes VALUES (%s, %s, %s)'
        cursor = self.connection().cursor()
        cursor.execute(query, (1, self.id, fid))
        self.connection().commit()


    def downvote(self, fid):
        if self.voted.get(fid) in range(-1,2):
            query = 'UPDATE votes SET vote=%s WHERE voter=%s AND doc=%s'
        else:
            query = 'INSERT INTO votes VALUES (%s, %s, %s)'
        cursor = self.connection().cursor()
        cursor.execute(query, (-1, self.id, fid))
        self.connection().commit()