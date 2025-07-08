from db_utils import database_connection
import psycopg2
import sys
import datetime
from scipy.stats import mannwhitneyu, chi2, zscore, pearsonr
import scipy.stats as stats
import numpy as np
from tqdm import tqdm
import os
import pandas as pd
import time
from scipy.spatial.distance import mahalanobis
from scipy.linalg import inv
from utils import draw_chart


def get_ratings(pid):
    try:
        connection = database_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT main_study_answers, real_indices, modified_indices, imc_indices, atc_indices, correct_imc_values 
                          FROM participants WHERE pid = %s""", (pid,))
        data = cursor.fetchall()
        return data
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            #print("PostgreSQL connection is closed")

def get_main_study_ratings(pid):
    data = get_ratings(pid)
    if data:
        main_study_answers = data[0][0]
        real_indices = data[0][1]
        modified_indices = data[0][2]

        imc_indices = data[0][3]
        atc_indices = data[0][4]

        # Drop all ratings that are either on imc or atc indices
        main_study_answers = [main_study_answers[i] for i in range(len(main_study_answers)) if i not in imc_indices and i not in atc_indices]
        return main_study_answers

def get_colorblind_answers(pid):
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT colorblind_answers, correct_digits, ishihara_test_cards 
                    FROM participants WHERE pid = %s""", (pid,))

        data = cur.fetchall()
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
        return data
    
def get_comprehension_check_answers(pid):
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT comprehension_check_answers, comprehension_check_images, correct_comprehension_check_answers 
                    FROM participants WHERE pid = %s""", (pid,))

        data = cur.fetchall()
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
        return data

def process_ratings(pid, post_hoc=True):

    data = get_ratings(pid)
    if data:
        main_study_answers = data[0][0]
        real_indices = data[0][1]
        modified_indices = data[0][2]
        imc_indices = data[0][3]
        atc_indices = data[0][4]
        correct_imc_values = data[0][5]

        #print(correct_imc_values)
        
        accuracy = 0
        imc_performance = 0
        atc_performance = 0
        imc_index = 0
        atc_index = 0

        wrong_indices = []
        wrong_ratings = []

        wrong_answers_real = 0
        wrong_answers_modified = 0

        if main_study_answers is None:
            print("No data found for the given pid")
            return None

        for i in range(len(main_study_answers)):

            current_answer = int(main_study_answers[i])

            if i in real_indices:
                if current_answer > 0:
                    accuracy += 1
                else:
                    wrong_answers_real += 1
                    wrong_indices.append(i)
                    wrong_ratings.append(current_answer)
            
            elif i in modified_indices:
                if current_answer < 0:
                    accuracy += 1
                else:
                    wrong_answers_modified += 1
                    wrong_indices.append(i)
                    wrong_ratings.append(current_answer)
            
            elif i in atc_indices: 
                atc_index += 1
                if post_hoc:
                    print("ATC:", atc_index, "Answer:", current_answer)
                if current_answer < 0:
                    atc_performance += 1
            
            elif i in imc_indices and correct_imc_values is not None: 
                # Get position of value i in imc_indices
                pos = imc_indices.index(i)
                if int(current_answer) == int(correct_imc_values[pos]):
                    imc_performance += 1
                else:
                    if post_hoc:
                        print("IMC:", imc_index, "Answer:", current_answer, "Correct:", correct_imc_values[pos])
                imc_index += 1

            
        accuracy = accuracy / (len(main_study_answers) - len(imc_indices) - len(atc_indices))
        accuracy = round(accuracy, 2)

        real_accuracy = round((len(real_indices) - wrong_answers_real) / len(real_indices), 2)
        modified_accuracy = round((len(modified_indices) - wrong_answers_modified) / len(modified_indices), 2)
        check_accuracy = round((imc_performance + atc_performance) / (len(imc_indices) + len(atc_indices)), 2)
        
        user_data = [pid, accuracy, real_accuracy, modified_accuracy, check_accuracy]

        if not post_hoc:
            return user_data

        accuracy = accuracy * 100

        print("You graded", len(main_study_answers), "out of 106 images.")
        print("Accuracy on the main", len(main_study_answers) - len(imc_indices) - len(atc_indices) ,"images: {:.2f}".format(accuracy), "%")
        print("Accuracy on real images: {:.2f}".format((len(real_indices) - wrong_answers_real) / len(real_indices) * 100), "%")
        print("Accuracy on modified images: {:.2f}".format((len(modified_indices) - wrong_answers_modified) / len(modified_indices) * 100), "%")
        if correct_imc_values is not None:
            print("IMC Performance:", imc_performance, "/", imc_index)
        print("ATC Performance:", atc_performance, "/", atc_index)

        if len(wrong_indices) > 0:
            print("Wrongly rated main study images:")
            for i in range(len(wrong_indices)):
                print("Image", wrong_indices[i], "was rated as", wrong_ratings[i])
        
        return wrong_indices, real_indices, modified_indices

    else:
        print("No data found for the given pid")
        return None


from PIL import Image
import matplotlib.pyplot as plt
from io import BytesIO

def display_image_from_bytes(image_bytes):
    # Convert bytes data to PIL Image
    image = Image.open(BytesIO(image_bytes))

    # Display the image
    plt.imshow(image)
    plt.axis('off')  # Hide the axis
    plt.show()

def get_comprehension_check_image(id):
    try:
        connection = database_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT * 
                          FROM comprehension_check_images 
                          WHERE id = %s""", (id,))
        
        output = cursor.fetchall()
        row = output[0]
        if row:
            image = row[1]
            is_modified = row[2]
            modification = row[3]
            obj_class = row[4]
            image_number = row[5]
            
            print("Object class:", obj_class)

            if is_modified:
                print("Modification:", modification)
            
            else:
                print("This is a real image")

            print("Image number:", image_number)
            
            display_image_from_bytes(image)

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

def get_colorblind_image(id):
    try:
        connection = database_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT * 
                          FROM ishihara_test_cards 
                          WHERE id = %s""", (id,))
        
        output = cursor.fetchall()
        row = output[0]
        if row:
            image = row[1]
            color_type = row[2]
            digit = row[3]
            
            print("Color Type:", color_type)

            print("Correct Digit:", digit)
            
            display_image_from_bytes(image)

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

def get_wrong_image(index, pid):
    try:
        connection = database_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT main_study_images, real_indices, modified_indices 
                          FROM participants WHERE pid = %s""", (pid,))
        
        data = cursor.fetchall()
        if data:
            img_ids = data[0][0]
            real_indices = data[0][1]
            modified_indices = data[0][2]

            if index in real_indices:
                
                cursor.execute("""SELECT image 
                                  FROM real_images 
                                  WHERE id = %s""", (img_ids[index],))
                image = cursor.fetchall()

                display_image_from_bytes(image[0][0])
                return None


            elif index in modified_indices:
                cursor.execute("""SELECT image 
                                  FROM modified_images 
                                  WHERE id = %s""", (img_ids[index],))
                image = cursor.fetchall()

                display_image_from_bytes(image[0][0])
                return None

            else:
                return None
        else:
            return None

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")


def site_time_tracking(pid, verbose=False):
    domain = "http://scooter.l3s.uni-hannover.de/"
    parameter = "?PROLIFIC_PID="
    print("Current user:", pid[0])
    try:
        connection = database_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT url, time 
                          FROM site_logs WHERE pid = %s""", (pid,))
        
        data = cursor.fetchall()
        
        for i in range(len(data) - 1):
            url = data[i][0]
            time_of_arrival = data[i][1]
            time_of_departure = data[i+1][1]

            # Get the time spent on the site
            time_spent = time_of_departure - time_of_arrival

            hours, remainder = divmod(time_spent.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Get everything between the domain string and the parameter string
            start_index = len(domain)
            end_index = url.find(parameter)

            if verbose:
                print("Time spent on", url[start_index:end_index], ":", hours, "hours", minutes, "minutes", seconds, "seconds")

        total_time = data[-1][1] - data[0][1]
        hours, remainder = divmod(total_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        print("Total time spent on the site:", hours, "hours", minutes, "minutes", seconds, "seconds")

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

def image_time_tracking(pid, verbose=False):
    try:
        connection = database_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT index, time 
                          FROM image_logs WHERE pid = %s""", (pid,))
        
        data = cursor.fetchall()

        print("Current user:", pid[0])

        # Important: You need to escape the % character in the like clause!
        cursor.execute("""SELECT max(time)
                           FROM site_logs 
                           WHERE pid = %s
                           and url like '%%main-study?%%'""", (pid,))

        max_time = cursor.fetchall()
        #print(max_time)
        
        for i in range(len(data)):
            image = data[i][0]
            time_of_arrival = data[i][1]
            if i == len(data) - 1:
                time_of_departure = max_time[0][0]
            else:
                time_of_departure = data[i+1][1]

            # Get the time spent on the site
            time_spent = time_of_departure - time_of_arrival

            hours, remainder = divmod(time_spent.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if verbose:
                print("Time spent on image", image, ":", hours, "hours", minutes, "minutes", seconds, "seconds")
        
        total_time = max_time[0][0] - data[0][1]
        average_time = total_time.seconds / len(data)
        average_seconds = round(average_time)
        average_ms = round((average_time - average_seconds) * 1000)
        print("Average time spent on each image:", average_seconds, "seconds", average_ms, "ms")

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

def get_leaderboard_pids():
    try:
        connection = database_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT id 
                          FROM leaderboard""")
        
        pids = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
        return None

    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
        return pids

def get_main_study_image_ids(pid):
    try:
        connection = database_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT main_study_images 
                          FROM participants WHERE pid = %s""", (pid,))
        
        data = cursor.fetchall()
        if data:
            return data[0][0]
        else:
            return None

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

