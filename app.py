from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


app = Flask(__name__)
app.config["SECRET_KEY"] = "my-security-key"
# Use an absolute path to ensure the database is always in the project folder
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "mybank.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)

login = LoginManager()
login.init_app(app)


from routes import *

if __name__ == '__main__':
    app.run(debug=True)
