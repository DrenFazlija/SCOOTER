from flask import Blueprint, flash, request, jsonify
from flask_mail import Message, Mail
from config import config_recipient, config_mail

email_bp = Blueprint("email_bp", __name__)

recipient = config_recipient()["address"]
# Initialize mail without an app
mail = Mail()


@email_bp.route("/send_email", methods=["POST"])
def send_email():
    try:
        request_data = request.get_json()
        user_id = request_data["pid"]
        subject = request_data["subject"]
        message_body = request_data["message"]

        # Assuming recipient and mail configurations are already set
        sender = config_mail()["mail_username"]
        recipient = config_recipient()["address"]

        msg = Message(subject=subject, recipients=[recipient], sender=sender)
        msg.body = message_body + "\n\nProlific ID: " + user_id
        mail.send(msg)

        email_sent_successfully = True
    except Exception as e:
        print(e)  # Log the exception for debugging
        email_sent_successfully = False

    if email_sent_successfully:
        return jsonify({"status": "success", "message": "Email sent successfully!"})
    else:
        return jsonify({"status": "error", "message": "Failed to send email."})
