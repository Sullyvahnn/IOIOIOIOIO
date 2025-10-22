from datetime import timedelta
from models import addUser
from flask_mail import Message
from flask import Blueprint, current_app as app, request, jsonify, redirect, url_for, flash, session
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

from app import mail
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, db

auth = Blueprint('auth', __name__)

# class UnvalidMailException(Exception):
#     def __init__(self, message):
#         super(UnvalidMailException, self).__init__(message)
#
#
# class UnvalidTokenException(Exception):
#     def __init__(self, message):
#         super(UnvalidTokenException, self).__init__(message)
#
#
# def generate_confirmation_token(email):
#     serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
#     return serializer.dumps(email, salt=app.config['EMAIL_CONFIRM_SALT'])
#
#
# def confirm_token(token, expiration=3600):
#     serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
#     try:
#         email = serializer.loads(
#             token,
#             salt=app.config['EMAIL_CONFIRM_SALT'],
#             max_age=expiration
#         )
#     except Exception as e:
#         raise UnvalidTokenException("Can't authorize groupCode")
#     return email
#
#
# def is_valid_email(email):
#     pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
#     if not re.match(pattern, email):
#         raise UnvalidMailException('Invalid email address')
#
#
# @auth.route('/request-code', methods=['POST'])
# def request_code():
#     email = request.get_json().get('email')
#     try:
#         is_valid_email(email)
#     except UnvalidMailException as ex:
#         return jsonify({'error': 'Invalid email address'}), 400
#
#     token = generate_confirmation_token(email)
#     msg = Message(
#         subject="Verify your registration code",
#         sender=app.config['MAIL_USERNAME'],
#         recipients=[email],
#     )
#     msg.body = token
#     try:
#         mail.send(msg)
#         return jsonify({'Success': 'Email sent successfully'}), 200
#     except Exception as ex:
#         return jsonify({'Error': ex}), 400
#
#
# @auth.route('/confirm-code', methods=['POST'])
# def confirm():
#     token = request.get_json().get('token')
#     try:
#         email = confirm_token(token)
#     except UnvalidTokenException as ex:
#         return jsonify({'error': 'Invalid confirmation code'}), 400
#     access_token = create_access_token(identity=email)
#     return jsonify({"token": access_token}), 200


@auth.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        flash("Email and password are required.", "error")
        return redirect(url_for('main.register'))

    existing_user = User.query.filter_by(Login=email).first()
    if existing_user:
        flash("User already exists.", "error")
        return redirect(url_for('main.register'))

    hashed_password = generate_password_hash(password)
    addUser(email, hashed_password, name="", stanowisko="")

    flash("Registration successful! You can now log in.", "success")
    return redirect(url_for('main.login'))


# ----------------------------
# LOGIN ROUTE
# ----------------------------
@auth.route('/login', methods=['POST'])
def login():
    data = request.form.to_dict()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        flash("Email and password are required.", "error")
        return redirect(url_for('main.login'))

    user = User.query.filter_by(Login=email).first()
    if not user or not check_password_hash(user.Password, password):
        flash("Wrong password or mail.", "error")
        return redirect(url_for('main.login'))

    session['access_token'] = create_access_token(identity=email, expires_delta=timedelta(days=1))
    return redirect(url_for('main.home'))

@auth.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_email = get_jwt_identity()
    return jsonify({"email": user_email}), 200
