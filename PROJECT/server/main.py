from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
app.config['SECRET_KEY'] = 'sakujotitla'
app.config['JSON_SORT_KEYS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

from app.database import db
db.init_app(app)


CORS(app)

app.app_context().push()


from app.controler import *

if __name__ == '__main__':
    app.run(debug=True,host = '127.0.0.1',port = 8081)