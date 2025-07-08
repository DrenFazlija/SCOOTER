from flask import Blueprint
from flask import render_template, request, session, jsonify
from db_utils import database_connection


endpoints_bp = Blueprint("endpoints", __name__, template_folder="templates")


@endpoints_bp.route("/thank-you")
def thank_you():
    """Render the thank you page after study completion."""
    return render_template("thank_you.html")


@endpoints_bp.route("/error")
def error():
    """Render the generic error page."""
    return render_template("error.html")


@endpoints_bp.route("/already-participated")
def already_participated():
    """Render the page shown when a participant attempts to participate multiple times."""
    return render_template("already_participated.html")


@endpoints_bp.route("/unexpected-error")
def unexpected_error():
    """Render the page shown when an unexpected error occurs."""
    return render_template("unexpected_error.html")


@endpoints_bp.route("/feedback")
def feedback():
    """Render the feedback form page."""
    return render_template("feedback.html")


@endpoints_bp.route("/clear-session", methods=["POST"])
def clear_session():
    """Clear the current session data.
    
    Returns:
        JSON response indicating success status
    """
    data = request.json
    print("Clearing session")
    session.clear()
    return jsonify({"status": "success"})


@endpoints_bp.route("/send-feedback", methods=["POST"])
def send_feedback():
    """Handle submission of participant feedback.
    
    Receives feedback form data including:
    - Prolific ID
    - 7 self-assessment questions (q1-q7)
    - Open feedback text
    
    Stores the feedback in the database.

    Returns:
        JSON response indicating success or error status
    """
    # Handle form data here
    data = request.get_json()
    print(data)

    # Extract individual fields from the data
    prolific_pid = data.get("prolific_pid")
    q1 = data.get("q1")
    q2 = data.get("q2")
    q3 = data.get("q3")
    q4 = data.get("q4")
    q5 = data.get("q5")
    q6 = data.get("q6")
    q7 = data.get("q7")
    feedback = data.get("feedback")

    try:
        conn = database_connection()
        cur = conn.cursor()

        self_assessment = [q1, q2, q3, q4, q5, q6, q7]
        print(type(self_assessment))

        cur.execute(
            "INSERT INTO feedback VALUES (%s, %s, %s)",
            (prolific_pid, feedback, self_assessment),
        )

        conn.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        print(e)
        return jsonify({"status": "error"})

    finally:
        cur.close()
        conn.close()
