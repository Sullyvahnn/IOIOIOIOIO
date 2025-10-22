from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from models import Cabin, User
from models import db
from app.routes.user import get_current_user

cabins_bp = Blueprint('cabins', __name__)


def reserve_cabin(cabin_id, member_id):
    try:
        cabin = db.session.query(Cabin).with_for_update().filter(Cabin.id == cabin_id).first()

        if cabin.is_locked:
            return {"status": "failed", "reason": "cabin is locked"}

        if not cabin:
            return {'status': 'failed', 'reason': 'Cabin not found'}

        cabin.add_member(member_id)
        return {'status': 'success', 'cabin_id': cabin_id, 'member_id': member_id}
    except IntegrityError:
        db.session.rollback()
        return {'status': 'failed', 'reason': 'Database constraint violation'}
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'reason': str(e)}


def leave_cabin(user: User):
    cabin_id = user.cabin_id
    user_id = user.id
    try:
        cabin = db.session.query(Cabin).with_for_update().filter(Cabin.id == cabin_id).first()

        if not cabin:
            return {'status': 'failed', 'reason': 'Cabin not found'}

        cabin.remove_member(user_id)
        return {'status': 'success'}
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'reason': str(e)}


@cabins_bp.route('/reserve', methods=['POST'])
@jwt_required()
def reserve():
    data = request.get_json()
    cabin_id = data.get('cabin_id')
    user = get_current_user()

    if not cabin_id:
        return jsonify({'error': 'cabin_id is required'}), 400

    if user is None:
        return jsonify({'error': 'You are not registered'}), 400

    if get_current_user().cabin_id is not None:
        return jsonify({'error': f'You already have cabin {get_current_user().cabin_id} reserved'}), 400

    result = reserve_cabin(cabin_id, user.id)
    db.session.commit()

    if result['status'] == 'success':
        return jsonify({
            'message': 'Cabin reserved successfully',
            'cabin_id': result['cabin_id']
        }), 200
    else:
        return jsonify({'error': result['reason']}), 400


@cabins_bp.route('/leave', methods=['POST'])
@jwt_required()
def leave():
    user = get_current_user()

    if user is None:
        return jsonify({'error': 'You are not registered'}), 400

    if user.cabin_id is None:
        return jsonify({'error': 'You do not have any cabin reserved'}), 400

    result = leave_cabin(user)
    db.session.commit()

    if result['status'] == 'success':
        return jsonify({'message': 'Left cabin successfully'}), 200
    else:
        return jsonify({'error': result['reason']}), 400


@cabins_bp.route('/', methods=['GET'])
def get_cabins():
    """Get list of all cabins with their current occupancy"""
    try:
        cabins = db.session.query(Cabin).all()
        cabins_data = [cabin.to_dict() for cabin in cabins]
        return jsonify(cabins_data)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch cabins: {str(e)}"}), 400


@cabins_bp.route('/my-cabin', methods=['GET'])
@jwt_required()
def get_my_cabin():
    """Get current user's cabin information"""
    try:
        user = get_current_user()
        if user.cabin_id is None:
            return jsonify({'message': 'No cabin reserved'}), 200

        cabin = db.session.query(Cabin).filter(Cabin.id == user.cabin_id).first()
        if not cabin:
            return jsonify({'error': 'Cabin not found'}), 404

        return jsonify(cabin.to_dict()), 200  # 🔧 Fixed: previously returned a raw Cabin object

    except Exception:
        return jsonify({'error': 'Failed to fetch cabin information'}), 500


@cabins_bp.route("/get-by-id", methods=['POST'])
@jwt_required()
def get_cabin_by_id():
    data = request.get_json()
    cabin_id = data.get('cabin_id')

    if cabin_id is None:
        return jsonify({'error': 'Missing cabin_id in request body'}), 400

    cabin = db.session.query(Cabin).get(cabin_id)
    if not cabin:
        return jsonify({'error': 'Cabin not found'}), 404

    return jsonify(cabin.to_dict()), 200
