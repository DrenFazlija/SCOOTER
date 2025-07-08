from flask import Blueprint, render_template, jsonify, request
from db_utils import database_connection
from psycopg2.errors import IntegrityError
import random
from configparser import ConfigParser
import os

consent_form_bp = Blueprint("consent_form", __name__, template_folder="templates")

config = ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '..', 'attack.ini'))
attack_name = config.get('attack', 'name', fallback='diffattack')


@consent_form_bp.route("/consent-form")
def consent_form():
    return render_template("consent_form.html")


@consent_form_bp.route("/submit-pid", methods=["POST"])
def submit_pid():
    data = request.json
    #print(data)
    prolific_pid = data.get("PROLIFIC_PID")
    #attack_name = data.get("attack_name")
    #print("Attack name: ", attack_name)

    try:
        conn = database_connection()
        cur = conn.cursor()

        study_id = "1"  # TODO: Make this dynamic
        session_id = "1"  # TODO: Make this dynamic

        # Try to insert the participant into the database
        cur.execute(
            "INSERT INTO participants (pid, study_id, session_id) VALUES (%s, %s, %s)",
            (prolific_pid, study_id, session_id),
        )

        cur.execute(
            """UPDATE participants
                SET ishihara_test_cards = (
                    SELECT array_agg(id ORDER BY random()) as random_ids
                    FROM (
                        SELECT DISTINCT ON (color_type) id
                            FROM ishihara_test_cards
                            ORDER BY color_type, random()
                    ) as distinct_images
                )
               WHERE pid = %s""",
            (prolific_pid,),
        )

        # Get the participant's assigned Ishihara images
        cur.execute(
            """SELECT ishihara_test_cards
                       FROM participants
                       WHERE pid = %s""",
            (prolific_pid,),
        )

        image_paths = cur.fetchone()[0]  # Fetch the first row of the result set
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

        # Assign participants to a random set of comprehension check image pairs

        # 1. Get six modified images -- two from each modification type
        cur.execute(
            """
            SELECT id
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (PARTITION BY modification ORDER BY RANDOM()) AS rn
                FROM comprehension_check_images
                WHERE is_modified = TRUE
            ) AS subquery
            WHERE rn <= 2
            ORDER BY RANDOM()
            """,
        )

        modified_images = cur.fetchall()

        # 2. Get 6 unmodified images -- one from each class, and output them in random order
        cur.execute(
            """
            SELECT id
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (PARTITION BY class ORDER BY RANDOM()) AS rn
                FROM comprehension_check_images
                WHERE is_modified = FALSE
            ) AS subquery
            WHERE rn <= 1
            ORDER BY RANDOM()
            LIMIT 6
            """,
        )

        unmodified_images = cur.fetchall()

        # 3. Combine the modified and unmodified images into a single list -- randomize order within each pair
        comprehension_check_images = []
        for i in range(0, 6):
            # randomly choose which image to put first
            if bool(random.getrandbits(1)):
                comprehension_check_images.append(modified_images[i])
                comprehension_check_images.append(unmodified_images[i])
            else:
                comprehension_check_images.append(unmodified_images[i])
                comprehension_check_images.append(modified_images[i])

        # 4. Update the participants table with the ordered comprehension_check_images

        cur.execute(
            "UPDATE participants SET comprehension_check_images = %s WHERE pid = %s",
            (comprehension_check_images, prolific_pid),
        )

        # 5. Also store the ids of the modified images as correct answers
        cur.execute(
            "UPDATE participants SET correct_comprehension_check_answers = %s WHERE pid = %s",
            (modified_images, prolific_pid),
        )

        # Assign the participants to a random set of real and modified images
        # As well as a random set of attention check images and instruction manipulation check images

        # 1. Get 50 real images
        cur.execute(
            """
            SELECT id
            FROM real_images
            ORDER BY RANDOM()
            LIMIT 50
            """,
        )

        real_images = cur.fetchall()

        # 2. Get 50 modified images
        cur.execute(
            """
            SELECT id
            FROM modified_images
            WHERE attack_name = %s
            ORDER BY RANDOM()
            LIMIT 50
            """,
            (attack_name,),
        )

        fake_images = cur.fetchall()

        # From here on, we need to keep track of the indices of the real and modified images

        real_indices = []
        modified_indices = []

        # 3. Combine the real and modified images into a single list
        all_images = []
        real_index = 0
        modified_index = 0

        # Get a 0-1-array of length 100, where 0 means real image and 1 means modified image
        # This is used to randomly choose which type of image to put at each index
        real_or_modified = [0] * 50 + [1] * 50
        random.shuffle(real_or_modified)

        for i in range(0, 100):
            # randomly choose which type of image to put at index i
            if real_or_modified[i] == 0:
                all_images.append(real_images[real_index])
                real_index += 1
                real_indices.append(i)
            else:
                all_images.append(fake_images[modified_index])
                modified_index += 1
                modified_indices.append(i)

        # 4. Get 6 attention check images, 3 images where is_imc is true and 3 where is_imc is false
        cur.execute(
            """
            SELECT id
            FROM attention_check_images
            WHERE is_imc = TRUE
            ORDER BY RANDOM()
            LIMIT 3
            """,
        )

        imc_images = cur.fetchall()

        # Get the correct values of the IMC images
        correct_imc_values = []

        for id in imc_images:
            cur.execute(
                """
                SELECT correct_value
                FROM attention_check_images
                WHERE id = %s
                """,
                (id,),
            )
            correct_imc_values.append(cur.fetchone())

        cur.execute(
            """
            SELECT id
            FROM attention_check_images
            WHERE is_imc = FALSE
            ORDER BY RANDOM()
            LIMIT 3
            """,
        )

        attention_check_images = cur.fetchall() + imc_images

        # From now on, we need to keep track of the indices of the attention check images
        atc_indices = []
        imc_indices = []

        # 5. Adding the attention check images to the all_images list

        # The first three images from attention_check_images are the ones where is_imc is false
        # We want to have one in each of the first three quarters of the all_images list
        # The position within a quarter is random

        # The last three images from attention_check_images are the ones where is_imc is true
        # Two such images are added to the first quarter of the all_images list
        # One such image is added to around the 50% mark of the all_images list

        # Insert attention check images and update indices
        for index, img in enumerate(attention_check_images):
            if index < 3:
                # First three images where is_imc is false
                position = random.randint(index * 25, (index + 1) * 25)
            else:
                # Last three images where is_imc is true
                position = (
                    random.randint(0, 25) if index < 5 else random.randint(45, 55)
                )

            # Insert the image
            all_images.insert(position, img)
            # Update the indices lists
            real_indices = update_indices(real_indices, position)
            modified_indices = update_indices(modified_indices, position)
            atc_indices = update_indices(atc_indices, position)
            if index < 3:
                atc_indices.append(position)
            else:
                imc_indices = update_indices(imc_indices, position)
                imc_indices.append(position)

        # Assure that that each index occurs only once in through all the lists
        assert len(set(real_indices)) == 50
        assert len(set(modified_indices)) == 50
        assert len(set(atc_indices)) == 3
        assert len(set(imc_indices)) == 3

        all_indices = real_indices + modified_indices + atc_indices + imc_indices
        # Check for uniqueness by comparing the length of all_indices with the length of its set
        assert len(set(all_indices)) == 106

        # Check for completeness by ensuring all indices from 0 to 105 are present
        expected_indices = set(range(106))  # Set of all indices from 0 to 105
        actual_indices = set(all_indices)

        assert expected_indices == actual_indices

        # 6. Update the participants table with the ordered all_images and the indices lists
        cur.execute(
            """
            UPDATE participants 
            SET main_study_images = %s,
                real_indices = %s,
                modified_indices = %s,
                atc_indices = %s,
                imc_indices = %s,
                correct_imc_values = %s
            WHERE pid = %s""",
            (
                all_images,
                real_indices,
                modified_indices,
                atc_indices,
                imc_indices,
                correct_imc_values,
                prolific_pid,
            ),
        )

        # Commit the changes to the database
        conn.commit()
        return jsonify({"status": "success", "prolific_pid": prolific_pid})

    except IntegrityError:
        if conn:
            conn.rollback()  # Roll back the failed transaction
        print("Error: Participant already participated")
        return jsonify({"status": "error", "error": "already_participated"}), 409

    except Exception as e:
        # Handle any other exception that occurs and roll back the transaction
        if conn:
            conn.rollback()
        print("Error: {}".format(e))
        return jsonify({"status": "error", "error": "unknown"}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def update_indices(indices_list, insert_position):
    # Increment all indices greater than or equal to the insert position
    return [index + 1 if index >= insert_position else index for index in indices_list]
