from flask_jwt_extended import JWTManager
from flask import Flask, jsonify
from flask_mail import Mail
from models import db
from flask_cors import CORS #delete after production

mail = Mail()


def create_app(config_class="config.Config"):
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object(config_class)

    CORS(app, supports_credentials=True)
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

    from app.routes.user import user_bp as user_blueprint
    app.register_blueprint(user_blueprint, url_prefix='/user')

    from app.routes.cabins import cabins_bp as cabins_blueprint
    app.register_blueprint(cabins_blueprint, url_prefix="/cabins")

    from app.routes.admin import admin_bp as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')


    return app

