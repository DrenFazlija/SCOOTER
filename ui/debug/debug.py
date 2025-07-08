from flask import Blueprint
from flask import render_template, request, session, jsonify
from db_utils import database_connection
from data_processing import process_ratings
import os


debug_bp = Blueprint("debug", __name__, template_folder="templates", static_folder="static")

@debug_bp.route('/debug-login')
def debug_login():
    return render_template("debug_login.html")

@debug_bp.route('/login-processing', methods=["POST"])
def login_processing():
    try:
        data = request.form

        # Read the secret key from the file
        with open(os.path.join(directory, "debug.key"), "r") as file:
            debug_key = file.read()
        
        if debug_key != data.get("debug_pid"):
            return jsonify({"status": "error", "message": "Invalid password."})
        
        conn = database_connection()
        cur = conn.cursor()

        cur.execute("""SELECT pid FROM participants WHERE pid = %s""", (data.get("debug_pid"),))
        rows = cur.fetchall()
        if not rows:
            return jsonify({"status": "error", "message": "Invalid participant ID."})

        session["debug_pid"] = data.get("debug_pid")
        session["debug_password"] = data.get("debug_password")
    
        ratings = get_ratings(data.get("debug_pid"))
        if ratings is None:
            return jsonify({"status": "error", "message": "No ratings found for the provided participant ID."})

        imc_info = load_imc_info(data.get("debug_pid"))
        if imc_info is None:
            return jsonify({"status": "error", "message": "No IMC information found for the provided participant ID."})

        return render_template("debug_main_study_slider.html", ratings=ratings, imc_info=imc_info)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def get_ratings(pid):
    try:
        conn = database_connection()
        cur = conn.cursor()

        cur.execute("""SELECT main_study_answers FROM participants WHERE pid = %s""", (pid,))
        rows = cur.fetchall()
        if not rows:
            return None

        return rows[0][0]
    except Exception as e:
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()        

def load_imc_info(pid):

    try:
        conn = database_connection()
        cur = conn.cursor()

        # Get the indices of the intruction manipulation check (IMC) images and their corresponding random values
        cur.execute(
            "SELECT imc_indices, correct_imc_values FROM participants WHERE pid = %s",
            (prolific_pid,),
        )

        rows = cur.fetchall()
        if not rows:
            return None

        imc_indices, random_numbers = rows[0]
        print(rows[0])
        print(random_numbers)

        # Only generate random numbers if the participant has not already been assigned random values
        if random_numbers is None:
            # Generate three random numbers between (and including) -100 and 100
            # These are the random values that participants will be asked to select
            random_numbers = [str(random.randint(-100, 100)) for _ in range(3)]

            # Add the random numbers to the database
            cur.execute(
                "UPDATE participants SET correct_imc_values = %s WHERE pid = %s",
                (random_numbers, prolific_pid),
            )

        imc_info = []
        rng_index = 0
        for index in imc_indices:
            custom_string = "the value 0"
            if int(random_numbers[rng_index]) > 0:
                custom_string = "I\'m " + random_numbers[rng_index] + "% sure it\'s REAL"
            elif int(random_numbers[rng_index]) < 0:
                val = abs(int(random_numbers[rng_index]))
                custom_string = "I\'m " + str(val) + "% sure it\'s MODIFIED"

            imc_info.append(
                [
                    index,
                    " Please ignore this question and choose "
                    + custom_string
                    + ". This is an attention check.",
                ]
            )
            rng_index += 1

        conn.commit()

        return imc_info

    except Exception as e:
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@debug_bp.route('/debug-overview')
def debug_overview():
    return render_template("debug_overview.html")

@debug_bp.route('/debug-main-study-slider')
def debug_main_study_slider():

    if debug_pid not in session or debug_password not in session: 
        return render_template("debug_login.html")

    # Read the secret key from the file
    with open(os.path.join(directory, "debug.key"), "r") as file:
        debug_key = file.read()
    
    if debug_key != session["debug_password"]:
        return render_template("debug_login.html")

    return render_template("debug_main_study_slider.html")