from flask import Blueprint, render_template, jsonify, request
from db_utils import database_connection
import base64


comprehension_check_bp = Blueprint(
    "comprehension_check", __name__, template_folder="templates"
)


@comprehension_check_bp.route("/focal-study-instructions")
def focal_study_instructions():
    return render_template("focal_study_instructions.html")


@comprehension_check_bp.route("/comprehension-check")
def comprehension_check():
    return render_template("comprehension_check.html")

@comprehension_check_bp.route("/instructions-recap")
def instructions_recap():
    return render_template("instructions_recap.html")

@comprehension_check_bp.route("/update-attempted-comprehension-check", methods=["POST"])
def update_attempted_comprehension_check():
    data = request.json
    prolific_pid = data.get("PROLIFIC_PID")

    conn = database_connection()
    cur = conn.cursor()

    try:
        # Check if the participant has already attempted the comprehension check
        cur.execute(
            "SELECT attempted_comprehension FROM participants WHERE pid = %s",
            (prolific_pid,),
        )
        attempted_comprehension_result = cur.fetchone()

        if attempted_comprehension_result is None:
            # Handle the case where the PID does not exist in the database
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "PID not found",
                    }
                ),
                404,
            )

        attempted_comprehension = attempted_comprehension_result[0]

        if attempted_comprehension:
            # Everything is alright, the participant has already clicked the button before
            jsonify({"status": "success", "prolific_pid": prolific_pid})

        # If the participant has not already attempted the comprehension check, update the database
        cur.execute(
            "UPDATE participants SET attempted_comprehension = true WHERE pid = %s",
            (prolific_pid,),
        )

        # Commit the changes to the database
        conn.commit()

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


@comprehension_check_bp.route("/load-comprehension-check", methods=["POST"])
def load_comprehension_check():
    data = request.json
    prolific_pid = data.get("PROLIFIC_PID")

    conn = database_connection()
    cur = conn.cursor()

    try:
        conn = database_connection()
        cur = conn.cursor()

        # Get the participant's assigned comprehension check images
        cur.execute(
            """SELECT comprehension_check_images
               FROM participants
               WHERE pid = %s""",
            (prolific_pid,),
        )

        image_ids = cur.fetchone()[0]  # Fetch the first row of the result set

        # Join the comprehension_check_images table with the unnested array of ids to preserve order
        cur.execute(
            """
            SELECT cci.image
            FROM unnest(%s) WITH ORDINALITY as order_tbl(id, ord)
            JOIN comprehension_check_images cci ON cci.id = order_tbl.id
            ORDER BY order_tbl.ord;
            """,
            (image_ids,),
        )

        image_blobs = cur.fetchall()

        encoded_images = []
        for blob_tuple in image_blobs:
            blob = blob_tuple[0]  # Extract the blob from the tuple
            if isinstance(blob, memoryview):
                # Convert memoryview to bytes and then encode it to Base64
                encoded_image = base64.b64encode(blob.tobytes()).decode("utf-8")
                encoded_images.append(encoded_image)
            else:
                print(f"Unexpected data type: {type(blob)}")  # For debugging

        # Prepend the static directory to each image path
        # image_paths = ["static/" + item for item in image_paths]

        return jsonify({"status": "success", "images": encoded_images})

    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred fetching the image paths."}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@comprehension_check_bp.route("/send-comprehension-answers", methods=["POST"])
def send_comprehension_answers():
    data = request.json
    prolific_pid = data.get("PROLIFIC_PID")
    answers = data.get("answers")

    conn = database_connection()
    cur = conn.cursor()

    print("What")

    try:
        # Get the participant's assigned comprehension check images
        cur.execute(
            """SELECT comprehension_check_images
               FROM participants
               WHERE pid = %s""",
            (prolific_pid,),
        )

        assigned_images = cur.fetchone()[0]  # Fetch the first row of the result set

        # Use the indices of the answers to get the corresponding image IDs
        image_ids = [assigned_images[index] for index in answers]

        # Update the participant's comprehension check answers
        cur.execute(
            """UPDATE participants
               SET comprehension_check_answers = %s
               WHERE pid = %s""",
            (image_ids, prolific_pid),
        )

        # Check if the participant has at least 5 correct answers
        cur.execute(
            """SELECT correct_comprehension_check_answers
                FROM participants
                WHERE pid = %s""",
            (prolific_pid,),
        )

        correct_answers = cur.fetchone()[0]  # Fetch the first row of the result set
        print(correct_answers)
        print(image_ids)
        correct_count = 0

        for i in range(len(image_ids)):
            if image_ids[i] == correct_answers[i]:
                correct_count += 1

        passed_comprehension = correct_count >= 5

        # Update the participant's comprehension check status
        cur.execute(
            """UPDATE participants
               SET passed_comprehension = %s
               WHERE pid = %s""",
            (passed_comprehension, prolific_pid),
        )

        # Commit the changes to the database
        conn.commit()

        if passed_comprehension:
            return jsonify({"status": "success", "prolific_pid": prolific_pid})

        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "Participant failed comprehension check",
                    }
                ),
                400,
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