def get_ratings_per_image(pids, format="table", filename="ratings_ijcv.csv"):
    real_images_ratings = {}
    modified_images_ratings = {}
    attention_check_ratings = {}
    imc_ratings = {}
    try:
        connection = database_connection()
        cursor = connection.cursor()

        # Get all real image ids
        cursor.execute("""SELECT id 
                          FROM real_images""")
        real_image_ids = cursor.fetchall()
        # Initialize dictionary with image ids as keys and empty lists as values
        for image_id in real_image_ids:
            real_images_ratings[image_id[0]] = []
        
        # Get all modified image ids
        cursor.execute("""SELECT id 
                          FROM modified_images""")
        modified_image_ids = cursor.fetchall()
        # Initialize dictionary with image ids as keys and empty lists as values
        for image_id in modified_image_ids:
            modified_images_ratings[image_id[0]] = []
        
        # Get all attention check image ids
        cursor.execute("""SELECT id 
                          FROM attention_check_images
                          WHERE is_imc = False""")
        attention_check_image_ids = cursor.fetchall()
        # Initialize dictionary with image ids as keys and empty lists as values
        for image_id in attention_check_image_ids:
            attention_check_ratings[image_id[0]] = []
        
        # Get all imc image ids
        cursor.execute("""SELECT id
                        FROM attention_check_images
                        WHERE is_imc = True""")
        imc_image_ids = cursor.fetchall()
        # Initialize dictionary with image ids as keys and empty lists as values
        for image_id in imc_image_ids:
            imc_ratings[image_id[0]] = []

        for pid in tqdm(pids):
            #pid = pid[0]
            data = get_ratings(pid)
            main_study_image_ids = get_main_study_image_ids(pid)

            if data:
                main_study_answers = data[0][0]
                real_indices = data[0][1]
                modified_indices = data[0][2]
                imc_indices = data[0][3]
                atc_indices = data[0][4]

                for i in range(len(main_study_answers)):
                    if i in real_indices:
                        real_images_ratings[main_study_image_ids[i]].append((pid, int(main_study_answers[i])))
                    elif i in modified_indices:
                        modified_images_ratings[main_study_image_ids[i]].append((pid, int(main_study_answers[i])))
                    elif i in atc_indices:
                        attention_check_ratings[main_study_image_ids[i]].append((pid, int(main_study_answers[i])))
                    elif i in imc_indices:
                        # check if key exists -- if not: add it + empty list
                        if main_study_image_ids[i] not in imc_ratings:
                            imc_ratings[main_study_image_ids[i]] = []

                        imc_ratings[main_study_image_ids[i]].append((pid, int(main_study_answers[i])))
                    else:
                        print("Error: Image index not found in any category")
                        return None
            else:
                print("No data found for the given pid")
                return None
        
        #write_ratings_to_file(real_images_ratings, modified_images_ratings, attention_check_ratings, imc_ratings, pids)
        
        if format == "table":
            add_to_ratings_table(real_images_ratings, modified_images_ratings, attention_check_ratings, imc_ratings, pids)
        elif format == "csv":
            write_ratings_to_file(real_images_ratings, modified_images_ratings, attention_check_ratings, imc_ratings, pids, filename)

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
        return None

    finally:
        if connection:
            cursor.close()
            connection.close()
            #print("PostgreSQL connection is closed")

def add_to_ratings_table(real_images_ratings, modified_images_ratings, attention_check_ratings, imc_ratings, pids):
    # Create a table to store all the ratings
    try:
        connection = database_connection()
        cursor = connection.cursor()

        for image_id, ratings in real_images_ratings.items():
            for rating in ratings:
                cursor.execute("""INSERT INTO ratings (image_id, category, pid, rating) VALUES (%s, %s, %s, %s)""", (image_id, "Real Image", rating[0], rating[1]))
        
        for image_id, ratings in modified_images_ratings.items():
            for rating in ratings:
                cursor.execute("""INSERT INTO ratings (image_id, category, pid, rating) VALUES (%s, %s, %s, %s)""", (image_id, "Modified Image", rating[0], rating[1]))
        
        for image_id, ratings in attention_check_ratings.items():
            for rating in ratings:
                cursor.execute("""INSERT INTO ratings (image_id, category, pid, rating) VALUES (%s, %s, %s, %s)""", (image_id, "ATC", rating[0], rating[1]))
        
        for image_id, ratings in imc_ratings.items():
            for rating in ratings:
                cursor.execute("""INSERT INTO ratings (image_id, category, pid, rating) VALUES (%s, %s, %s, %s)""", (image_id, "IMC", rating[0], rating[1]))
        
        connection.commit()
        print("Data inserted successfully in PostgreSQL ")

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
        return None

    finally:
        if connection:
            cursor.close()
            connection.close()
            #print("PostgreSQL connection is closed")

def write_ratings_to_file(real_images_ratings, modified_images_ratings, attention_check_ratings, imc_ratings, pids, filename="ratings.csv"):
    # Create a csv file to store all the ratings
    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, 'w') as file:
        file.write("Image ID, Category, PID, Rating\n")
        for image_id, ratings in real_images_ratings.items():
            for rating in ratings:
                file.write(f"{image_id}, Real Image, {rating[0]}, {rating[1]}\n")
        for image_id, ratings in modified_images_ratings.items():
            for rating in ratings:
                file.write(f"{image_id}, Modified Image, {rating[0]}, {rating[1]}\n")
        for image_id, ratings in attention_check_ratings.items():
            for rating in ratings:
                file.write(f"{image_id}, ATC, {rating[0]}, {rating[1]}\n")
        for image_id, ratings in imc_ratings.items():
            for rating in ratings:
                file.write(f"{image_id}, IMC, {rating[0]}, {rating[1]}\n")

def get_sample_averages(pids=None, only_arrays=False):
    real_images_ratings = []
    modified_images_ratings = []

    if pids is None:
        try:
            connection = database_connection()
            cursor = connection.cursor()
            cursor.execute("""SELECT id 
                            FROM leaderboard""")
            
            pids = cursor.fetchall()
            print(pids)

        except (Exception, psycopg2.Error) as error:
            print("Error while fetching data from PostgreSQL", error)
            return None
        finally:
            if connection:
                cursor.close()
                connection.close()
                #print("PostgreSQL connection is closed")

    for pid in pids:
        data = get_ratings(pid)
        if data:
            main_study_answers = data[0][0]
            real_indices = data[0][1]
            modified_indices = data[0][2]
            for i in range(len(main_study_answers)):
                if i in real_indices:
                    real_images_ratings.append(int(main_study_answers[i]))
                elif i in modified_indices:
                    modified_images_ratings.append(int(main_study_answers[i]))
    
    if only_arrays:
        #ratings = np.concatenate((real_images_ratings, modified_images_ratings))
        #group_real = [0] * len(real_images_ratings)
        #group_modified = [1] * len(modified_images_ratings)
        #grouping = np.concatenate((group_real, group_modified))
        return real_images_ratings, modified_images_ratings

    real_images_ratings = np.array(real_images_ratings)
    real_images_mean = np.mean(real_images_ratings)
    real_images_sd = np.std(real_images_ratings, ddof=1)

    modified_images_ratings = np.array(modified_images_ratings)
    modified_images_mean = np.mean(modified_images_ratings)
    modified_images_sd = np.std(modified_images_ratings, ddof=1)

    return real_images_mean, real_images_sd, modified_images_mean, modified_images_sd
    
def get_total_time(pid):
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT max(time) - min(time) from site_logs WHERE pid = %s""", (pid,))
        result = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
        return result[0][0]

def get_average_image_time(pid):
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT (max(time) - min(time)) / 106 from image_logs WHERE pid = %s""", (pid,))
        result = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
        return result[0][0]


def population_std(times_array, sample_mean):
    N = len(times_array)
    mean_in_seconds = sample_mean.total_seconds()
    sum = 0
    for time in times_array:
        time = time.total_seconds()
        sum += (time - mean_in_seconds) ** 2
    sum_in_seconds = np.sqrt(sum / (N - 1))
    return datetime.timedelta(seconds=sum_in_seconds)


def get_time_stats(pids, verbose=False, percentiles=False):
    total_times = []
    average_image_times = []
    for pid in pids:
        time = get_total_time(pid)
        if time.total_seconds() > 3600:
            print("User with PID", pid, "was excluded due to being a clear outlier:", time)
        else:
            total_times.append(get_total_time(pid))
            average_image_times.append(get_average_image_time(pid))
    
    print("Total amount of users:", len(total_times))

    mean_total_time = np.mean(total_times)
    median_total_time = np.median(total_times)
    min_total_time = np.min(total_times)
    max_total_time = np.max(total_times)
    sd_total_time = population_std(total_times, mean_total_time)

    mean_average_image_time = np.mean(average_image_times)
    median_average_image_time = np.median(average_image_times)
    min_average_image_time = np.min(average_image_times)
    max_average_image_time = np.max(average_image_times)
    sd_average_image_time = population_std(average_image_times, mean_average_image_time)

    if verbose:
        print("Total Time Stats")
        print("Total Time Mean:", mean_total_time)
        print("Total Time Median:", median_total_time)
        print("Total Time Min:", min_total_time)
        print("Total Time Max:", max_total_time)
        print("Total Time SD:", sd_total_time)
        print("")

        print("Average Image Time Stats")
        print("Average Image Time Mean:", mean_average_image_time)
        print("Average Image Time Median:", median_average_image_time)
        print("Average Image Time Min:", min_average_image_time)
        print("Average Image Time Max:", max_average_image_time)
        print("Average Image Time SD:", sd_average_image_time)

    if percentiles:
        # Get 10th, 5th and 1st percentiles of total time on site and time per image
        total_time_10 = np.percentile(total_times, 10)
        total_time_5 = np.percentile(total_times, 5)
        total_time_1 = np.percentile(total_times, 1)

        average_image_time_10 = np.percentile(average_image_times, 10)
        average_image_time_5 = np.percentile(average_image_times, 5)
        average_image_time_1 = np.percentile(average_image_times, 1)

        print("Total Time 10th Percentile:", total_time_10)
        print("Total Time 5th Percentile:", total_time_5)
        print("Total Time 1st Percentile:", total_time_1)

        print("Average Image Time 10th Percentile:", average_image_time_10)
        print("Average Image Time 5th Percentile:", average_image_time_5)
        print("Average Image Time 1st Percentile:", average_image_time_1)

    return mean_total_time, median_total_time, min_total_time, max_total_time, sd_total_time, mean_average_image_time, median_average_image_time, min_average_image_time, max_average_image_time, sd_average_image_time

