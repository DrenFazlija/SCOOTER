from flask import Blueprint, jsonify, request, render_template
from db_utils import database_connection
from datetime import datetime

main_routes = Blueprint("main", __name__)

@main_routes.route('/log', methods=['POST'])
def log():
    data = request.get_json()
    url = data.get('url')
    time_str = data.get('time')
    pid = data.get('pid')

    # Convert the time string to a datetime object
    try:
        timestamp = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    except ValueError as e:
        return jsonify({"error": "Invalid time format"}), 400

    try:
        conn = database_connection()
        cur = conn.cursor()

        cur.execute("INSERT INTO site_logs VALUES (%s, %s, %s)", (pid, url, timestamp))
        conn.commit()
        return jsonify({"status": "success"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@main_routes.route("/check-for-illegal-behavior", methods=["POST"])
def check_for_illegal_behavior():
    """
    Endpoint to check for illegal behavior based on the current page and participant's PID.

    This endpoint handles various stages of a study by checking the participant's progress
    and ensuring they have not already completed the study. It routes the request to the
    appropriate handler based on the current page.

    Returns:
        JSON response indicating the status of the request and any relevant error messages.

    Request Body:
            "PROLIFIC_PID": str,  # The participant's Prolific PID
            "current_page": str   # The current page the participant is on

    Responses:
        200: Successful handling of the request.
        403: Participant has already completed the study.
        404: Participant PID not found in the database.
        500: Internal server error.

    Raises:
        Exception: If any error occurs during database operations or request handling.
    """
    data = request.json
    prolific_pid = data.get("PROLIFIC_PID")
    current_page = data.get("current_page")

    conn = database_connection()
    cur = conn.cursor()

    try:
        # conn = database_connection()
        # cur = conn.cursor()

        cur.execute(
            "SELECT attempted_colorblindness, passed_colorblindness, attempted_comprehension, passed_comprehension, completed_study FROM participants WHERE pid = %s",
            (prolific_pid,),
        )
        result = cur.fetchone()
        if result is None:
            # Handle the case where the PID does not exist in the database
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "pid_not_found",
                    }
                ),
                404,
            )

        print(current_page)

        if current_page == "feedback":
            return handle_feedback(prolific_pid)

        attempted_colorblindness = result[0]
        passed_colorblindness = result[1]
        attempted_comprehension = result[2]
        passed_comprehension = result[3]
        completed_study = result[4]

        if completed_study:
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "already_completed_study",
                    }
                ),
                403,
            )

        if current_page == "consent-form":
            return handle_consent_form_page(
                prolific_pid, attempted_colorblindness, passed_colorblindness
            )

        if current_page == "introduction-colorblindness":
            return handle_introduction_colorblindness_page(
                prolific_pid, attempted_colorblindness, passed_colorblindness
            )

        if current_page == "colorblindness-check":
            return handle_colorblindness_check_page(
                prolific_pid, attempted_colorblindness, passed_colorblindness
            )

        if current_page == "introduction-focal-study":
            return handle_introduction_focal_study_page(
                prolific_pid,
                attempted_colorblindness,
                passed_colorblindness,
                attempted_comprehension,
                passed_comprehension,
            )
        if current_page == "comprehension-check":
            return handle_comprehension_check_page(
                prolific_pid,
                attempted_colorblindness,
                passed_colorblindness,
                attempted_comprehension,
                passed_comprehension,
            )
        if current_page == "main-study":
            return handle_main_study_page(
                prolific_pid,
                attempted_colorblindness,
                passed_colorblindness,
                attempted_comprehension,
                passed_comprehension,
            )
    except Exception as e:
        # Handle any other exception that occurs and roll back the transaction
        conn.rollback()
        return (
            jsonify({"status": "error", "prolific_pid": prolific_pid, "error": str(e)}),
            500,
        )

    finally:
        # Ensure resources are cleaned up
        cur.close()
        conn.close()


