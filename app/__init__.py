import MySQLdb
from flask import Flask

app = Flask(__name__)
app.config.from_object('config')


def connect_local_db():
    ldb = MySQLdb.connect(host="127.0.0.1", # your host, usually localhost
                         user=app.config['USERNAME'], # your username
                         passwd=app.config['PASSWORD'], # your password
                         db=app.config['LOCALDATABASE'], # name of the data base
                         port=3306)
    ldb.autocommit(0)
    return ldb

def connect_hq_db():
    hqdb = MySQLdb.connect(host="127.0.0.1", # your host, usually localhost
                         user=app.config['USERNAME'], # your username
                         passwd=app.config['PASSWORD'], # your password
                         db=app.config['HQDATABASE'], # name of the data base
                         port=3306)
    hqdb.autocommit(0)
    cur = hqdb.cursor()
    return hqdb


from app import views