# Conservative Mann-Whitney-U sample size estimation as described in:
# Section 3 of "Sample Size Determination for Some Common Nonparametric Tests" (Noether, 1987)
# Code based on R implementation from https://rdrr.io/cran/rankFD/src/R/samplesize.R

def noether(alpha, power, p, t=0.5):
    # Input validation
    assert 0 < alpha < 1, "alpha must be between 0 and 1"
    assert power > 0, "power must be greater than 0"
    assert 0 < t < 1, "t must be between 0 and 1"
    assert 0 < p < 1, "p must be between 0 and 1"

    # Calculate Nu based on the simplified assumptions
    Nu = (stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)) ** 2 * 1 / (12 * t * (1 - t) * (p - 0.5) ** 2)
    n1u = Nu * t
    n2u = Nu * (1 - t)
    
    # Output the results
    output = np.array([alpha, power, p, Nu, t, n1u, n2u, np.ceil(n1u) + np.ceil(n2u), np.ceil(n1u), np.ceil(n2u)])
    output_matrix = output.reshape(-1, 1)
    
    row_names = ["alpha (2-sided)", "Power", "relevant relative effect p", "N (total sample size needed)", "t=n1/N", 
                 "n1 in Group 1", "n2 in Group 2", "N rounded", "n1 rounded", "n2 rounded"]
    
    return output_matrix, row_names

def are_method(mean_1, mean_2, std_1, std_2):
    std_prime = np.sqrt((std_1 ** 2 + std_2 ** 2) / 2)
    effect_size = abs(mean_1 - mean_2) / std_prime
    return effect_size


def subsampling(pids, sample_size, number_of_sets, seed=0):
    # The binomial coefficient of C(75, 60) is too high for practical assessments
    # Therefore, we will use a subsampling method to reduce the number of possible combinations
    # We will take a sample of 60 images from the 75 available images
    # We will repeat this process 'number_of_sets' times

    # Create a list to store the subsampled data
    subsampled_data = []

    # Set the seed for reproducibility
    rng = np.random.default_rng(seed)

    for _ in range(number_of_sets):
        # Randomly select 60 indices from the list of indices
        subsample = rng.choice(pids, sample_size, replace=False)
        # Append the selected indices to the subsampled data
        subsampled_data.append(subsample)

    return subsampled_data

def long_string(ratings, sequences=None):
    if sequences is None:
        sequences = {}
    current_val = ratings[0]
    current_count = 1
    for i in range(1, len(ratings)):
        if ratings[i] == current_val:
            current_count += 1
        else:
            if current_count not in sequences:
                sequences[current_count] = 1
            else:
                sequences[current_count] += 1
            
            current_val = ratings[i]
            current_count = 1
    
    seq_lengths = []
    for key in sequences.keys():
        seq_lengths += [key] * sequences[key]

    
    return sequences, max(seq_lengths), np.mean(seq_lengths), np.median(seq_lengths)

def accumulate_ls_stats(pids, visualize=False, previous_means=None, save=False):
    sequences = {}
    max_seq_length = 0
    for pid in pids:
        ratings = get_main_study_ratings(pid)
        sequences, current_max, mean_seq_length, median_seq_length = long_string(ratings, sequences)
        if current_max > max_seq_length:
            max_seq_length = current_max
    
    if visualize:
        draw_chart(sequences, mean_seq_length, median_seq_length, save=True, previous_means=previous_means)
        print("Sequences:", sequences)
        print("Max Sequence Length:", max_seq_length)
        print("Mean Sequence Length:", mean_seq_length)
        print("Median Sequence Length:", median_seq_length)
        return None

    return sequences, max_seq_length, mean_seq_length, median_seq_length

def ls_percentiles(pids):
    max_seq_lengths = []
    mean_seq_lengths = []
    median_seq_lengths = []
    for pid in pids:
        ratings = get_main_study_ratings(pid)
        _, max_seq, mean_seq, median_seq = long_string(ratings)
        max_seq_lengths.append(max_seq)
        mean_seq_lengths.append(mean_seq)
        median_seq_lengths.append(median_seq)
    
    np_max_seq_lengths = np.array(max_seq_lengths)
    np_mean_seq_lengths = np.array(mean_seq_lengths)
    np_median_seq_lengths = np.array(median_seq_lengths)

    # Get the different percentiles of the max sequence lengths
    max_seq_25 = np.percentile(np_max_seq_lengths, 25)
    max_seq_50 = np.percentile(np_max_seq_lengths, 50)
    max_seq_75 = np.percentile(np_max_seq_lengths, 75)
    # Get the different percentiles of the mean sequence lengths
    mean_seq_25 = np.percentile(np_mean_seq_lengths, 25)
    mean_seq_50 = np.percentile(np_mean_seq_lengths, 50)
    mean_seq_75 = np.percentile(np_mean_seq_lengths, 75)
    # Get the different percentiles of the median sequence lengths
    median_seq_25 = np.percentile(np_median_seq_lengths, 25)
    median_seq_50 = np.percentile(np_median_seq_lengths, 50)
    median_seq_75 = np.percentile(np_median_seq_lengths, 75)

    # Get minimum, maximum and median of the max sequence lengths
    max_seq_min = np.min(np_max_seq_lengths)
    max_seq_max = np.max(np_max_seq_lengths)
    max_seq_median = np.median(np_max_seq_lengths)
    # Get minimum, maximum and median of the mean sequence lengths
    mean_seq_min = np.min(np_mean_seq_lengths)
    mean_seq_max = np.max(np_mean_seq_lengths)
    mean_seq_median = np.median(np_mean_seq_lengths)
    # Get minimum, maximum and median of the median sequence lengths
    median_seq_min = np.min(np_median_seq_lengths)
    median_seq_max = np.max(np_median_seq_lengths)
    median_seq_median = np.median(np_median_seq_lengths)

    # Get the ranges that cover 85%, 90%, 95% and 99% of the data
    max_seq_85 = np.percentile(np_max_seq_lengths, 85)
    max_seq_90 = np.percentile(np_max_seq_lengths, 90)
    max_seq_95 = np.percentile(np_max_seq_lengths, 95)
    max_seq_99 = np.percentile(np_max_seq_lengths, 99)
    mean_seq_85 = np.percentile(np_mean_seq_lengths, 85)
    mean_seq_90 = np.percentile(np_mean_seq_lengths, 90)
    mean_seq_95 = np.percentile(np_mean_seq_lengths, 95)
    mean_seq_99 = np.percentile(np_mean_seq_lengths, 99)
    median_seq_85 = np.percentile(np_median_seq_lengths, 85)
    median_seq_90 = np.percentile(np_median_seq_lengths, 90)
    median_seq_95 = np.percentile(np_median_seq_lengths, 95)
    median_seq_99 = np.percentile(np_median_seq_lengths, 99)

    # Print the results
    print("Max Sequence Lengths")
    print("25th Percentile:", max_seq_25)
    print("50th Percentile:", max_seq_50)
    print("75th Percentile:", max_seq_75)
    print("Min:", max_seq_min)
    print("Max:", max_seq_max)
    print("Median:", max_seq_median)
    print("85th Percentile:", max_seq_85)
    print("90th Percentile:", max_seq_90)
    print("95th Percentile:", max_seq_95)
    print("99th Percentile:", max_seq_99)
    print("")
    print("Mean Sequence Lengths")
    print("25th Percentile:", mean_seq_25)
    print("50th Percentile:", mean_seq_50)
    print("75th Percentile:", mean_seq_75)
    print("Min:", mean_seq_min)
    print("Max:", mean_seq_max)
    print("Median:", mean_seq_median)
    print("85th Percentile:", mean_seq_85)
    print("90th Percentile:", mean_seq_90)
    print("95th Percentile:", mean_seq_95)
    print("99th Percentile:", mean_seq_99)
    print("")
    print("Median Sequence Lengths")
    print("25th Percentile:", median_seq_25)
    print("50th Percentile:", median_seq_50)
    print("75th Percentile:", median_seq_75)
    print("Min:", median_seq_min)
    print("Max:", median_seq_max)
    print("Median:", median_seq_median)
    print("85th Percentile:", median_seq_85)
    print("90th Percentile:", median_seq_90)
    print("95th Percentile:", median_seq_95)
    print("99th Percentile:", median_seq_99)

