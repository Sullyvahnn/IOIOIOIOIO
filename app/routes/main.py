import io
from datetime import datetime

from flask import Blueprint, render_template, session, flash, redirect, jsonify, request
from flask_jwt_extended import decode_token
from flask_mail import Message
from jwt import ExpiredSignatureError, InvalidTokenError
from ReportGen import ReportGen
from app import mail
from models import User, Report, db

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

    return render_template('main.html', user_email=user_email, users=User.query.all())

@main.route('/login')
def login():
    return render_template("login.html")

@main.route('/register')
def register():
    return render_template("register.html")

@main.route('/forgot')
def forgot():
    return render_template("forgot.html")

@main.route('/addShift', methods=['POST'])
def addShift():
    token = session.get('access_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    decoded = decode_token(token)
    user_email = decoded.get('sub')

    data = request.get_json()
    date_str = data.get('date')          # "2025-06-06"
    start_hour_str = data.get('start_hour')  # "08:00"
    end_hour_str = data.get('end_hour')      # "10:00"
    activity = data.get('activity')

    try:
        report = Report(
            user_email,
            datetime.strptime(date_str, "%Y-%m-%d").date(),
            datetime.strptime(start_hour_str, "%H:%M").time(),
            datetime.strptime(end_hour_str, "%H:%M").time(),
            activity
        )
        db.session.add(report)
        db.session.commit()
        return jsonify({"message": "Workshift added successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)})



@main.route('/generate', methods=["POST"])
def generate():
    token = session.get('access_token')
    identity = decode_token(token).get('sub')
    person_to_generate = request.form.get('user_login')
    report_gen = ReportGen()
    text, fig = report_gen.generate_report(person_to_generate)
    try:
        # Generate report and attach
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        msg = Message(
            subject="Your Report",
            sender="admin@admin.com",
            recipients=[identity],  # must be string
            body="Attached is your workshift report."
        )
        msg.attach("Report.png", "image/png", buf.read())
        mail.send(msg)

        return redirect('/')
    except Exception as ex:
        # Convert exception to string before sending JSON
        return jsonify({'Error': str(ex)}), 400
