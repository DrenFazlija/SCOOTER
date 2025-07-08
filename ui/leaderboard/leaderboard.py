from flask import Blueprint
from flask import render_template, request, session, jsonify
from db_utils import database_connection
from data_processing import process_ratings, get_ratings


leaderboard_bp = Blueprint("leaderboard", __name__, template_folder="templates")

@leaderboard_bp.route('/add-user', methods=['POST'])
def add_user():
    data = request.get_json()
    pid = data['pid']
    user_name = data['username']

    #print(pid, user_name)

    db_data = get_ratings(pid)

    if not db_data:
        return jsonify({"error": "Participant ID not found"}), 404
    
    elif db_data[0][0] is None or len(db_data[0][0]) < 106:
        return jsonify({"error": "Participant has not completed the study"}), 400

    entry = process_ratings(pid, post_hoc=False)
    print(entry)

    if entry is None:
        return jsonify({"error": "Participant ID not found"}), 404
    
    pid = entry[0]
    total_accuracy = entry[1]
    real_accuracy = entry[2]
    modified_accuracy = entry[3]
    check_accuracy = entry[4]

    try:
        conn = database_connection()
        cur = conn.cursor()

        # Check if user already exists
        cur.execute("SELECT id FROM leaderboard WHERE id = %s", (pid,))
        result = cur.fetchone()
        
        if result:
            return jsonify({"error": "Participant already signed up"}), 400

        # Check if username already exists
        cur.execute("SELECT user_name FROM leaderboard WHERE user_name = %s", (user_name,))
        result = cur.fetchone()

        if result:
            return jsonify({"error": "Username taken"}), 400

        # TODO: Dynamically set model and attack names
        model_name = 'Salman2020Do_R50'
        attack_name = 'diffattack'

        cur.execute("SELECT add_user (%s, %s, %s, %s, %s, %s,  %s,  %s)", 
                    (pid, user_name, total_accuracy, real_accuracy, modified_accuracy, check_accuracy, model_name, attack_name))
        conn.commit()
        return jsonify({"status": "success"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cur.close()
        conn.close()

@leaderboard_bp.route('/leaderboard')
def leaderboard():

    try:
        conn = database_connection()
        cur = conn.cursor()

        # TODO: Dynamically set model and attack names
        model_name = 'Salman2020Do_R50'
        attack_name = 'diffattack'

        cur.execute("""SELECT user_name, total_accuracy, real_accuracy, 
                       modified_accuracy, check_accuracy, borda_score
                       FROM leaderboard
                       WHERE model_name = %s AND attack_name = %s
                       ORDER BY borda_score DESC""",
                       (model_name, attack_name))
        
        result = cur.fetchall()

        result = [list(row) for row in result]

        for i in range(len(result)):
            result[i][1] = round(result[i][1], 2)
            result[i][2] = round(result[i][2], 2)
            result[i][3] = round(result[i][3], 2)
            result[i][4] = round(result[i][4], 2)
            result[i][5] = round(result[i][5], 2)

        return render_template('leaderboard.html', data=result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cur.close()
        conn.close()