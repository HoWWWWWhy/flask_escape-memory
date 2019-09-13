from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_admin import Admin
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('CLEARDB_DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['S3_BUCKET'] = os.environ.get("S3_BUCKET_NAME")
app.config['S3_KEY'] = os.environ.get("AWS_ACCESS_KEY_ID")
app.config['S3_SECRET'] = os.environ.get("AWS_SECRET_ACCESS_KEY")



db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "error"

# Admin Page
admin = Admin(app, name="Escape Memory's admin page")


from my_app import routes

if __name__ == '__main__':
    #app.run()# for Heroku
    #app.run(debug=True)# for development
    #app.run(host='0.0.0.0')
    app.debug = True
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port = port)    