def export_study_data_numba(pids, path):
    order_ratings = []
    real_ratings = []
    modified_ratings = []
    total_times = []
    average_image_times = []

    for pid in pids:
        
        order_ratings.append(get_main_study_ratings(pid))
        r_pid, m_pid = get_sample_averages([pid], only_arrays=True)
        real_ratings.append(r_pid)
        modified_ratings.append(m_pid)

        total_times.append(get_total_time(pid))
        average_image_times.append(get_average_image_time(pid))

    # Turn all involved arrays - including pids - into numpy arrays
    pids = np.array(pids)
    order_ratings = np.array(order_ratings)
    real_ratings = np.array(real_ratings)
    modified_ratings = np.array(modified_ratings)
    total_times = np.array(total_times)
    average_image_times = np.array(average_image_times)

    now = int(round(time.time() * 1000))
    filename = f"{path}/{now}_exported_data.npz"

    # Save the data to disk
    np.savez(filename, pids=pids, order_ratings=order_ratings, real_ratings=real_ratings, modified_ratings=modified_ratings, total_times=total_times, average_image_times=average_image_times)

def study_overview(pids, sample_size, number_of_sets, seed=0, path=None, verbose=False, checkpoint=None, early_stop=None, previous_file=None):
    subsamples = subsampling(pids, sample_size, number_of_sets, seed)
    header = [
        "Real Images Mean", "Real Images SD", "Modified Images Mean", "Modified Images SD",
        "P(X > Y)", "U", "P-Value", "Z", "Effect Size (PCC)", "Effect Size (A.R.E)",
        "Required Sample Size (Noether)", "Required Sample Size (A.R.E.)",
        "Total Time Mean", "Total Time Median", "Total Time Min", "Total Time Max", "Total Time SD",
        "Average Image Time Mean", "Average Image Time Median", "Average Image Time Min", "Average Image Time Max", "Average Image Time SD",
        "Max Sequence Length", "Mean Sequence Length", "Median Sequence Length"
    ]


    start = 0 if checkpoint is None else checkpoint
    end = number_of_sets if early_stop is None else early_stop
    subsamples = subsamples[start:end]
    
    if path is not None:
        now = int(round(time.time() * 1000))
        filename = f"{path}/{now}_overview.csv" if previous_file is None else f"{path}/{previous_file}"
        mode = 'a' if previous_file is not None else 'w'
        with open(filename, mode) as file:
            if previous_file is None:
                file.write(",".join(header) + "\n")
            for subsample in tqdm(subsamples):
                entries = list(subsample)
                x, y = get_sample_averages(entries, only_arrays=True)

                real_images_mean = np.mean(x)
                real_images_sd = np.std(x, ddof=1)

                modified_images_mean = np.mean(y)
                modified_images_sd = np.std(y, ddof=1)

                U1, p = mannwhitneyu(x, y)
                p_x_greater_y = U1 / (len(x) * len(y))
                U2 = len(x) * len(y) - U1
                U = min(U1, U2)
                z = (U - len(x) * len(y) / 2) / np.sqrt(len(x) * len(y) * (len(x) + len(y) + 1) / 12)
                effect_size = abs(z) / np.sqrt(len(x) + len(y))
                effect_size_are = are_method(real_images_mean, modified_images_mean, real_images_sd, modified_images_sd)

                result, _ = noether(alpha=0.01, power=0.95, p=p_x_greater_y)

                sample_size_are = None
                sequences, max_seq_length, mean_seq_length, median_seq_length = accumulate_ls_stats(entries)

                total_time_mean, total_time_median, total_time_min, total_time_max, total_time_sd, average_image_time_mean, average_image_time_median, average_image_time_min, average_image_time_max, average_image_time_sd = get_time_stats(entries)

                file.write(f"{real_images_mean},{real_images_sd},{modified_images_mean},{modified_images_sd},{p_x_greater_y},{U},{p},{z},{effect_size},{effect_size_are},{int(result[-1][0])},{sample_size_are},{total_time_mean},{total_time_median},{total_time_min},{total_time_max},{total_time_sd},{average_image_time_mean},{average_image_time_median},{average_image_time_min},{average_image_time_max},{average_image_time_sd},{max_seq_length},{mean_seq_length},{median_seq_length}\n")
    
    elif verbose:
        
        for subsample in subsamples:
            entries = list(subsample)
            x, y = get_sample_averages(entries, only_arrays=True)

            real_images_mean = np.mean(x)
            real_images_sd = np.std(x, ddof=1)

            modified_images_mean = np.mean(y)
            modified_images_sd = np.std(y, ddof=1)

            
            print("Real Images Mean:", real_images_mean)
            print("Real Images SD:", real_images_sd)
            print("Modified Images Mean:", modified_images_mean)
            print("Modified Images SD:", modified_images_sd)

            U1, p = mannwhitneyu(x, y)
            p_x_greater_y = U1 / (len(x) * len(y))
            U2 = len(x) * len(y) - U1
            U = min(U1, U2)
            z = (U - len(x) * len(y) / 2) / np.sqrt(len(x) * len(y) * (len(x) + len(y) + 1) / 12)
            effect_size = abs(z) / np.sqrt(len(x) + len(y))
            effect_size_are = are_method(real_images_mean, modified_images_mean, real_images_sd, modified_images_sd)

            print("P(X > Y):", p_x_greater_y)
            print("U:", U)
            print("P-Value:", p)
            print("Z:", z)
            # effect size = z / sqrt(N)
            print("Effect Size:", effect_size)
            print("Effect Size (A.R.E.):", effect_size_are)

            result, _ = noether(alpha=0.01, power=0.95, p=p_x_greater_y)
            sample_size_are = None
            sequences, max_seq_length, mean_seq_length, median_seq_length = accumulate_ls_stats(entries)
            

        
            print(f"Required sample size for each group (Noether): {int(result[-1][0])}")
            print(f"Required sample size for each group (A.R.E.): {sample_size_are}")
            print("")
            get_time_stats(entries, verbose=verbose)
            print("")
            print("Long String Stats")
            print("Sequences:", sequences)
            print("Max Sequence Length:", max_seq_length)
            print("Mean Sequence Length:", mean_seq_length)
            print("Median Sequence Length:", median_seq_length)

            print("--------------------------------------------------\n")

def population_overview(pids):
    x, y = get_sample_averages(pids, only_arrays=True)

    real_images_ratings = np.array(x)
    real_images_mean = np.mean(x)
    real_images_sd = np.std(x, ddof=1)

    modified_images_ratings = np.array(y)
    modified_images_mean = np.mean(y)
    modified_images_sd = np.std(y, ddof=1)

    print("Real Images Mean:", real_images_mean)
    print("Real Images SD:", real_images_sd)
    print("Modified Images Mean:", modified_images_mean)
    print("Modified Images SD:", modified_images_sd)

    U1, p = mannwhitneyu(x, y)
    p_x_greater_y = U1 / (len(x) * len(y))
    U2 = len(x) * len(y) - U1
    print("P(X > Y):", p_x_greater_y)
    U = min(U1, U2)
    print("U:", U)
    print("P-Value:", p)
    z = (U - len(x) * len(y) / 2) / np.sqrt(len(x) * len(y) * (len(x) + len(y) + 1) / 12)
    print("Z:", z)

    effect_size = abs(z) / np.sqrt(len(x) + len(y))
    # effect size = z / sqrt(N)
    print("Effect Size:", effect_size)

    result, _ = noether(alpha=0.01, power=0.95, p=p_x_greater_y)
    print(f"Required sample size for each group: {int(result[-1][0])}")

    print("")
    get_time_stats(pids, verbose=True)

    print("")
    sequences, max_seq_length, mean_seq_length, median_seq_length = accumulate_ls_stats(pids)
    print("Long String Stats")
    print("Sequences:", sequences)
    print("Max Sequence Length:", max_seq_length)
    print("Mean Sequence Length:", mean_seq_length)
    print("Median Sequence Length:", median_seq_length)

