import psycopg2
from config import config
import os
import random
from tqdm import tqdm


def database_connection():
    db_config = config()
    try:
        conn = psycopg2.connect(
            dbname=db_config["dbname"],
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
        )
        #print("Connection to database successful.")
        return conn
    except Exception as e:
        print("Error connecting to database:", e)


def execute_sql_file(file_path):
    # Read the SQL file
    db_config = config()
    with open(file_path, "r") as file:
        sql_script = file.read()

    # Connect to the database
    conn = psycopg2.connect(
        dbname=db_config["dbname"],
        #user=db_config["user"],
        #password=db_config["password"],
        user="postgres",
        password="postgres",
        host=db_config["host"],
    )

    # Create a cursor
    cur = conn.cursor()
    try:
        # Execute the SQL script
        cur.execute(sql_script)

        # Commit the changes
        conn.commit()

        # Close the cursor
        cur.close()

        print("SQL script executed successfully.")

    except Exception as e:
        print("Error during execution of SQL script:", e)

        # Rollback in case of error
        if conn is not None:
            conn.rollback()

    finally:
        # Close the connection
        if conn is not None:
            conn.close()


def configure_image_db(
    path, name_of_db, is_imc=False, table_exists=False, model_name="Salman2020Do_R50"
):
    db_config = config()
    # Read all the images in the directory
    images = os.listdir(path)

    # Connect to the database
    conn = psycopg2.connect(
        dbname=db_config["dbname"],
        user=db_config["user"],
        password=db_config["password"],
        host=db_config["host"],
    )

    # Create a cursor
    cur = conn.cursor()

    try:
        # Create the table
        if not table_exists:
            cur.execute(
                "CREATE TABLE " + name_of_db + " (id SERIAL PRIMARY KEY, image BYTEA)"
            )

        # Add additional columns based on name of the database
        if name_of_db == "ishihara_test_cards":
            if not table_exists:
                cur.execute(
                    "ALTER TABLE "
                    + name_of_db
                    + " ADD COLUMN color_type VARCHAR(255), ADD COLUMN digit VARCHAR(255)"
                )
            # Insert the images into the database
            for image in images:
                # Ishihare images are named as follows: 0_AveriaLibre-LightItalictheme_1 type_1.png
                color_info = image.split("_")

                digit = color_info[0]  # in our example: 0

                # check if digit character is a number
                if not digit.isdigit():
                    color_type = "4"
                    digit = "I don't see a digit"
                    with open(path + "/" + image, "rb") as file:
                        cur.execute(
                            "INSERT INTO "
                            + name_of_db
                            + " (image, color_type, digit) VALUES (%s , %s, %s)",
                            (psycopg2.Binary(file.read()), color_type, digit),
                        )

                else:
                    color_type = (
                        color_info[2][0] + color_info[3][0]
                    )  # in our example: 11 -> first 1 from "1 type" and second 1 from "1.png"

                    if color_type == "11":
                        color_type = "0"

                    elif color_type == "22":
                        color_type = "1"

                    elif color_type == "33":
                        color_type = "2"

                    elif color_type == "43":
                        color_type = "3"

                    else:
                        color_type = "4"

                    with open(path + "/" + image, "rb") as file:
                        cur.execute(
                            "INSERT INTO "
                            + name_of_db
                            + " (image, color_type, digit) VALUES (%s , %s, %s)",
                            (psycopg2.Binary(file.read()), color_type, digit),
                        )

        elif name_of_db == "attention_check_images":
            if not table_exists:
                cur.execute("ALTER TABLE " + name_of_db + " ADD COLUMN is_imc BOOLEAN")
            # Insert the images into the database
            insert_attention_check_images(images, path, cur, is_imc)

        else:
            if not table_exists:
                cur.execute(
                    "ALTER TABLE " + name_of_db + " ADD COLUMN model_name VARCHAR(255)"
                )
            if name_of_db == "real_images":
                main_study_real_images(images, path, cur, model_name)
            if name_of_db == "modified_images":
                main_study_modified_images(images, path, cur, model_name)

        # Commit the changes
        conn.commit()

        # Close the cursor
        cur.close()

        print("Images uploaded successfully.")

    except Exception as e:
        print("Error during execution of SQL script:", e)

        # Rollback in case of error
        if conn is not None:
            conn.rollback()


