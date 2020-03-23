from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from app.dbconfig import config

app = Flask(__name__)
# DB_URL = 'sqlite:///stock.db'

# for heroku PostgreSQL
DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}:{port}/{db}'.format(user=config["user"], pw=config["pwd"],
                                                                      url=config["url"], port=config["port"],
                                                                      db=config["db"])
# postgres://{user}:{password}@{url}:{port}/{db}


app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

from app import views
