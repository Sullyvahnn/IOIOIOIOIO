import random
import string
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User

user_bp = Blueprint('user', __name__)


def get_current_user():
    current_user = db.session.query(User).filter_by(email=get_jwt_identity()).first()
    if current_user is None:
        return None
    return current_user


def generate_group_token():
    characters = string.ascii_letters + string.digits
    while True:
        token = ''.join(random.choice(characters) for _ in range(8))
        if db.session.query(User).filter(User.groupCode == token).count() == 0:
            break
    return token


@user_bp.route("/create", methods=['POST'])
@jwt_required()
def create_user():
    user_request = request.get_json()
    email = user_request['email']
    role = email == 'admin@admin.com'

    if db.session.query(User).filter_by(email=email).first():
        return jsonify({'error': 'There is already a user with that email'}), 400

    user = User(
        name=user_request['name'],
        email=user_request['email'],  # ⚠️ Note: still unsafe until validation added
        groupCode=generate_group_token(),
        is_admin=role
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': f'user {user.name} created'}), 200


@user_bp.route("/change-code", methods=['POST'])
@jwt_required()
def change_user_code():
    change_code_request = request.get_json()
    code = change_code_request.get('groupCode')
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'You are not logged in'}), 400

    current_user.groupCode = code
    db.session.commit()
    return jsonify({'success': f'user {current_user.name} code changed'}), 200


@user_bp.route("/group", methods=['GET'])
@jwt_required()
def view_user_group():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'You are not logged in'}), 400

    group = db.session.query(User).filter_by(groupCode=current_user.groupCode).all()
    group_names = [user.name for user in group]
    return jsonify({'success': group_names}), 200


@user_bp.route("/<int:user_id>", methods=['GET'])
@jwt_required()
def get_user_by_id(user_id):
    user = db.session.query(User).get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user.to_dict()), 200

@user_bp.route("/current-user", methods=['GET'])
@jwt_required()
def get_logged_in_user():
    identity = get_jwt_identity()
    if not identity:
        return jsonify({'error': 'Token is invalid or expired'}), 401

    user = db.session.query(User).filter_by(email=identity).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user.to_dict()), 200



@user_bp.route('/user/email', methods=['GET'])
@jwt_required()
def get_user_email():
    identity = get_jwt_identity()  # This is whatever you passed when creating the JWT
    return jsonify({'email': identity}), 200
