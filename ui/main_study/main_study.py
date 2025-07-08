from flask import Blueprint, render_template, jsonify, request, session
from config import config_data_storage
import random
from db_utils import database_connection
import base64
from datetime import datetime

main_study_bp = Blueprint("main_study_bp", __name__, template_folder="templates")


@main_study_bp.route("/main-study-instructions", methods=["GET"])
def main_study_introduction():
    return render_template("main_study_instructions.html")


@main_study_bp.route("/main-study", methods=["GET"])
def main_study():
    print("This is printed when running the main-study function")
    print("Current session variable: ", session)
    if "ratings" not in session:
        session["ratings"] = []
    return render_template(
        "main_study.html", number_of_images=106, ratings=session["ratings"], imageIndex=1
    )

"""
@main_study_bp.route("/main-study-debug", methods=["GET"])
def main_study_debug():
    if "ratings" not in session:
        session["ratings"] = []
    return render_template("main_study.html", number_of_images=106, ratings=session["ratings"])
"""

@main_study_bp.route("/load-study-images", methods=["POST"])
def load_study_images():
    data = request.json
    prolific_pid = data.get("PROLIFIC_PID")
    image_index = data.get("index")

    try:
        conn = database_connection()
        cur = conn.cursor()

        # Fetch the image IDs and their indices
        cur.execute(
            """SELECT main_study_images, real_indices, modified_indices, atc_indices, imc_indices
            FROM participants
            WHERE pid = %s""",
            (prolific_pid,),
        )

        rows = cur.fetchall()
        if not rows:
            return jsonify(
                {
                    "status": "error",
                    "message": "No data found for the provided participant ID.",
                }
            )

        # Unpack fetched data
        image_ids, real_indices, modified_indices, atc_indices, imc_indices = rows[0]

        # Define table names corresponding to each type of image
        table_map = {
            "real": "real_images",
            "modified": "modified_images",
            "atc": "attention_check_images",
            "imc": "attention_check_images",
        }

        # image_index = 0

        if image_index in real_indices:
            table_key = "real"
        elif image_index in modified_indices:
            table_key = "modified"
        elif image_index in atc_indices:
            table_key = "atc"
        else:
            table_key = "imc"

        table_name = table_map[table_key]
        encoded_image = fetch_and_encode_image(
            table_name, image_ids[image_index], table_key, cur
        )

        return jsonify({"status": "success", "image": encoded_image})

    except Exception as e:
        # Log the error details
        print(f"An unexpected error occurred: {e}")
        import traceback

        traceback.print_exc()  # This will print the full traceback
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def transform_path(path):
    return path.replace("\\", "\\\\")


# Function to fetch and encode image from database based on table and ID
def fetch_and_encode_image(table_name, image_id, table_key, cur):
    if table_key != "imc":
        cur.execute(f"SELECT image FROM {table_name} WHERE id = %s", (image_id,))
    else:
        cur.execute(
            f"SELECT image FROM {table_name} WHERE id = %s AND is_imc = 'True'",
            (image_id,),
        )
    blob = cur.fetchone()[0]
    if isinstance(blob, memoryview):
        return base64.b64encode(blob.tobytes()).decode("utf-8")
    return None


@main_study_bp.route("/update-ratings", methods=["POST"])
def update_ratings():
    data = request.json
    session["ratings"] = data.get("ratings")
    session.modified = True
    print("Updated session ratings: ", session["ratings"])
    return jsonify({"message": "Ratings updated successfully!"})

@main_study_bp.route("/update-image-index", methods=["POST"])
def update_image_index():
    data = request.json
    session["imageIndex"] = data.get("imageIndex")
    session.modified = True
    print("Updated session imageIndex: ", session["imageIndex"])
    return jsonify({"message": "Image index updated successfully!"})


@main_study_bp.route("/log-image", methods=["POST"])
def log_image():
    data = request.get_json()
    imageIndex = data.get('imageIndex')
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

        cur.execute("INSERT INTO image_logs VALUES (%s, %s, %s)", (pid, imageIndex, timestamp))
        conn.commit()
        return jsonify({"status": "success"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cur.close()
        conn.close()