@main_routes.route("/study-completed", methods=["POST"])
def study_completed():
    data = request.json
    prolific_pid = data.get("PROLIFIC_PID")
    ratings = data.get("RATINGS")

    print(prolific_pid)
    print(ratings)

    try:

        conn = database_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE participants SET completed_study = true WHERE pid = %s",
            (prolific_pid,),
        )

        print("The update was successful!")

        if ratings is not None:
            cur.execute(
                "UPDATE participants SET main_study_answers = %s WHERE pid = %s",
                (ratings, prolific_pid),
            )
        

        conn.commit()
        return jsonify({"status": "success", "prolific_pid": prolific_pid})

    except Exception as e:
        conn.rollback()
        return (
            jsonify({"status": "error", "prolific_pid": prolific_pid, "error": str(e)}),
            500,
        )

    finally:
        cur.close()
        conn.close()

# Helper functions for check_for_illegal_behavior


def handle_consent_form_page(
    prolific_pid, attempted_colorblindness, passed_colorblindness
):
    if not attempted_colorblindness:
        if passed_colorblindness is None:
            # The pid is already stored in the database, but the participant has not yet attempted the colorblindness test
            return jsonify({"status": "error", "error": "send_to_colorblindness_intro"})
        else:
            # Use 500 Internal Server Error as passing colorblindness without ever attempting should be impossible
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "unknown_source_of_db_update",
                    }
                ),
                500,
            )
    else:
        if passed_colorblindness:
            # The participant has already passed the colorblindness test
            return (
                jsonify({"status": "error", "error": "send_to_focal_study"}),
                500,
            )
        elif passed_colorblindness is None:
            # The participant clicked on the "Continue" button on the introduction page, but the database has not been updated
            # Suggestions: Just let them continue to the test page
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "participant_not_correctly_redirected",
                    }
                ),
                500,
            )
        else:
            # The participant has attempted but not passed the colorblindness test
            return (
                jsonify({"status": "error", "error": "already_attempted_test"}),
                500,
            )


def handle_introduction_colorblindness_page(
    prolific_pid, attempted_colorblindness, passed_colorblindness
):
    if not attempted_colorblindness:
        if passed_colorblindness is None:
            # This is the only correct state for this page. Hence, we return 200 OK
            return jsonify({"status": "success", "prolific_pid": prolific_pid})
        else:
            # Use 500 Internal Server Error as passing colorblindness without ever attempting should be impossible
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "unknown_source_of_db_update",
                    }
                ),
                500,
            )

    elif passed_colorblindness is None:
        # This means that the participant has clicked on the "Continue" button on the introduction page, but the database has not been updated
        # Suggestions: Just let them continue to the test page
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "participant_not_correctly_redirected",
                }
            ),
            500,
        )
    elif passed_colorblindness:
        # Use 200 OK since the error message implies a correct state
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "colorblindness_already_passed",
                }
            ),
            200,
        )
    else:
        # Use 403 Forbidden as they have attempted but not passed
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "colorblindness_not_passed",
                }
            ),
            403,
        )


def handle_colorblindness_check_page(
    prolific_pid, attempted_colorblindness, passed_colorblindness
):
    # If the participant has not attempted the colorblindness test, return an error message
    if not attempted_colorblindness:
        # Either, the participant has simply skipped the introduction page by directly going to the test page...
        if passed_colorblindness is None:
            # Use 400 Bad Request as the action is invalid due to no attempt
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "colorblindness_not_attempted",
                    }
                ),
                400,
            )
        # ... or they somehow managed to skip the introduction page while simultaneously triggering an update to the database
        else:
            # Use 500 Internal Server Error as passing colorblindness without ever attempting should be impossible
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "unknown_source_of_db_update",
                    }
                ),
                500,
            )

    # Attempted_colorblindness is true iff the participant has pressed the continue button on the introduction page
    else:
        if passed_colorblindness is None:
            # This is the first time that the participant sees this page
            # We update the passed_colorblindness field to false to indicate that they have not passed (yet)
            cur.execute(
                "UPDATE participants SET passed_colorblindness = false WHERE pid = %s",
                (prolific_pid,),
            )
            conn.commit()
            # This is the only correct state for this page. Hence, we return 200 OK
            return jsonify({"status": "success", "prolific_pid": prolific_pid})

        elif not passed_colorblindness:
            # Use 403 Forbidden as they are not allowed to proceed as they already attempted but did not pass
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "colorblindness_not_passed",
                    }
                ),
                403,
            )
        else:
            # Use 200 OK since the error message implies a correct state
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "colorblindness_already_passed",
                    }
                ),
                200,
            )