def get_booleans(pid):
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT attempted_colorblindness, passed_colorblindness, 
                    attempted_comprehension, passed_comprehension, completed_study
                    FROM participants WHERE pid = %s""", (pid,))
        result = cur.fetchone()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
        return result

def get_returned_tasks(file, verbose=False, pids_array = None):
    # Create a dataframe based on the file
    df = pd.read_csv(file)
    
    if pids_array is not None:
        df_approved = df[df['Status'] == 'APPROVED']
        pseudo_approved = df_approved[~df_approved['Participant id'].isin(pids_array)]
        pseudo_pids = pseudo_approved["Participant id"].values
        print("Pseudo PIDs:", pseudo_pids)

    # Only keep entries with a status of "RETURNED" or "AWAITING REVIEW"
    df = df[(df["Status"] == "RETURNED") | (df["Status"] == "AWAITING REVIEW")]

    # Get all the remaining participant ids and store them in an array
    pids = df["Participant id"].values

    rejection_reason = {
        "Did not consent": [],
        "Failed attention check": [],
        "Failed comprehension check": [],
        "Failed colorblindness test": [],
        "Something else": [],
        "Actually passed!": []
    }

    for pid in pids:
        booleans = get_booleans(pid)
        
        if booleans is None:
            rejection_reason["Did not consent"].append(pid)

        elif booleans[1] == False:
            rejection_reason["Failed colorblindness test"].append(pid)
        
        elif booleans[3] == False:
            rejection_reason["Failed comprehension check"].append(pid)

        elif booleans[4] == True:
            user_data = process_ratings(pid, post_hoc=False)
            if user_data == None:
                rejection_reason["Something else"].append(pid)
                print("Main study data not found for PID:", pid)
            elif user_data[-1] <= 0.67:
                rejection_reason["Failed attention check"].append(pid)
        else:
            rejection_reason["Something else"].append(pid)
            print("Check PID:", pid)
    
    if pids_array is not None:
        for pid in pseudo_pids:
            booleans = get_booleans(pid)
        
            if booleans is None:
                rejection_reason["Did not consent"].append(pid)

            elif booleans[1] == False:
                rejection_reason["Failed colorblindness test"].append(pid)
            
            elif booleans[3] == False:
                rejection_reason["Failed comprehension check"].append(pid)

            elif booleans[4] == True:
                user_data = process_ratings(pid, post_hoc=False)
                if user_data[-1] <= 0.67:
                    rejection_reason["Failed attention check"].append(pid)
                else:
                    rejection_reason["Actually passed!"].append(pid)
                    #print("Actually passed:", pid)
            else:
                rejection_reason["Something else"].append(pid)

    if verbose:
        for key in rejection_reason.keys():
            print(key, ":", len(rejection_reason[key]))

    return rejection_reason    

def analyze_subsample_run(file, verbose=False):
    df = pd.read_csv(file)
    
    # Get min and max of each column
    min_values = df.min()
    max_values = df.max()

    print("Min Values")
    print(min_values)
    print("")
    print("Max Values")
    print(max_values)
    print("")

    # Count distinct values for the column "Required Sample Size (Noether)"
    noether_sample_size = df["Required Sample Size (Noether)"].value_counts()
    print("Noether Sample Size")
    print(noether_sample_size)
    print("")

    # Count distinct values for the column "Max Sequence Length"
    max_seq_length = df["Max Sequence Length"].value_counts()
    print("Max Sequence Length")
    print(max_seq_length)

def cb_test_mistakes(pids):
    mistakes = {
        "CB Data was not stored propely": [],
        "User never used the no digit option": [],
        "User just got it wrong": []
    }

    failed_card_ids = {}

    for pid in pids:
        cb_data = get_colorblind_answers(pid)

        answers = cb_data[0][0]
        correct_digits = cb_data[0][1]
        card_ids = cb_data[0][2]
    
        # Case 1: CB were wrongly stored
        if len(answers) != 5:
            mistakes["CB Data was not stored propely"].append(pid)
        
        else:
            if "I don't see a digit" not in answers:
                mistakes["User never used the no digit option"].append(pid)
            
            elif answers != correct_digits:
                mistakes["User just got it wrong"].append(pid)
                for i in range(len(answers)):
                    if answers[i] != correct_digits[i]:
                        solution = "You answered with:" + answers[i] + ". The correct digit is: " + str(correct_digits[i])
                        if card_ids[i] not in failed_card_ids:
                            failed_card_ids[card_ids[i]] = [solution]
                        else:
                            failed_card_ids[card_ids[i]].append(solution)

    return mistakes, failed_card_ids 

def get_comprehension_check_performance(pids):
    performance = {
        "4/6": [],
        "3/6": [],
        "2/6": [],
        "1/6": [],
        "0/6": [],
    }

    wrong_choices = {

    }

    won_comparison = {

    }

    for pid in pids:
        performance_data = get_comprehension_check_answers(pid)[0]
        correct = 0
        for i in range(6):
            if int(performance_data[0][i]) == performance_data[2][i]:
                correct += 1
            else:
                if int(performance_data[0][i]) in wrong_choices:
                    wrong_choices[int(performance_data[0][i])] += 1
                
                if int(performance_data[0][i]) not in wrong_choices:
                    wrong_choices[int(performance_data[0][i])] = 1

                if performance_data[2][i] in won_comparison:
                    won_comparison[performance_data[2][i]] += 1

                if performance_data[2][i] not in won_comparison:
                    won_comparison[performance_data[2][i]] = 1
            
        if correct == 4:
            performance["4/6"].append(pid)
        elif correct == 3:
            performance["3/6"].append(pid)
        elif correct == 2:
            performance["2/6"].append(pid)
        elif correct == 1:
            performance["1/6"].append(pid)
        else:
            performance["0/6"].append(pid)
    
    # Order wrong_choices and won_comparison based on the number of times a choice was made
    wrong_choices = dict(sorted(wrong_choices.items(), key=lambda item: item[1], reverse=True))
    won_comparison = dict(sorted(won_comparison.items(), key=lambda item: item[1], reverse=True))

    return performance, wrong_choices, won_comparison

def get_time_stats_for_phase(pids, phase='comprehension_check'):
    phase_times = []
    for pid in pids:
        if phase == 'comprehension_check':
            phase_time = get_comprehension_check_time(pid)
            if phase_time is not None:
                phase_times.append(phase_time)
            else:
                print("User with PID", pid, "was excluded due to missing data")
        elif phase == 'colorblindness_test':
            phase_time = get_colorblindness_time(pid)
            if phase_time is not None:
                phase_times.append(phase_time)
            else:
                print("User with PID", pid, "was excluded due to missing data")
        else:
            print("Invalid phase")
            return None
    avg_time = np.mean(phase_times)
    median_time = np.median(phase_times)
    min_time = np.min(phase_times)
    max_time = np.max(phase_times)
    
    return phase_times, avg_time, median_time, min_time, max_time

def get_comprehension_check_time(pid):
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute(""" WITH time_diff_table as (
                            SELECT url, time, time - lag(time) over (order by time) as time_diff
                            FROM site_logs
                            WHERE pid = %s
                        )
                        SELECT sum(time_diff)
                        FROM time_diff_table
                        WHERE url like '%%main-study-instructions%%' or url like '%%comprehension-check%%'
                    """, (pid,))
        result = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
        if len(result) == 0:
            return None
        return result[0][0]

def get_colorblindness_time(pid):
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute(""" WITH time_diff_table as (
                            SELECT url, time, time - lag(time) over (order by time) as time_diff
                            FROM site_logs
                            WHERE pid = %s
                        )
                        SELECT time_diff
                        FROM time_diff_table
                        WHERE url like '%%focal-study-instructions%%'
                    """, (pid,))
        result = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
        if len(result) == 0:
            return None
        return result[0][0]


def even_odd_consistency(pid):
    ratings = get_main_study_ratings(pid)
    ratings = [int(rating) for rating in ratings]

    even_items = ratings[::2]
    odd_items = ratings[1::2]

    even_score = np.sum(even_items)
    odd_score = np.sum(odd_items)

    correlation, _ = pearsonr(even_items, odd_items)
    return even_score, odd_score, correlation

def resampling_consistency(pid, seed=0, num_resamples=1000):
    ratings = get_main_study_ratings(pid)
    ratings = [int(rating) for rating in ratings]

    rng = np.random.default_rng(seed)
    ratings = np.array(ratings)

    correlations = []
    for _ in range(num_resamples):
        # Randomly split the ratings into two groups
        rng.shuffle(ratings)
        first_half = ratings[:len(ratings) // 2]
        second_half = ratings[len(ratings) // 2:]

        corr = np.corrcoef(first_half, second_half)[0, 1]
        correlations.append(corr)

    # Average the correlations
    median_correlation = np.median(correlations)
    return median_correlation

def get_sample_feedback(pids, anonymous=False):
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT pid, feedback FROM feedback""")
        result = cur.fetchall()
        for row in result:
            if row[0] in pids and len(row[1]) > 0:
                if anonymous:
                    print(row[1])
                else:
                    print(row[0] + ": " + row[1])
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
        return None

# Effectively provides you with all the info you need for IRV shenanigans
# E.g., You could use the provided sd range to determine what standard deviation value may be appropriate
def sd_stats(pids, visualize=False, only_values=False):
    real_sds = []
    modified_sds = []

    for pid in pids:
        x, y = get_sample_averages([pid], only_arrays=True)

        real_images_sd = np.std(x, ddof=1)
        modified_images_sd = np.std(y, ddof=1)

        real_sds.append(real_images_sd)
        modified_sds.append(modified_images_sd)
    
    real_sds = np.array(real_sds)
    modified_sds = np.array(modified_sds)

    real_min = np.min(real_sds)
    real_max = np.max(real_sds)
    modified_min = np.min(modified_sds)
    modified_max = np.max(modified_sds)

    # Range, where 95% of the data lies
    real_range = np.percentile(real_sds, [2.5, 97.5])
    modified_range = np.percentile(modified_sds, [2.5, 97.5])

    # Range, where 80% of the data lies
    real_range_80 = np.percentile(real_sds, [10, 90])
    modified_range_80 = np.percentile(modified_sds, [10, 90])

    # Range, where 85% of the data lies
    real_range_85 = np.percentile(real_sds, [7.5, 92.5])
    modified_range_85 = np.percentile(modified_sds, [7.5, 92.5])

    # Range, where 90% of the data lies
    real_range_90 = np.percentile(real_sds, [5, 95])
    modified_range_90 = np.percentile(modified_sds, [5, 95])

    # Range, where 99% of the data lies
    real_range_99 = np.percentile(real_sds, [0.5, 99.5])
    modified_range_99 = np.percentile(modified_sds, [0.0, 99.0]) # As minimum is 0

    if only_values:
        return real_min, real_max, modified_min, modified_max, real_range, modified_range, real_range_80, modified_range_80, real_range_85, modified_range_85

    print("Real Images SD Min:", real_min)
    print("Real Images SD Max:", real_max)
    print("Modified Images SD Min:", modified_min)
    print("Modified Images SD Max:", modified_max)

    print("Ranges that contain 95% of the data")
    print("Real Images SD Range:", real_range)
    print("Modified Images SD Range:", modified_range)

    #print("Ranges that contain 80% of the data")
    #print("Real Images SD Range:", real_range_80)
    #print("Modified Images SD Range:", modified_range_80)

    print("Ranges that contain 85% of the data")
    print("Real Images SD Range:", real_range_85)
    print("Modified Images SD Range:", modified_range_85)

    print("Ranges that contain 90% of the data")
    print("Real Images SD Range:", real_range_90)
    print("Modified Images SD Range:", modified_range_90)

    print("Ranges that contain 99% of the data")
    print("Real Images SD Range:", real_range_99)
    print("Modified Images SD Range:", modified_range_99)

    if visualize:
        # Draw a histogram of the standard deviations
        plt.hist(real_sds, bins=10)
        plt.title('Standard Deviation of Real Images')
        plt.xlabel('Standard Deviation')
        plt.ylabel('Frequency')
        plt.show()
        plt.hist(modified_sds, bins=10)
        plt.title('Standard Deviation of Modified Images')
        plt.xlabel('Standard Deviation')
        plt.ylabel('Frequency')
        plt.show()


