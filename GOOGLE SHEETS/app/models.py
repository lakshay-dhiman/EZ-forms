
from .database import db
from flask_login import UserMixin

class Sheets(db.Model):
    __tablename__ = 'sheets'
    id = db.Column(db.Integer, primary_key = True)
    form_id = db.Column(db.Integer)
    sheet_url = db.Column(db.Text)
    user_id = db.Column(db.Text)
    sheet_id = db.Column(db.Text)


class Users(db.Model,UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Text, primary_key = True)
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)