from flask import Blueprint, render_template, jsonify, request
from db_utils import database_connection
from psycopg2.errors import IntegrityError
import base64


colorblindess_test_bp = Blueprint(
    "colorblindess_test", __name__, template_folder="templates"
)


@colorblindess_test_bp.route("/load-ishihara", methods=["POST"])
def load_ishihara():
    data = request.json
    prolific_pid = data.get("PROLIFIC_PID")

    conn = database_connection()
    cur = conn.cursor()

    try:
        conn = database_connection()
        cur = conn.cursor()

        # Get the participant's assigned Ishihara images
        cur.execute(
            """SELECT ishihara_test_cards
                       FROM participants
                       WHERE pid = %s""",
            (prolific_pid,),
        )

        image_ids = cur.fetchone()[0]  # Fetch the first row of the result set
        # image_paths = cur.fetchone()[0]  # Fetch the first row of the result set

        # Join the ishihara table with the unnested array of ids to preserve order
        cur.execute(
            """
            SELECT itc.image
            FROM unnest(%s) WITH ORDINALITY as order_tbl(id, ord)
            JOIN ishihara_test_cards itc ON itc.id = order_tbl.id
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


@colorblindess_test_bp.route("/submit-rating", methods=["POST"])
def submit_rating():
    data = request.json
    rating = str(data.get("rating"))
    prolific_pid = data.get("PROLIFIC_PID")
    finished = data.get("finished")
    first_rating = data.get("first_rating")

    conn = database_connection()
    cur = conn.cursor()

    try:
        conn = database_connection()
        cur = conn.cursor()

        # Only if you successfully inserted the participant, assign them to a random set of Ishihara images
        cur.execute(
            """UPDATE participants 
                SET colorblind_answers = ARRAY_APPEND(colorblind_answers, %s) 
                WHERE pid = %s""",
            (
                rating,
                prolific_pid,
            ),
        )

        # Get the participant's assigned Ishihara images
        cur.execute(
            """SELECT ishihara_test_cards
                       FROM participants
                       WHERE pid = %s""",
            (prolific_pid,),
        )

        image_paths = cur.fetchone()[0]  # Fetch the first row of the result set

        # Join the ishihara table with the unnested array of file paths to preserve order
        cur.execute(
            """SELECT i.digit
                       FROM unnest(%s) WITH ORDINALITY as u(id, ord)
                       JOIN ishihara_test_cards i ON i.id = u.id
                       ORDER BY u.ord""",
            (image_paths,),
        )

        correct_digits = [digit[0] for digit in cur.fetchall()]

        # Update the participants table with the ordered correct_digits
        cur.execute(
            "UPDATE participants SET correct_digits = %s WHERE pid = %s",
            (correct_digits, prolific_pid),
        )

        if first_rating:
            cur.execute(
                "UPDATE participants SET attempted_colorblindness = true WHERE pid = %s",
                (prolific_pid,),
            )

        passed = False
        if finished:
            cur.execute(
                """SELECT
                                CASE WHEN correct_digits = colorblind_answers THEN true
                                    ELSE false
                                END
                                FROM participants
                        WHERE pid=%s""",
                (prolific_pid,),
            )
            passed = cur.fetchone()[0]

            cur.execute(
                "UPDATE participants SET passed_colorblindness = %s WHERE pid = %s",
                (passed, prolific_pid,),
            )

        # Commit the changes to the database
        conn.commit()
        return jsonify(
            {"status": "success", "prolific_pid": prolific_pid, "passed": passed}
        )

    except IntegrityError:
        if conn:
            conn.rollback()  # Roll back the failed transaction
        print("Error: Participant already participated")
        return jsonify({"status": "error", "error": "already_participated"}), 409

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@colorblindess_test_bp.route("/update-attempted-colorblindness-test", methods=["POST"])
def update_attempted_colorblindness_test():
    data = request.json
    prolific_pid = data.get("PROLIFIC_PID")

    conn = database_connection()
    cur = conn.cursor()

    try:
        # Check if the participant has already attempted the colorblindness test
        cur.execute(
            "SELECT attempted_colorblindness FROM participants WHERE pid = %s",
            (prolific_pid,),
        )
        attempted_colorblindness_result = cur.fetchone()

        if attempted_colorblindness_result is None:
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

        attempted_colorblindness = attempted_colorblindness_result[0]

        if attempted_colorblindness:
            # If the participant has already attempted, return an error message
            return (
                jsonify(
                    {
                        "status": "error",
                        "prolific_pid": prolific_pid,
                        "error": "already_participated",
                    }
                ),
                409,
            )

        # If the participant has not already attempted the colorblindness test, update the database
        cur.execute(
            "UPDATE participants SET attempted_colorblindness = true WHERE pid = %s",
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


@colorblindess_test_bp.route("/introduction-colorblindness")
def introduction_colorblindness():
    return render_template("introduction_colorblindness.html")


@colorblindess_test_bp.route("/colorblindness-test")
def colorblindness_test():
    return render_template("colorblindness_test.html")