def performance_versus_time(pids, save=False):
    performance_overall = []
    performance_real = []
    performance_modified = []
    times = []
    for pid in pids:
        # user_data = [pid, accuracy, real_accuracy, modified_accuracy, check_accuracy]
        time = get_total_time(pid)

        # Check if time is over 1 hour
        if time.total_seconds() > 3600:
            continue
        times.append(time.total_seconds())
        data = process_ratings(pid, post_hoc=False)
        performance_overall.append(data[1])
        performance_real.append(data[2])
        performance_modified.append(data[3])
        
    performance_overall = np.array(performance_overall)
    performance_real = np.array(performance_real)
    performance_modified = np.array(performance_modified)
    times = np.array(times)

    print("Number of participants (excluding wrongly tracked times):", len(performance_overall))

    # Define the time sections
    sections = [(0, 1000), (1001, 1750), (1751, float('inf'))]
    section_labels = ['0-1000', '1001-1750', '>1750']

    # Initialize lists to store means and standard deviations
    overall_means = []
    overall_stds = []
    real_means = []
    real_stds = []
    modified_means = []
    modified_stds = []
    counts = []

    for start, end in sections:
        mask = (times >= start) & (times <= end)
        counts.append(np.sum(mask))
        overall_means.append(np.mean(performance_overall[mask]))
        overall_stds.append(np.std(performance_overall[mask]))
        real_means.append(np.mean(performance_real[mask]))
        real_stds.append(np.std(performance_real[mask]))
        modified_means.append(np.mean(performance_modified[mask]))
        modified_stds.append(np.std(performance_modified[mask]))

    # Update section labels to include counts
    section_labels = [f'{label}\n(n={count})' for label, count in zip(section_labels, counts)]

    # Plot the performance versus time as bar charts with error bars
    x = np.arange(len(section_labels))  # the label locations
    width = 0.25  # the width of the bars

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    rects1 = ax.bar(x - width, overall_means, width, yerr=overall_stds, capsize=5, label='Overall Performance')
    rects2 = ax.bar(x, real_means, width, yerr=real_stds, capsize=5, label='Real Image Performance')
    rects3 = ax.bar(x + width, modified_means, width, yerr=modified_stds, capsize=5, label='Modified Image Performance')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel('Total Time (seconds)')
    ax.set_ylabel('Performance')
    ax.set_title('Performance by Time Sections')
    ax.set_xticks(x)
    ax.set_xticklabels(section_labels)
    ax.legend()

    fig.tight_layout()

    if save:
        plt.savefig("performance_vs_time.png", dpi=300, bbox_inches='tight')
    else:
        plt.show()

def process_sd_range(sd_range):
    
    # Remove the brackets
    sd_range = sd_range[1:-1]
    # Remove outer whitespace
    sd_range = sd_range.strip()
    # Ensure that there is only one whitespace between the two values
    sd_range = " ".join(sd_range.split())

    # Get the two values
    val1 = sd_range[1:-1].split(" ")[0]
    val1 = float(val1)
    val2 = sd_range[1:-1].split(" ")[1]
    val2 = float(val2)
    return val2 - val1

