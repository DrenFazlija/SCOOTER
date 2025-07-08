from db_utils import database_connection
from data_processing import get_ratings, get_main_study_image_ids
import psycopg2
import csv
import os
from tqdm import tqdm
import numpy as np


def export_ratings_of_experiment(pids, export_path, is_per_user=False, with_image_ids=False):

    if not is_per_user:
        with open(export_path + ".csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['rating', 'pid', 'image_type', 'image_id'])
    
    else:
        real_averages = []
        modified_averages = []

    for pid in tqdm(pids):
        data = get_ratings(pid)
        if data:
            main_study_answers = data[0][0]
            real_indices = data[0][1]
            modified_indices = data[0][2]

            if is_per_user:
                real_ratings = []
                modified_ratings = []
                for i in range(len(main_study_answers)):
                    if i in real_indices:
                        real_ratings.append(int(main_study_answers[i]))
                    elif i in modified_indices:
                        modified_ratings.append(int(main_study_answers[i]))

                np_real = np.array(real_ratings)
                np_modified = np.array(modified_ratings)

                # Get the average ratings for the real and modified images
                real_average = np.mean(np_real)
                modified_average = np.mean(np_modified)

                real_averages.append(real_average)
                modified_averages.append(modified_average)
            
            else:
                image_ids = get_main_study_image_ids(pid) if with_image_ids else [None] * len(main_study_answers)

                with open(export_path + ".csv", mode='a') as file:
                    writer = csv.writer(file)
                    for i in range(len(main_study_answers)):
                        if i in real_indices:
                            writer.writerow([main_study_answers[i], pid, "real", image_ids[i]])
                        elif i in modified_indices:
                            writer.writerow([main_study_answers[i], pid, "modified", image_ids[i]])
        else:
            print("PID not found in database: " + pid)
            return

    if is_per_user:
        real_averages = np.array(real_averages)
        modified_averages = np.array(modified_averages)

        np.savez_compressed(export_path + "_averages.npz", real_averages=real_averages, modified_averages=modified_averages)

# A function used to assign an external set of images to the corresponding real images in the database
# E.g., the real_images.zip file is sorted by the classes and the images are named as "[1-2966].jpg"
# Multiple attack implementations (NCF and cAdv) follow this naming scheme, allowing us to directly assign the images to the corresponding real images
def annotate_external_dataset(images, path, cur, pids, model_name="Salman2020Do_R50", category="Real Image"):
    # Prepare a file to store the image-id pairs
    filename = path + "/" + model_name + "_annotations.csv"
    id_names = {}
    ratings_per_image = {}

    if category == "Real Image":
        table_name = "real_images"
    elif category == "Modified Image":
        table_name = "modified_images"
    else:
        print("Invalid category: " + category)
        return

    # Map all image ids to their corresponding names
    for image in tqdm(images):
        with open(path + "/" + image, "rb") as file:
            if table_name == "real_images":
                cur.execute("""
                            SELECT id 
                            FROM real_images 
                            WHERE image = %s
                            """, (psycopg2.Binary(file.read()), ))
            elif table_name == "modified_images":
                cur.execute("""
                            SELECT id 
                            FROM modified_images 
                            WHERE image = %s
                            """, (psycopg2.Binary(file.read()), ))
            image_id = cur.fetchone()
            if image_id:
                id_names[image_id[0]] = image                    
            else:
                print("Image not found in database: " + image)

    # Get all ratings for the image ids
    for pid in tqdm(pids):
            cur.execute("""
                        SELECT main_study_images, main_study_answers, real_indices, modified_indices
                        FROM participants
                        WHERE pid = %s
                        """, (pid,))
            
            result = cur.fetchone()
            if result:
                images = result[0]
                answers = result[1]
                real_indices = result[2]
                modified_indices = result[3]

                if category == "Real Image":
                    for i in range(len(images)):
                        if i in real_indices:
                            if images[i] not in ratings_per_image:
                                ratings_per_image[images[i]] = []
                            ratings_per_image[images[i]].append(answers[i])

                elif category == "Modified Image":
                    for i in range(len(images)):
                        if i in modified_indices:
                            if images[i] not in ratings_per_image:
                                ratings_per_image[images[i]] = []
                            ratings_per_image[images[i]].append(answers[i])
            else:
                print("PID not found in database: " + pid)
    
    print("Successfully retrieved all ratings for the images.")

    # Write the image_name-rating pairs to a csv file
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['image_name', 'ratings'])
        for key in ratings_per_image:
            writer.writerow([id_names[key], ratings_per_image[key]])

