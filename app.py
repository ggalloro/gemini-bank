from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager



app = Flask(__name__)
app.config["SECURITY_KEY"] = "my-security-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mybank.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)

login = LoginManager()
login.init_app(app)