def analyze_sd_subsample_run(file):
    df = pd.read_csv(file)
    
    # Generate two df copies: one with only the first half of the columns and one with the second half
    df_extrems = df.iloc[:, :len(df.columns) // 2]
    df_ranges = df.iloc[:, len(df.columns) // 2:]

    # Get min and max of each column
    min_values = df_extrems.min()
    max_values = df_extrems.max()

    print("Min Values")
    print(min_values)
    print("")
    print("Max Values")
    print(max_values)
    print("")

    smallest_real_range = [100, None]
    smallest_modified_range = [100, None]
    smallest_real_range_80 = [100, None]
    smallest_modified_range_80 = [100, None]

    largest_real_range = [-1, None]
    largest_modified_range = [-1, None]
    largest_real_range_80 = [-1, None]
    largest_modified_range_80 = [-1, None]

    # Iterate over all rows in df_ranges
    for _, row in df_ranges.iterrows():
        
        real_range = process_sd_range(row["real_range"])
        modified_range = process_sd_range(row["modified_range"])
        real_range_80 = process_sd_range(row["real_range_80"])
        modified_range_80 = process_sd_range(row["modified_range_80"])

        if real_range < smallest_real_range[0]:
            smallest_real_range = [real_range, row["real_range"]]
        if modified_range < smallest_modified_range[0]:
            smallest_modified_range = [modified_range, row["modified_range"]]
        if real_range_80 < smallest_real_range_80[0]:
            smallest_real_range_80 = [real_range_80, row["real_range_80"]]
        if modified_range_80 < smallest_modified_range_80[0]:
            smallest_modified_range_80 = [modified_range_80, row["modified_range_80"]]

        if real_range > largest_real_range[0]:
            largest_real_range = [real_range, row["real_range"]]
        if modified_range > largest_modified_range[0]:
            largest_modified_range = [modified_range, row["modified_range"]]
        if real_range_80 > largest_real_range_80[0]:
            largest_real_range_80 = [real_range_80, row["real_range_80"]]
        if modified_range_80 > largest_modified_range_80[0]:
            largest_modified_range_80 = [modified_range_80, row["modified_range_80"]]
    
    print("Smallest Real Range:", smallest_real_range)
    print("Smallest Modified Range:", smallest_modified_range)
    print("Smallest Real Range 80:", smallest_real_range_80)
    print("Smallest Modified Range 80:", smallest_modified_range_80)

    print("Largest Real Range:", largest_real_range)
    print("Largest Modified Range:", largest_modified_range)
    print("Largest Real Range 80:", largest_real_range_80)
    print("Largest Modified Range 80:", largest_modified_range_80)
    
def filtered_users_stats(pids, max_hard_indicators=5, max_soft_indicators=5, array_only=False):
    user_data = []
    for pid in pids:
        ratings = get_main_study_ratings(pid)
        attention_checks = process_ratings(pid, post_hoc=False)[-1]
        average_image_time = get_average_image_time(pid)
        avg_in_seconds = average_image_time.total_seconds()

        _, max_seq_length, mean_seq_length, median_seq_length = long_string(ratings)
        real_ratings, modified_ratings = get_sample_averages([pid], only_arrays=True)
        real_sd = np.std(real_ratings, ddof=1)
        modified_sd = np.std(modified_ratings, ddof=1)
        
        user_data.append({
            "pid": pid,
            "ratings": ratings,
            "attention_checks": attention_checks,
            "time_per_image": avg_in_seconds,
            "max_seq_length": max_seq_length,
            "mean_seq_length": mean_seq_length,
            "median_seq_length": median_seq_length,
            "real_sd": real_sd,
            "modified_sd": modified_sd,
        })
    
    # Define a set of boolean conditions to filter the users
    instant_out = [
        lambda x: x["attention_checks"] <= 0.67,
        lambda x: x["time_per_image"] <= 2,
        lambda x: x["max_seq_length"] >= 10,
        lambda x: x["mean_seq_length"] >= 2.11,
        lambda x: x["median_seq_length"] >= 2,
        lambda x: not (0.5463 <= x["real_sd"] <= 1.914),
        lambda x: x["modified_sd"] > 1.7328
    ]
    
    hard_indicators = [
        lambda x: x["time_per_image"] < 2.456,
        lambda x: x["max_seq_length"] >= 8,
        lambda x: x["mean_seq_length"] > 1.8028,
        lambda x: not (0.5923 <= x["real_sd"] <= 1.7505),
        lambda x: x["modified_sd"] > 1.643
    ]

    soft_indicators = [
        lambda x: x["time_per_image"] < 2.756,
        lambda x: x["max_seq_length"] >= 7,
        lambda x: x["mean_seq_length"] > 1.7168,
        lambda x: not (0.6818 <= x["real_sd"] <= 1.68006),
        lambda x: not (0.106 <= x["modified_sd"] <= 1.5517)
    ]

    # Filter out all users who fail at least one instant out condition
    # Remove affected users from the user_data list
    user_data = [user for user in user_data if not any(condition(user) for condition in instant_out)]
    if not array_only:
        print("Number of users after instant out:", len(user_data))

    # Filter out all users who fail more than max_hard_indicators hard indicators
    # Remove affected users from the user_data list
    user_data = [user for user in user_data if sum(condition(user) for condition in hard_indicators) <= max_hard_indicators]
    if not array_only:
        print("Number of users after hard indicators:", len(user_data))

    # Filter out all users who fail more than max_soft_indicators soft indicators
    # Remove affected users from the user_data list
    user_data = [user for user in user_data if sum(condition(user) for condition in soft_indicators) <= max_soft_indicators]
    if not array_only:
        print("Number of users after soft indicators:", len(user_data))
        population_overview([user["pid"] for user in user_data])

    return [user["pid"] for user in user_data]

def threshold_subsampling_overview(pids, path=None):

    header = [
        "Max_Hard_Indicators", "Max_Soft_Indicators", "Number of Participants",
        "Real Images Mean", "Real Images SD", "Modified Images Mean", "Modified Images SD",
        "P(X > Y)", "U", "P-Value", "Z", "Effect Size (PCC)", "Effect Size (A.R.E)",
        "Required Sample Size (Noether)", "Required Sample Size (A.R.E.)",
        "Total Time Mean", "Total Time Median", "Total Time Min", "Total Time Max", "Total Time SD",
        "Average Image Time Mean", "Average Image Time Median", "Average Image Time Min", "Average Image Time Max", "Average Image Time SD",
        "Max Sequence Length", "Mean Sequence Length", "Median Sequence Length"
    ]

    if path is None:
        path = os.getcwd()

    now = int(round(time.time() * 1000))
    filename = f"{path}/{now}_threshold_subsampling_overview.csv"
    with open(filename, 'w') as file:
        file.write(",".join(header) + "\n")

    for max_hard_indicators in tqdm(range(6)):
        for max_soft_indicators in tqdm(range(6)):
            entries = filtered_users_stats(pids, max_hard_indicators=max_hard_indicators, max_soft_indicators=max_soft_indicators, array_only=True)
            if len(entries) == 0:
                with open(filename, 'a') as file:
                    file.write(f"{max_hard_indicators},{max_soft_indicators},0,,,,,,,,,,,,,,,,,,,,,,,\n")
    
            else:
                x, y = get_sample_averages(entries, only_arrays=True)

                real_images_mean = np.mean(x)
                real_images_sd = np.std(x, ddof=1)

                modified_images_mean = np.mean(y)
                modified_images_sd = np.std(y, ddof=1)

                U1, p = mannwhitneyu(x, y)
                p_x_greater_y = U1 / (len(x) * len(y))
                U2 = len(x) * len(y) - U1
                U = min(U1, U2)
                z = (U - len(x) * len(y) / 2) / np.sqrt(len(x) * len(y) * (len(x) + len(y) + 1) / 12)
                effect_size = abs(z) / np.sqrt(len(x) + len(y))
                effect_size_are = are_method(real_images_mean, modified_images_mean, real_images_sd, modified_images_sd)

                result, _ = noether(alpha=0.01, power=0.95, p=p_x_greater_y)

                sample_size_are = None
                _, max_seq_length, mean_seq_length, median_seq_length = accumulate_ls_stats(entries)

                total_time_mean, total_time_median, total_time_min, total_time_max, total_time_sd, average_image_time_mean, average_image_time_median, average_image_time_min, average_image_time_max, average_image_time_sd = get_time_stats(entries)

                with open(filename, 'a') as file:
                    file.write(f"{max_hard_indicators},{max_soft_indicators},{len(entries)},{real_images_mean},{real_images_sd},{modified_images_mean},{modified_images_sd},{p_x_greater_y},{U},{p},{z},{effect_size},{effect_size_are},{int(result[-1][0])},{sample_size_are},{total_time_mean},{total_time_median},{total_time_min},{total_time_max},{total_time_sd},{average_image_time_mean},{average_image_time_median},{average_image_time_min},{average_image_time_max},{average_image_time_sd},{max_seq_length},{mean_seq_length},{median_seq_length}\n")


def map_image_name_to_id(img_dir, is_real=True, model_name="Salman2020Do_R50", attack_name="diffattack"):
    """
    Maps image names to their corresponding database IDs by comparing byte representations.
    
    Args:
        img_dir (str): Directory containing the images
        is_real (bool): If True, look in real_images table, else in modified_images table
        model_name (str): Model name for modified images
        attack_name (str): Attack name for modified images
    
    Returns:
        str: Path to the output CSV file
    """
    try:
        connection = database_connection()
        cursor = connection.cursor()
        
        # Determine which table to query based on is_real flag
        if is_real:
            table_name = "real_images"
            cursor.execute("""SELECT id, image FROM real_images WHERE model_name = %s""", (model_name,))
        else:
            table_name = "modified_images"
            cursor.execute("""SELECT id, image FROM modified_images 
                             WHERE model_name = %s AND attack_name = %s""", 
                          (model_name, attack_name))
        
        db_images = cursor.fetchall()
        
        # Create output CSV file
        output_filename = f"image_name_to_id_mapping_{table_name}_{attack_name if not is_real else 'real'}.csv"
        with open(output_filename, 'w') as file:
            file.write("image_name,image_id\n")
            
            # Get all image files from the directory
            image_files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            for img_file in tqdm(image_files, desc="Processing images"):
                img_path = os.path.join(img_dir, img_file)
                
                # Read the image file as bytes
                with open(img_path, 'rb') as f:
                    img_bytes = f.read()
                
                # Find matching image in database
                matched_id = None
                for db_id, db_image_data in db_images:
                    if db_image_data == img_bytes:
                        matched_id = db_id
                        break
                
                if matched_id:
                    # Write to CSV: parent_dir/image_name, image_id
                    parent_dir = os.path.basename(img_dir)
                    image_name = f"{parent_dir}/{img_file}"
                    file.write(f"{image_name},{matched_id}\n")
                else:
                    print(f"Warning: No match found for {img_file}")
        
        print(f"Mapping completed. Results saved to {output_filename}")
        return output_filename
        
    except (Exception, psycopg2.Error) as error:
        print("Error while processing images:", error)
        return None
        
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

if __name__ == "__main__":
    
    pids_dir = "/home/dren.fazlija/data/Scooter/pids/"
    attacks = ["semanticadv/", "cadv/", "ncf/", "diffattack/", "advpp/", "aca/"]
    #attacks = ["aca/"]
    pids = []
    
    for attack in attacks:
        pids_file = pids_dir + attack + "pids.txt"
        with open(pids_file, "r") as file:
            attack_pids = file.readlines()
            pids.extend([pid.strip() for pid in attack_pids])

    print(len(pids))
    get_time_stats(pids, verbose=True, percentiles=True)

    #population_overview(pids)
    #get_ratings_per_image(pids, format="csv", filename="ratings_ijcv.csv")
    #map_image_name_to_id("/home/dren.fazlija/data/Scooter/attacks/real_images", is_real=True, model_name="Salman2020Do_R50", attack_name="diffattack")

    # # CC and CB time stats
    # attack = attacks[0]
    # df = pd.read_csv(pids_dir + attack + "prolific_export.csv")
    # status_counts = df['Status'].value_counts()
    # print(status_counts)

    # rejections = get_returned_tasks(pids_dir + attack + "prolific_export.csv", pids_array=pids, verbose=True)

    # # Add additional passed pids, if you somehow missed them
    # #pids.extend(rejections["Actually passed!"])
    
    # print("")

    # # Comprehension Check Time Stats
    # print("Number of tracked participants: "  + str(len(pids)))
    # cc_times = get_time_stats_for_phase(pids, phase='comprehension_check')
    # print("Comprehension Check Times")
    # print("Average Time:", cc_times[1])
    # print("Median Time:", cc_times[2])
    # print("Min Time:", cc_times[3])
    # print("Max Time:", cc_times[4])

    # print("")2024
    # print("")

    # # Colorblindness Test Time Stats
    # pids.extend(rejections["Failed comprehension check"])
    # print("Number of tracked participants: "  + str(len(pids)))
    # cb_times = get_time_stats_for_phase(pids, phase='colorblindness_test')
    # print("Colorblindness Test Times")
    # print("Average Time:", cb_times[1])
    # print("Median Time:", cb_times[2])
    # print("Min Time:", cb_times[3])
    # print("Max Time:", cb_times[4])
    
    # Get the pids that failed the comprehension check
    #rejections = get_returned_tasks(pids_dir + attack + "prolific_export.csv", pids_array=pids, verbose=True)

    # # Add additional passed pids, if you somehow missed them
    # pids.extend(rejections["Actually passed!"])

    # performances, wrong_choices, won_comparisons = get_comprehension_check_performance(pids)

    # print(len(pids))
    # print(performances["4/6"])
    # print(performances["3/6"])
    # print(performances["2/6"])
    # print(performances["1/6"])

    # non_4_6_pids = [pid for pid in pids if pid not in performances["4/6"]]
    # print(len(non_4_6_pids))

    #print(len(pids))
    #performance_versus_time(pids, save=True)
    #population_overview(non_4_6_pids)
    # with open(pids_file, "r") as file:
    #     pids = file.readlines()
    #     pids = [pid.strip() for pid in pids]

    #attack = "diffattack/"
    #df = pd.read_csv(pids_dir + attack + "prolific_export_673cdf3baaaed8a6046adb60.csv")
    
    # Only keep entries with a status of "RETURNED" or "AWAITING REVIEW"
    # df = df[(df["Status"] == "APPROVED")]

    # # Get all the remaining participant ids and store them in an array
    #pids = df["Participant id"].values
    #print("Original number of participants:", len(pids))
    # population_overview(pids)

    # pids_file = pids_dir + attack + "pids.txt"
    # with open(pids_file, "r") as file:
    #     pids = file.readlines()
    #     pids = [pid.strip() for pid in pids]

    # # Comprehension Check Time Stats
    # print("Number of tracked participants: "  + str(len(pids)))
    # cc_times = get_time_stats_for_phase(pids, phase='comprehension_check')
    # print("Comprehension Check Times")
    # print("Average Time:", cc_times[1])
    # print("Median Time:", cc_times[2])
    # print("Min Time:", cc_times[3])
    # print("Max Time:", cc_times[4])

    # performances, wrong_choices, won_comparisons = get_comprehension_check_performance(pids)

    # print(performances["4/6"])
    # print(performances["3/6"])
    # print(performances["2/6"])
    # print(performances["1/6"])

    #non_4_6_pids = [pid for pid in pids if pid not in performances["4/6"]]

    

    """
    semantic_adv_pids_file = "/home/dren.fazlija/data/Scooter/pids/larger_test_study/pids.txt"
    with open(semantic_adv_pids_file, "r") as file:
        semantic_adv_pids = file.readlines()
        semantic_adv_pids = [pid.strip() for pid in semantic_adv_pids]

    # Get the pids that failed the comprehension check
    rejections = get_returned_tasks(pids_dir + attack + "prolific_export.csv", pids_array=semantic_adv_pids, verbose=True)

    # Add additional passed pids, if you somehow missed them
    semantic_adv_pids.extend(rejections["Actually passed!"])

    passed_pids = semantic_adv_pids.copy()

    # Extend with the pids that failed the comprehension check
    semantic_adv_pids.extend(rejections["Failed comprehension check"])

    print("")
    print("Number of tracked participants: "  + str(len(semantic_adv_pids)))
          
    performances, wrong_choices, won_comparisons = get_comprehension_check_performance(semantic_adv_pids)

    filtered_out = []
    for key in wrong_choices.keys():
        if wrong_choices[key] > 2:
            filtered_out.append(key)
    for key in won_comparisons.keys():
        if won_comparisons[key] > 1:
            filtered_out.append(key)

    print("Filtered out:", len(filtered_out))
    print("Passed:", len(passed_pids))

    to_be_removed = []

    for pid in passed_pids:
        cc_images = get_comprehension_check_answers(pid)[0][1]
        for i in range(len(cc_images)):
            if cc_images[i] in filtered_out:
                to_be_removed.append(pid)
                break

    print("Passed after filtering:", len(passed_pids) - len(to_be_removed))
    #population_overview(passed_pids)"""

    """
    df = pd.read_csv(pids_dir + attack + "prolific_export.csv")
    status_counts = df['Status'].value_counts()
    print(status_counts)

    rejections = get_returned_tasks(pids_dir + attack + "prolific_export.csv", pids_array=pids, verbose=True)

    # Add additional passed pids, if you somehow missed them
    pids.extend(rejections["Actually passed!"])
    
    print("")

    # Comprehension Check Time Stats
    print("Number of tracked participants: "  + str(len(pids)))
    cc_times = get_time_stats_for_phase(pids, phase='comprehension_check')
    print("Comprehension Check Times")
    print("Average Time:", cc_times[1])
    print("Median Time:", cc_times[2])
    print("Min Time:", cc_times[3])
    print("Max Time:", cc_times[4])

    print("")
    print("")

    # Colorblindness Test Time Stats
    pids.extend(rejections["Failed comprehension check"])
    print("Number of tracked participants: "  + str(len(pids)))
    cb_times = get_time_stats_for_phase(pids, phase='colorblindness_test')
    print("Colorblindness Test Times")
    print("Average Time:", cb_times[1])
    print("Median Time:", cb_times[2])
    print("Min Time:", cb_times[3])
    print("Max Time:", cb_times[4])"""

    """

    dir = "/home/dren.fazlija/data/Scooter/pids/cadv/"
    export_dir = "/home/dren.fazlija/data/Scooter/exported_data/larger_test_study/"

    """
    # pids_file = dir + "ncf_approved.txt"
    # with open(pids_file, "r") as file:
    #     pids = file.readlines()
    #     pids = [pid.strip() for pid in pids]
    """

    df = pd.read_csv(dir + "prolific_export.csv")
    
    # Only keep entries with a status of "RETURNED" or "AWAITING REVIEW"
    df = df[(df["Status"] == "APPROVED")]

    # Get all the remaining participant ids and store them in an array
    pids = df["Participant id"].values
    #print("Original number of participants:", len(pids))
    #population_overview(pids)

    #study_overview(pids, sample_size=60, number_of_sets=10000, seed=0, path=dir, verbose=False, checkpoint=760, early_stop=1000, previous_file="1722858305169_overview.csv")

    #get_sample_feedback(pids, anonymous=True)
    #get_time_stats(pids, verbose=True)
    #accumulate_ls_stats(pids, visualize=True)
    #performance_versus_time(pids, save=True)

    performances, wrong_choices, won_comparisons = get_comprehension_check_performance(pids)

    print(performances["4/6"])
    print(performances["3/6"])
    print(performances["2/6"])
    print(performances["1/6"])

    non_4_6_pids = [pid for pid in pids if pid not in performances["4/6"]]
    print("Number of participants that got 5/6 or more:", len(non_4_6_pids))"""

    """
    # Get SemanticAdv and NCF pids
    semantic_adv_pids = []
    ncf_pids = []

    semantic_adv_pids_file = "/home/dren.fazlija/data/Scooter/pids/larger_test_study/pids.txt"
    with open(semantic_adv_pids_file, "r") as file:
        semantic_adv_pids = file.readlines()
        semantic_adv_pids = [pid.strip() for pid in semantic_adv_pids]

    ncf_pids_file = "/home/dren.fazlija/data/Scooter/pids/ncf/ncf_approved.txt"
    with open(ncf_pids_file, "r") as file:
        ncf_pids = file.readlines()
        ncf_pids = [pid.strip() for pid in ncf_pids]
    
    print("SemanticAdv Pids:", len(semantic_adv_pids))
    print("NCF Pids:", len(ncf_pids))
    print("cAdv Pids:", len(non_4_6_pids))

    combined_pids = list(set(semantic_adv_pids + ncf_pids + non_4_6_pids))
    print("Combined Pids:", len(combined_pids))"""


    #population_overview(combined_pids)
    #get_time_stats(combined_pids, percentiles=True)
    #performance_versus_time(combined_pids, save=True)
    #accumulate_ls_stats(combined_pids, visualize=True, previous_means={"SemanticAdv": 1.437, "NCF": 1.482, "cAdv": 1.472})
    #sd_stats(combined_pids)
    #ls_percentiles(combined_pids)
    #filtered_users_stats(combined_pids)
    #threshold_subsampling_overview(combined_pids, path="/home/dren.fazlija/data/Scooter/")
    """print("cAdv stats")
    print(accumulate_ls_stats(non_4_6_pids))
    print("")

    print("SemanticAdv stats")
    print(accumulate_ls_stats(semantic_adv_pids))
    print("")

    print("NCF stats")
    print(accumulate_ls_stats(ncf_pids))"""
    
    
    """
    rejections = get_returned_tasks(dir + "prolific_export_66dea778dc3d3c08e9f27063.csv")
    print(len(rejections["Failed comprehension check"]))

    pids.extend(rejections["Failed comprehension check"])
    print(len(pids))

    cb_times = get_time_stats_for_phase(pids, phase='colorblindness_test')
    cc_times = get_time_stats_for_phase(pids, phase='comprehension_check')

    print("Colorblindness Test Times")
    print("Average Time:", cb_times[1])
    print("Median Time:", cb_times[2])
    print("Min Time:", cb_times[3])
    print("Max Time:", cb_times[4])

    print("Comprehension Check Times")
    print("Average Time:", cc_times[1])
    print("Median Time:", cc_times[2])
    print("Min Time:", cc_times[3])
    print("Max Time:", cc_times[4])"""

    #get_time_stats(pids, verbose=True)

    """

    performances, wrong_choices, won_comparisons = get_comprehension_check_performance(pids)

    print(performances["4/6"])
    print(performances["3/6"])
    print(performances["2/6"])
    print(performances["1/6"])"""

    """
    print(wrong_choices)
    to_be_deleted_wrong_choices = ""
    wrong_choices_keys = list(wrong_choices.keys())
    for key in wrong_choices_keys:
        if wrong_choices[key] > 2:
            to_be_deleted_wrong_choices += str(key) + ", "

    print(to_be_deleted_wrong_choices[:-2])
    
    print(won_comparisons)
    to_be_deleted_won_comparisons = ""
    won_comparisons_keys = list(won_comparisons.keys())
    for key in won_comparisons_keys:
        if won_comparisons[key] > 1:
            to_be_deleted_won_comparisons += str(key) + ", "
    print(to_be_deleted_won_comparisons[:-2])"""
    
    #get_comprehension_check_image(49)
    #get_comprehension_check_image(107)
    #get_comprehension_check_image(37)

    """subsamples = subsampling(pids, 60, 1000, 0)
    header = [
        "real_min", "real_max", "modified_min", "modified_max", "real_range", "modified_range", "real_range_80", "modified_range_80"
    ]

    now = int(round(time.time() * 1000))
    filename = f"{export_dir}/{now}_overview.csv"

    with open(filename, 'w') as file:
        file.write(",".join(header) + "\n")

        for subsample in tqdm(subsamples):
            entries = list(subsample)
            real_min, real_max, modified_min, modified_max, real_range, modified_range, real_range_80, modified_range_80 = sd_stats(entries, only_values=True)
            file.write(f"{real_min},{real_max},{modified_min},{modified_max},{real_range},{modified_range},{real_range_80},{modified_range_80}\n")"""

    #sd_stats(pids, visualize=False)
    #analyze_sd_subsample_run(export_dir + "1723562184225_overview.csv")