def insert_attention_check_images(images, path, cur, is_imc, values=None):
    # These are our very noisy images from ImageNet-C
    if not is_imc:
        folders = ["gaussian_noise\\5", "shot_noise\\5", "impulse_noise\\5"]

        # for each folder, we take one image per class -> in total: 3k images
        for folder in folders:
            class_directories = os.listdir(path + "\\" + folder)

            # for each class directory, we take one random image
            for current_directory in tqdm(class_directories):
                images = os.listdir(path + "\\" + folder + "\\" + current_directory)

                # randomly choose one index between 0 and len(images)
                random_index = random.randint(0, len(images) - 1)
                image = images[random_index]

                with open(
                    path + "\\" + folder + "\\" + current_directory + "\\" + image,
                    "rb",
                ) as file:
                    cur.execute(
                        "INSERT INTO "
                        + "attention_check_images"
                        + " (image, is_imc) VALUES (%s , %s)",
                        (psycopg2.Binary(file.read()), is_imc),
                    )

    # These are clean sample images from ImageNet (Source: Eli Schwartz Repository)
    else:
        id = 0
        for image in images:
            # Check if image path is valid
            if os.path.isfile(path + "/" + image):
                with open(path + "/" + image, "rb") as file:
                    value = values[image]
                    cur.execute(
                        "INSERT INTO "
                        + "attention_check_images"
                        + " (id, image, is_imc, correct_value) VALUES (%s, %s , %s, %s)",
                        (id, psycopg2.Binary(file.read()), is_imc, value),
                    )
                id += 1
def add_new_cc_images(path, indicator="v2"):
    db_config = config()
    images = os.listdir(path)

    # Connect to the database
    conn = psycopg2.connect(
        dbname=db_config["dbname"],
        user=db_config["user"],
        password=db_config["password"],
        host=db_config["host"],
    )

    # Create a cursor
    cur = conn.cursor()

    try:
        superclasses = [
            "birds",
            "containers",
            "dogs",
            "furniture",
            "other_mammals",
            "vehicles",
            "clothing",
            "devices",
            "food_plants_fungi",
            "invertebrates",
            "reptiles",
        ]

        modification_types = ["coloring", "filters", "pixels"]

        # Insert the modified images into the database
        # Loop over all modification types and image classes
        for img_class in superclasses:
            for modification in modification_types:
                path_to_class = path + "/" + img_class + "/" + modification
                images = [
                    f
                    for f in os.listdir(path_to_class)
                    if os.path.isfile(os.path.join(path_to_class, f))
                ]
                for image in images:
                    if indicator in image:
                        img_number = image.split("_")[0][-1]
                        print("Updating the following entry Superclass:", img_class, "Modification:", modification, "Image Number:", img_number)
                        with open(path_to_class + "/" + image, "rb") as file:
                            cur.execute(
                                "UPDATE comprehension_check_images SET image = %s WHERE class = %s AND modification = %s AND img_number = %s",
                                (
                                    psycopg2.Binary(file.read()),
                                    str(img_class),
                                    str(modification),
                                    str(img_number),
                                ),
                            )
    
    except Exception as e:
        print("Error during execution of SQL script." + e)
    
    finally:
        conn.commit()
        cur.close()
        conn.close()

