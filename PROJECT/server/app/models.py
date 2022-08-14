
from email.policy import default
from flask_sqlalchemy.model import Model
from flask_login import UserMixin
from flask_sqlalchemy.model import Model
from .database import db

class Users(db.Model,UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Text, primary_key = True)
    email = db.Column(db.String(30), unique=True, nullable = False)
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)

class Forms(db.Model):
    __tablename__ = 'forms'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Text, db.ForeignKey('users.id'))
    form_title = db.Column(db.Text)
    form_url = db.Column(db.Text)
    google_sheets = db.Column(db.Integer,default=0)
    sheet_url = db.Column(db.Text, default='not_available')

class Fields(db.Model):
    __tablename__ = 'fields'
    id =  db.Column(db.Integer, primary_key = True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'))
    type = db.Column(db.Integer)
    name = db.Column(db.Text)

class Subfield_names(db.Model):
    __tablename__ = 'subfield_names'
    id = db.Column(db.Integer, primary_key = True)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'))
    title = db.Column(db.Text)

class Response_event(db.Model):
    __tablename__ = 'response_event'
    id = db.Column(db.Integer, primary_key = True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'))

class Responses(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key = True)
    field_id =db.Column(db.Integer, db.ForeignKey('fields.id'))
    response_event_id = db.Column(db.Integer, db.ForeignKey('response_event.id'))

class Number_values(db.Model):
    __tablename__ = 'number_values'
    id = db.Column(db.Integer, primary_key = True)
    response_id =db.Column(db.Integer, db.ForeignKey('responses.id'))
    value = db.Column(db.Integer)

class Text_values(db.Model):
    __tablename__ = 'text_values'
    id = db.Column(db.Integer, primary_key = True)
    response_id =db.Column(db.Integer, db.ForeignKey('responses.id'))
    value = db.Column(db.Text)

