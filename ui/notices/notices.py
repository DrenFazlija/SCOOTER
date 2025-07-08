from flask import Blueprint
from flask import render_template

notices_bp = Blueprint("notices", __name__, template_folder="templates")


@notices_bp.route("/imprint")
def imprint():
    return render_template("imprint.html")

@notices_bp.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy.html")

@notices_bp.route("/cookie-policy-eu")
def cookie_policy_eu():
    return render_template("cookie-policy-eu.html")