import re
from flask_mail import Message
from flask import Blueprint, current_app as app, request, jsonify
from itsdangerous import URLSafeTimedSerializer
from app import mail
from flask_jwt_extended import create_access_token

auth = Blueprint('auth', __name__)

class UnvalidMailException(Exception):
    def __init__(self, message):
        super(UnvalidMailException, self).__init__(message)


class UnvalidTokenException(Exception):
    def __init__(self, message):
        super(UnvalidTokenException, self).__init__(message)


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['EMAIL_CONFIRM_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['EMAIL_CONFIRM_SALT'],
            max_age=expiration
        )
    except Exception as e:
        raise UnvalidTokenException("Can't authorize groupCode")
    return email


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(pattern, email):
        raise UnvalidMailException('Invalid email address')


@auth.route('/request-code', methods=['POST'])
def request_code():
    email = request.get_json().get('email')
    try:
        is_valid_email(email)
    except UnvalidMailException as ex:
        return jsonify({'error': 'Invalid email address'}), 400

    token = generate_confirmation_token(email)
    msg = Message(
        subject="Verify your registration code",
        sender=app.config['MAIL_USERNAME'],
        recipients=[email],
    )
    msg.body = token
    try:
        mail.send(msg)
        return jsonify({'Success': 'Email sent successfully'}), 200
    except Exception as ex:
        return jsonify({'Error': ex}), 400


@auth.route('/confirm-code', methods=['POST'])
def confirm():
    token = request.get_json().get('token')
    try:
        email = confirm_token(token)
    except UnvalidTokenException as ex:
        return jsonify({'error': 'Invalid confirmation code'}), 400
    access_token = create_access_token(identity=email)
    return jsonify({"token": access_token}), 200