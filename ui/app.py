from flask import Flask, request, jsonify, render_template
import os
from config import config_mail
from routes import main_routes
from endpoints.endpoints import endpoints_bp
from comprehension_check.comprehension_check import comprehension_check_bp
from consent_fom.consent_form import consent_form_bp
from colorblindness_test.colorblindness_test import colorblindess_test_bp
from mail.email import email_bp, mail
from main_study.main_study import main_study_bp
from notices.notices import notices_bp
from leaderboard.leaderboard import leaderboard_bp
from debug.debug import debug_bp


# Please define you database.ini file for PostgreSQL credentials as follows:
"""
[postgresql]
host=<host>
dbname=<database name>
user=<username>
password=<password>
"""

def page_not_found(e):
    """
    Handle 404 errors by rendering a custom error page.

    Args:
        e (Exception): The exception that triggered the 404 error.

    Returns:
        tuple: A tuple containing the rendered error template and the HTTP status code 404.
    """
    return render_template('error.html'), 404

def create_app():
    """
    Create and configure the Flask application.

    This function sets up the Flask application with necessary configurations,
    initializes extensions, registers blueprints, and sets up error handling.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    # Use the os.path.dirname to get the current directory
    directory = os.path.dirname(os.path.abspath(__file__))

    # Read the secret key from the file
    with open(os.path.join(directory, "secret.key"), "r") as file:
        app.secret_key = file.read()

    # Configure Flask-Mail
    mail_config = config_mail()
    app.config.update(
        MAIL_SERVER=mail_config["mail_server"],
        MAIL_PORT=mail_config["mail_port"],
        MAIL_USERNAME=mail_config["mail_username"],
        MAIL_PASSWORD=mail_config["mail_password"],
        MAIL_USE_TLS=mail_config["mail_use_tls"],
    )

    # Initialize Flask-Mail with the app
    mail.init_app(app)

    # Register blueprints
    app.register_blueprint(main_routes)
    app.register_blueprint(consent_form_bp)
    app.register_blueprint(colorblindess_test_bp)
    app.register_blueprint(comprehension_check_bp)
    app.register_blueprint(endpoints_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(main_study_bp)
    app.register_blueprint(notices_bp)
    app.register_blueprint(leaderboard_bp)

    # Debug blueprint
    app.register_blueprint(debug_bp)

    # Error handling
    app.register_error_handler(404, page_not_found)

    return app


# Conditional main for running the app
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

    # Allows other computers to connect to the server
    # app.run(debug=True, port=5000, host='0.0.0.0')
