from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.routes.user import get_current_user
from models import db, Cabin, User
from sqlalchemy.exc import SQLAlchemyError

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/add-cabin', methods=['POST'])
@jwt_required()
def add_cabin():
    identity = get_current_user()
    if identity is None or not identity.is_admin:
        return jsonify({'error': 'Unauthorized'}), 400

    data = request.json
    try:
        new_cabin = Cabin(
            name=data['name'],
            capacity=data['capacity'],
        )
        db.session.add(new_cabin)
        db.session.commit()
        return jsonify({'message': 'Cabin added successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 200

@admin_bp.route('/remove-cabin', methods=['POST'])
@jwt_required()
def remove_cabin():
    identity = get_jwt_identity()
    if identity is None or identity != "admin@admin.com":
        return jsonify({'error': 'Unauthorized'}), 400

    cabin_id = request.json.get('id')
    cabin = Cabin.query.get(cabin_id)
    if not cabin:
        return jsonify({'error': 'Cabin not found'}), 400

    #todo remove cabin from user

    try:
        db.session.delete(cabin)
        db.session.commit()
        return jsonify({'message': 'Cabin removed successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/edit-cabin', methods=['POST'])
@jwt_required()
def edit_cabin():
    identity = get_jwt_identity()
    if identity is None or identity != "admin@admin.com":
        return jsonify({'error': 'Unauthorized'}), 400

    data = request.json
    cabin = Cabin.query.get(data.get('id'))
    if not cabin:
        return jsonify({'error': 'Cabin not found'}), 400

    try:
        cabin.name = data.get('name', cabin.name)
        cabin.capacity = data.get('capacity', cabin.capacity)
        db.session.commit()
        return jsonify({'message': 'Cabin updated successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    identity = get_jwt_identity()
    if identity is None or not identity.is_admin:
        return jsonify({'error': 'Unauthorized'}), 400

    users = User.query.all()
    user_dicts = []
    for user in users:
        user_dicts.append(user.to_dict())
    return jsonify(user_dicts), 200

@admin_bp.route('/delete-user', methods=['POST'])
@jwt_required()
def delete_user():
    identity = get_jwt_identity()
    if identity is None or not identity.is_admin:
        return jsonify({'error': 'Unauthorized'}), 400

    user_id = request.json.get('id')
    user = User.query.get(user_id)
    if user.is_admin:
        return jsonify({'error': 'Cannot delete admin'})
    if not user:
        return jsonify({'error': 'User not found'}), 400

    #todo remove him from cabin

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route("unlock/<int:cabin_id>", methods=["POST"])
@jwt_required()
def admin_unlock_cabin(cabin_id):
    current_user = get_current_user()
    if current_user is None or not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 400

    cabin = db.session.query(Cabin).get(cabin_id)
    if not cabin:
        return jsonify({'error': 'Cabin not found'}), 400

    cabin.is_locked = not cabin.is_locked
    cabin.unlock_time = None
    db.session.commit()

    return jsonify({"Success": f"Cabin {cabin.name} unlocked manually."}), 200

@admin_bp.route("schedule-unlock/<int:cabin_id>", methods=["POST"])
@jwt_required()
def schedule_unlock_time(cabin_id):
    current_user = get_current_user()
    if current_user is None or not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 400

    data = request.get_json()
    unlock_time_str = data.get("unlock_time")  # Expecting ISO 8601 format

    try:
        unlock_time = datetime.fromisoformat(unlock_time_str)
    except Exception:
        return jsonify({'error': 'Invalid unlock time'}), 400

    cabin = db.session.query(Cabin).get(cabin_id)
    if not cabin:
        return jsonify({'error': 'Cabin not found'}), 400

    cabin.unlock_time = unlock_time
    cabin.is_locked = True
    db.session.commit()

    return jsonify({"Success": f"Unlock time set for cabin {cabin.name}."}), 200