def handle_introduction_focal_study_page(
    prolific_pid,
    attempted_colorblindness,
    passed_colorblindness,
    attempted_comprehension,
    passed_comprehension,
):
    # Participant should only be here, if they attempted and passed the colorblindness test
    # Otherwise, they should be redirected to the colorblindness test
    if not attempted_colorblindness or not passed_colorblindness:
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "colorblindness_not_passed",
                }
            ),
            403,
        )
    # Passed_comprehension will always be None as long as the submitted their comprehension answers
    # To let the users switch between the instructions and the comprehension check,
    # users should be able to stay with either attempted_comprehension == False or attempted_comprehension == True
    if passed_comprehension == None:
        return jsonify({"status": "success", "prolific_pid": prolific_pid})

    # passed_comprehension can only be True or False if the user submits their answers
    # This requires attempted_comprehension to be True. Otherwise: Unexpected error
    if not attempted_comprehension:
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "unexpected_error",
                }
            ),
            500,
        )

    # We now either redirect the user to the main study or to the "Already attempted" page
    if passed_comprehension:
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "already_passed_comprehension",
                }
            ),
            403,
        )
    else:
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "already_attempted_comprehension",
                }
            ),
            403,
        )


def handle_comprehension_check_page(
    prolific_pid,
    attempted_colorblindness,
    passed_colorblindness,
    attempted_comprehension,
    passed_comprehension,
):
    # Participant should only be here, if they attempted and passed the colorblindness test
    # Otherwise, they should be redirected to the colorblindness test
    if not attempted_colorblindness or not passed_colorblindness:
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "colorblindness_not_passed",
                }
            ),
            403,
        )

    # Users should only be here if they read the focal study instructions
    # attempted_comprehension can only be true, if they clicked on the continue button in the focal study instructions page
    # Hence, attempted_comprehension == False means that they have not read the instructions yet
    if not attempted_comprehension:
        # We also need to check for potential unexpected errors (i.e., passed_comprehension is not None)
        if passed_comprehension is not None:
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "unexpected_error",
                    }
                ),
                500,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "send_to_focal_study_instructions",
                    }
                ),
                403,
            )

    # Passed_comprehension will always be None as long as the user submitted their comprehension answers
    # To let the users switch between the instructions and the comprehension check,
    # users should be able to stay with attempted_comprehension == True
    if passed_comprehension == None:
        return jsonify({"status": "success", "prolific_pid": prolific_pid})

    # The only remaining options are to either redirect the user to the main study or to the "Already attempted" page
    if passed_comprehension:
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "already_passed_comprehension",
                }
            ),
            403,
        )
    else:
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "already_attempted_comprehension",
                }
            ),
            403,
        )


def handle_main_study_page(
    prolific_pid,
    attempted_colorblindness,
    passed_colorblindness,
    attempted_comprehension,
    passed_comprehension,
):
    # Users should only be here if they attempted and passed both the colorblindness and comprehension check
    # Otherwise, they should be redirected to the colorblindness test or the comprehension check

    if not attempted_colorblindness or not passed_colorblindness:
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "colorblindness_not_passed",
                }
            ),
            403,
        )

    if not attempted_comprehension or not passed_comprehension:
        return (
            jsonify(
                {
                    "status": "error",
                    "prolific_pid": prolific_pid,
                    "error": "comprehension_not_passed",
                }
            ),
            403,
        )

    return jsonify({"status": "success", "prolific_pid": prolific_pid})


def handle_feedback(prolific_pid):
    conn = database_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM feedback WHERE pid = %s", (prolific_pid,))
        result = cur.fetchone()
        print(result is not None)
        if result is not None:
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "feedback_already_submitted",
                    }
                ),
                403,
            )
        else:
            return jsonify({"status": "success", "prolific_pid": prolific_pid})

    except Exception as e:
        # Handle any other exception that occurs and roll back the transaction
        conn.rollback()
        return (
            jsonify({"status": "error", "prolific_pid": prolific_pid, "error": str(e)}),
            500,
        )

    finally:
        # Ensure resources are cleaned up
        cur.close()
        conn.close()