def comprehension_check_images(path, name_of_db, table_exists=False):
    db_config = config()
    # Read all the images in the directory
    images = os.listdir(path)

    # Connect to the database
    conn = psycopg2.connect(
        dbname=db_config["dbname"],
        user=db_config["user"],
        password=db_config["password"],
        host=db_config["host"],
    )

    # Create a cursor
    cur = conn.cursor()

    try:
        # Create the table
        if not table_exists:
            cur.execute(
                "CREATE TABLE "
                + name_of_db
                + " (id SERIAL PRIMARY KEY, image BYTEA, is_modified BOOLEAN, modification VARCHAR(255), class VARCHAR(255), img_number VARCHAR(1))"
            )

        superclasses = [
            "birds",
            "containers",
            "dogs",
            "furniture",
            "other_mammals",
            "vehicles",
            "clothing",
            "devices",
            "food_plants_fungi",
            "invertebrates",
            "reptiles",
        ]

        # 1. Insert the unmodified images into the database
        for img_class in superclasses:
            path_to_class = path + "\\" + img_class
            images = [
                f
                for f in os.listdir(path_to_class)
                if os.path.isfile(os.path.join(path_to_class, f))
            ]
            img_number = 1
            for image in images:
                with open(path_to_class + "/" + image, "rb") as file:
                    cur.execute(
                        "INSERT INTO "
                        + name_of_db
                        + " (image, is_modified, class, img_number) VALUES (%s , %s, %s, %s)",
                        (
                            psycopg2.Binary(file.read()),
                            False,
                            str(img_class),
                            str(img_number),
                            image,
                        ),
                    )
                    img_number += 1

        modification_types = ["coloring", "filters", "pixels"]

        # 2. Insert the modified images into the database
        # Loop over all modification types and image classes
        for img_class in superclasses:
            for modification in modification_types:
                path_to_class = path + "\\" + img_class + "\\" + modification
                images = [
                    f
                    for f in os.listdir(path_to_class)
                    if os.path.isfile(os.path.join(path_to_class, f))
                ]
                img_number = 1
                for image in images:
                    with open(path_to_class + "/" + image, "rb") as file:
                        cur.execute(
                            "INSERT INTO "
                            + name_of_db
                            + " (image, is_modified, modification, class, img_number) VALUES (%s , %s, %s, %s, %s)",
                            (
                                psycopg2.Binary(file.read()),
                                True,
                                modification,
                                str(img_class),
                                str(img_number),
                                image,
                            ),
                        )
                        img_number += 1

        # Commit the changes
        conn.commit()

        # Close the cursor
        cur.close()

        print("Images uploaded successfully.")

    except Exception as e:
        print("Error during execution of SQL script:", e)

        # Rollback in case of error
        if conn is not None:
            conn.rollback()


def main_study_real_images(images, path, cur, model_name="Salman2020Do_R50"):
    #db_config = config()
    for subdirectory in tqdm(images):
        sub_images = os.listdir(path + "/" + subdirectory)
        for image in sub_images:
            with open(path + "/" + subdirectory + "/" + image, "rb") as file:
                cur.execute(
                    "INSERT INTO "
                    + "real_images"
                    + " (image, model_name) VALUES (%s , %s)",
                    (psycopg2.Binary(file.read()), model_name),
                )
                
def main_study_modified_images(images, path, cur, model_name="Salman2020Do_R50", attack_name="ncf", start_id = 0, start_known=False, file_extension=".JPEG"):
    #db_config = config()
    # Filter out images that are not the correct file extension
    images = [image for image in images if image.endswith(file_extension)]

    if not start_known:
        cur.execute("SELECT MAX(id) FROM modified_images")
        start_id = cur.fetchone()[0] + 1
        print("Starting ID:", start_id)

    for image in tqdm(images):
        with open(path + "/" + image, "rb") as file:
            cur.execute(
                "INSERT INTO "
                + "modified_images"
                + " (id, image, model_name, attack_name) VALUES (%s, %s , %s, %s)",
                (start_id, psycopg2.Binary(file.read()), model_name, attack_name),
            )
            start_id += 1

if __name__ == "__main__":
    conn = database_connection()
    cur = conn.cursor()

    images = os.listdir(
        "/home/dren.fazlija/data/Scooter/attacks/aca",    
    )

    main_study_modified_images(images, "/home/dren.fazlija/data/Scooter/attacks/aca", cur, model_name="Salman2020Do_R50", attack_name="aca", file_extension=".JPEG")
    
    conn.commit()
    cur.close()
    conn.close()