def map_original_names(original_img_path, real_img_path):
    original_images = os.listdir(original_img_path)
    real_images = os.listdir(real_img_path)

    # All original images are further divided into subdirectories
    # The subdirectories are named as the class labels (e.g., "0000", "0001", ..., "0999")
    # The real images are named as "[1-2966].jpg"

    name_pairs = {}

    original_images.sort()
    real_images.sort()
    for subdirs in tqdm(original_images):
        subdir_path = original_img_path + "/" + subdirs
        subdir_images = os.listdir(subdir_path)
        for image in subdir_images:
            for real_image in real_images:
                with open(subdir_path + "/" + image, "rb") as original_file, open(real_img_path + "/" + real_image, "rb") as real_file:
                    if original_file.read() == real_file.read():
                        name_pairs[real_image] = image
                        # Remove the real image from the list to avoid duplicate matches
                        real_images.remove(real_image)
                        break

    with open(original_img_path + "/name_pairs.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['real_image_name', 'original_image_name'])
        for key in name_pairs:
            writer.writerow([key, name_pairs[key]])

def rename_img_files(path, name_pairs_path):
    name_pairs = {}
    with open(name_pairs_path, mode='r') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            name_pairs[row[1]] = row[0]

    images = os.listdir(path)
    for image in tqdm(images):
        # Original name: ae_ILSVRC2012_val_00031381.JPEG.jpg
        image_id = image[3:-4]

        # ILSVRC2012_val_00024327.JPEG
        os.rename(path + "/" + image, path + "/" + name_pairs[image_id])

"""
All the following functions related to real and modified images are used to export the annotations from the database to a csv file.
Please only use these functions if you are able properly assign each attack's set of modified images
to the corresponding real images. Otherwise, you should use the functions above to annotate an external set of images.
"""

def export_real_images(export_path, pids, download_images=False):
    try:
        conn = database_connection()
        cur = conn.cursor()

        if download_images:
            # Get all images from the database
            cur.execute("SELECT image, id FROM real_images")
            images = cur.fetchall()
            for image in images:
                with open(export_path + str(image[1]) + ".jpg", "wb") as file:
                    file.write(image[0])

        ratings_per_image = {}
        for pid in tqdm(pids):
            cur.execute("""
                        SELECT main_study_images, main_study_answers, real_indices
                        FROM participants
                        WHERE pid = %s
                        """, (pid,))
            
            result = cur.fetchone()
            if result:
                images = result[0]
                answers = result[1]
                real_indices = result[2]

                for i in range(len(images)):
                    if i in real_indices:
                        if images[i] not in ratings_per_image:
                            ratings_per_image[images[i]] = []
                        ratings_per_image[images[i]].append(answers[i])
            else:
                print("PID not found in database: " + pid)
        
        with open(export_path + "real_images_ratings.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['image_id', 'ratings'])
            for key in ratings_per_image:
                writer.writerow([key, ratings_per_image[key]])

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def export_modified_images(export_path, pids, attack_name, model_name, download_images=False):
    try:
        conn = database_connection()
        cur = conn.cursor()

        if download_images:
            # Get all images from the database
            cur.execute("SELECT image, id FROM modified_images WHERE attack_name = %s AND model_name = %s", (attack_name, model_name))
            images = cur.fetchall()
            for image in tqdm(images):
                with open(export_path + attack_name + "/" + str(image[1]) + ".jpg", "wb") as file:
                    file.write(image[0])

        ratings_per_image = {}
        for pid in tqdm(pids):
            cur.execute("""
                        SELECT main_study_images, main_study_answers, modified_indices
                        FROM participants
                        WHERE pid = %s
                        """, (pid,))
            
            result = cur.fetchone()
            if result:
                images = result[0]
                answers = result[1]
                modified_indices = result[2]

                for i in range(len(images)):
                    if i in modified_indices:
                        if images[i] not in ratings_per_image:
                            ratings_per_image[images[i]] = []
                        ratings_per_image[images[i]].append(answers[i])
            else:
                print("PID not found in database: " + pid)
        
        csv_file_name = model_name + "_modified_images_ratings.csv"

        with open(export_path + attack_name + "/" + csv_file_name, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['image_id', 'ratings'])
            for key in ratings_per_image:
                writer.writerow([key, ratings_per_image[key]])

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def export_imc_ratings(export_path, pids, download_images=False):
    try:
        conn = database_connection()
        cur = conn.cursor()

        id_correct_value = {}

        # Get all images from the database
        cur.execute("SELECT image, id, correct_value FROM attention_check_images WHERE is_imc = TRUE")
        images = cur.fetchall()
        for image in images:
            if download_images:
                with open(export_path + str(image[1]) + ".jpg", "wb") as file:
                    file.write(image[0])
            id_correct_value[image[1]] = image[2]

        ratings_per_image = {}
        for pid in tqdm(pids):
            cur.execute("""
                        SELECT main_study_images, main_study_answers, imc_indices
                        FROM participants
                        WHERE pid = %s
                        """, (pid,))
            
            result = cur.fetchone()
            if result:
                images = result[0]
                answers = result[1]
                imc_indices = result[2]

                for i in range(len(images)):
                    if i in imc_indices:
                        if images[i] not in ratings_per_image:
                            ratings_per_image[images[i]] = []
                        ratings_per_image[images[i]].append(answers[i])
            else:
                print("PID not found in database: " + pid)
        
        with open(export_path + "imc_images_ratings.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['image_id', 'ratings', 'correct_value'])
            for key in ratings_per_image:
                writer.writerow([key, ratings_per_image[key], id_correct_value[key]])

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def export_atc_ratings(export_path, pids, download_images=False):
    try:
        conn = database_connection()
        cur = conn.cursor()

        # Get all images from the database
        if download_images:
            cur.execute("SELECT image, id FROM attention_check_images WHERE is_imc = FALSE")
            images = cur.fetchall()
            for image in images:
                with open(export_path + str(image[1]) + ".jpg", "wb") as file:
                    file.write(image[0])

        ratings_per_image = {}
        for pid in tqdm(pids):
            cur.execute("""
                        SELECT main_study_images, main_study_answers, atc_indices
                        FROM participants
                        WHERE pid = %s
                        """, (pid,))
        
            result = cur.fetchone()
            if result:
                images = result[0]
                answers = result[1]
                atc_indices = result[2]

                for i in range(len(images)):
                    if i in atc_indices:
                        if images[i] not in ratings_per_image:
                            ratings_per_image[images[i]] = []
                        ratings_per_image[images[i]].append(answers[i])
            else:
                print("PID not found in database: " + pid)
        
        with open(export_path + "atc_images_ratings.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['image_id', 'ratings'])
            for key in ratings_per_image:
                writer.writerow([key, ratings_per_image[key]])

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def export_ishihara_ratings(export_path, pids, download_images=False):
    try:
        conn = database_connection()
        cur = conn.cursor()

        image_info = {}

        # Get all images from the database
        
        cur.execute("SELECT image, id, color_type, digit FROM ishihara_test_cards")
        images = cur.fetchall()
        for image in images:
            if download_images:
                with open(export_path + str(image[1]) + ".jpg", "wb") as file:
                    file.write(image[0])
            image_info[image[1]] = (image[2], image[3])

        ratings_per_image = {}
        for pid in tqdm(pids):
            cur.execute("""
                        SELECT ishihara_test_cards, colorblind_answers
                        FROM participants
                        WHERE pid = %s
                        """, (pid,))
        
            result = cur.fetchone()
            if result:
                images = result[0]
                answers = result[1]

                for i in range(len(images)):
                    if images[i] not in ratings_per_image:
                        ratings_per_image[images[i]] = []
                    ratings_per_image[images[i]].append(answers[i])
            else:
                print("PID not found in database: " + pid)
        
        with open(export_path + "ishihara_images_ratings.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['image_id', 'ratings', 'color_type', 'digit'])
            for key in ratings_per_image:
                writer.writerow([key, ratings_per_image[key], image_info[key][0], image_info[key][1]])

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

# TODO: Implement
def export_comprehension_check_ratings(export_path, pids, download_images=False):
    raise NotImplementedError("This function is not yet implemented.")

def get_all_pids(dir, filenames=None, attacks=None):
    pids_per_attack = {}

    if not filenames:
        filenames = [
            "cadv/pids.txt",
            "larger_test_study/pids.txt",
            "ncf/ncf_approved.txt",
        ]

    if not attacks:
        attacks = ["cadv", "semanticadv", "ncf"]

    for i, filename in enumerate(filenames):
        with open(dir + filename, "r") as file:
            pids = file.readlines()
            pids = [pid.strip() for pid in pids]
            pids_per_attack[attacks[i]] = pids
    
    return pids_per_attack


if __name__ == "__main__":
    #get_annotations("Real Image")
    
    #export_real_images("/home/dren.fazlija/data/Scooter/exported_data/annotations/real_images/", download_images=False)

    filenames = [
        #"semanticadv/pids.txt",
        #"cadv/pids.txt",
        #"ncf/pids.txt",
        #"diffattack/pids.txt",
        #"advpp/pids.txt",
        "aca/pids.txt",
    ]

    pids_per_attack = get_all_pids("/home/dren.fazlija/data/Scooter/pids/", filenames=filenames, attacks=["aca"])
    # Combine all pids for real images annotations
    all_pids = []
    for key in pids_per_attack:
        all_pids += pids_per_attack[key]

    print(len(all_pids))

    #map_original_names("/home/dren.fazlija/data/Scooter/Salman2020Do_R50_v3", "/home/dren.fazlija/data/Scooter/attacks/real_images")
    #rename_img_files("/home/dren.fazlija/data/Scooter/attacks/semadv", "/home/dren.fazlija/data/Scooter/Salman2020Do_R50_v3/name_pairs.csv")
    
    #export_real_images("/home/dren.fazlija/data/Scooter/exported_data/annotations/real_images/", all_pids, download_images=False)

    #for attack in pids_per_attack:
        #export_modified_images("/home/dren.fazlija/data/Scooter/exported_data/annotations/modified_images/", pids_per_attack[attack], attack, "Salman2020Do_R50", download_images=True)
    
    #export_imc_ratings("/home/dren.fazlija/data/Scooter/exported_data/annotations/attention_check_images/instruction_manipulation_checks/", all_pids, download_images=False)
    #export_atc_ratings("/home/dren.fazlija/data/Scooter/exported_data/annotations/attention_check_images/bogus_items/", all_pids, download_images=False)
    #export_ishihara_ratings("/home/dren.fazlija/data/Scooter/exported_data/annotations/colorblind/", all_pids, download_images=True)

    #for key in pids_per_attack:
        #export_ratings_of_experiment(pids_per_attack[key], "/home/dren.fazlija/data/Scooter/attacks/" + key + "_with_image_ids_new", with_image_ids=True)

    try:
        conn = database_connection()
        cur = conn.cursor()

        main_path = "/home/dren.fazlija/data/Scooter/attacks/"

        subdirs = [
            "aca",
        ]

        for subdir in subdirs:
            path = main_path + subdir
            images = os.listdir(path)
            pids = None
            if subdir == "real_images":
                category = "Real Image"
                pids = all_pids
            else:
                category = "Modified Image"
                if subdir == "ncf_v3":
                    pids = pids_per_attack["ncf"]
                else:
                    pids = pids_per_attack[subdir]
            annotate_external_dataset(images, path, cur, pids, model_name="Salman2020Do_R50", category=category)
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    
    finally:
        cur.close()
        conn.close()
