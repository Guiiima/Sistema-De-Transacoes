from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dataclasses import dataclass
import requests

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///validadores.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

@dataclass
class Validador(db.Model):
    id: int
    saldo: float
    flags: int
    validacoes: int
    transacoes_corretas: int
    hold: bool
    hold_expires: int
    ip: str

    id = db.Column(db.Integer, primary_key=True)
    saldo = db.Column(db.Float)
    flags = db.Column(db.Integer)
    validacoes = db.Column(db.Integer)
    transacoes_corretas = db.Column(db.Integer)
    hold = db.Column(db.Boolean)
    hold_expires = db.Column(db.Integer)
    ip = db.Column(db.String(30), nullable=False)

with app.app_context():
    db.create_all()

app.run(host='0.0.0.0', debug=True)