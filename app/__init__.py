from flask_jwt_extended import JWTManager
from flask import Flask, jsonify
from flask_mail import Mail
from models import db

mail = Mail()


def create_app(config_class="config.Config"):
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object(config_class)

    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def handle_missing_token(err_msg):
        return jsonify({'error': 'Missing or invalid token'}), 401

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401

    # Initialize extensions with app
    db.init_app(app)
    mail.init_app(app)
    with app.app_context():
        db.create_all()

    # Register blueprints
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')


    return app

