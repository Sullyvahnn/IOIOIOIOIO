from flask import Blueprint, render_template, session, flash
from flask_jwt_extended import decode_token
from jwt import ExpiredSignatureError, InvalidTokenError

main = Blueprint('main', __name__)

@main.route('/')
def home():
    token = session.get('access_token')
    user_email = None

    if token:
        try:
            decoded = decode_token(token)
            user_email = decoded.get('sub')  # 'sub' = identity set in JWT
        except ExpiredSignatureError:
            flash("Session expired. Please log in again.", "error")
            session.pop('access_token', None)
        except InvalidTokenError:
            flash("Invalid session token.", "error")
            session.pop('access_token', None)

    return render_template('main.html', user_email=user_email)

@main.route('/login')
def login():
    return render_template("login.html")

@main.route('/register')
def register():
    return render_template("register.html")

@main.route('/forgot')
def forgot():
    return render_template("forgot.html")