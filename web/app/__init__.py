import os

from flask import render_template
from flask_openapi3 import OpenAPI
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.exceptions import HTTPException
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.utils.sendgrid import SendGridClient


# instantiate extensions
login_manager = LoginManager()
db = SQLAlchemy()
migration = Migrate()
sendgrid_client = SendGridClient(sendgrid_api_key=os.getenv("SENDGRID_API_KEY"))


def create_app(environment="development"):

    from config import config
    from app.views import (
        main_blueprint,
        auth_blueprint,
        email_blueprint,
    )
    from app.api import downloads_info_blueprint, api_email_blueprint
    from app.models import (
        User,
        AnonymousUser,
        Company,
        Computer,
        ComputerView,
        Location,
        LocationView,
    )

    # Instantiate app.
    app = OpenAPI(__name__)

    # set optional bootswatch theme
    app.config["FLASK_ADMIN_SWATCH"] = "cerulean"

    admin = Admin(app, name="microblog", template_mode="bootstrap3")
    # Add administrative views here
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Company, db.session))
    admin.add_view(ComputerView(Computer, db.session))
    admin.add_view(LocationView(Location, db.session))

    # Set app config.
    env = os.environ.get("FLASK_ENV", environment)
    app.config.from_object(config[env])
    config[env].configure(app)

    # Set up extensions.
    db.init_app(app)
    migration.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints.
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(email_blueprint)

    # Register api.
    app.register_api(downloads_info_blueprint)
    app.register_api(api_email_blueprint)

    # Set up flask login.
    @login_manager.user_loader
    def get_user(id):
        return User.query.filter_by(id=int(id)).first()

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.anonymous_user = AnonymousUser

    # Set up Sendgrid mailer
    sendgrid_client.init_app(app)

    # Error handlers.
    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        return render_template("error.html", error=exc), exc.code

    return app
