from db_utils import database_connection
import psycopg2
import numpy as np
import datetime
from data_processing import process_ratings, get_ratings, get_main_study_ratings, get_sample_averages
from utils import long_string, draw_chart

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'
   ITALIC = '\033[3m'

# The total time that the participant has to complete the study
total_time = 18
# Total payment for the study (in pounds)
total_payment = 2.70
# Time required for the colorblindness test
colorblindness_time = 0.5
# Time required for the comprehension test
comprehension_time = 6.0
# Time required for the main study
main_study_time = 11.5 


def current_state(pid):
    """
    Retrieves and prints the current state of a participant based on their participant ID (pid).
    This function connects to a database, fetches the participant's progress in various tests,
    and the last page they visited. It then formats and prints this information in a readable table format.
    If the last visited page is "Main Study", it calls the `current_image` function.
    Args:
        pid (str): The participant ID. It should be a 24 character long string.
    Raises:
        psycopg2.DatabaseError: If there is an error connecting to or querying the database.
    Returns:
        None
    """

    try:
        conn = database_connection()
        print("")
        cur = conn.cursor()
        
        
        cur.execute("""SELECT attempted_colorblindness, passed_colorblindness, 
                    attempted_comprehension, passed_comprehension, completed_study
                    FROM participants WHERE pid = %s""", (pid,))
        result = cur.fetchone()

        cur.execute("""SELECT url, time FROM site_logs WHERE pid = %s ORDER BY time DESC""", (pid,))
        last_page = cur.fetchone()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

        overview_output = []
        for i in range(len(result)):
            if result[i] == False:
                overview_output.append("No")
            elif result[i] == True:
                overview_output.append("Yes")
            else:
                overview_output.append("")

        table = "State of participant: \n"
        table += "| Attempted Colorblindness | Passed Colorblindness | Attempted Comprehension | Passed Comprehension | Completed Study |\n"
        table +="|--------------------------|-----------------------|-------------------------|----------------------|-----------------|\n"
        table += f"| {overview_output[0]:^24} | {overview_output[1]:^21} | {overview_output[2]:^23} | {overview_output[3]:^20} | {overview_output[4]:^15} |\n"

        print("")

        if last_page is not None:

            page_name = last_page[0].split("/")[-1]
            page_name = page_name.split("?")[0]
            page_name = page_name.split("-")
            page_name = [s.capitalize() for s in page_name]    
            page_name = " ".join(page_name)

            time = last_page[1].strftime("%d/%m/%Y %H:%M:%S") + " UTC"

            table += f"Last visited page: {page_name}\n"
            table += f"Time last visited: {time}\n"
        
        else:
            table += "No pages visited!"

        print(table)
        if page_name == "Main Study":
            print("Checking the current image...")
            current_image(pid)
        print("")
        return

def current_image(pid):
    """
    Retrieve the most recent image log entry for a given process ID (pid) from the database.
    This image is the most recent image that the participant viewed during the main study.

    Args:
        pid (str): The process ID for which to retrieve the most recent image log entry. It should be a 24 character long string.

    Returns:
        None: Prints the last viewed image information if available, otherwise prints "No images viewed!".

    Raises:
        psycopg2.DatabaseError: If there is an error connecting to or querying the database.
    """
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT * from image_logs WHERE pid = %s ORDER BY time DESC LIMIT 1""", (pid,))
        result = cur.fetchone()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
        if result is None:
            print("No images viewed!")
            return
        else:
            time = result[2].strftime("%d/%m/%Y %H:%M:%S") + " UTC"
            print("Last viewed image: Image", result[1], "at", time)
            return

def feedback(pid):
    """
    Retrieve and display feedback for a given participant ID (pid) from the database.
    The function connects to the database, fetches feedback data for the specified pid,
    and prints the feedback details. The feedback includes a descriptive comment and 
    responses to a series of Likert scale statements.
    Args:
        pid (str): The participant ID for which feedback is to be retrieved. It should be a 24 character long string.
    Raises:
        psycopg2.DatabaseError: If there is an error connecting to or querying the database.
    Notes:
        - The function prints feedback details to the console.
        - If no feedback is found for the given pid, a message indicating no feedback is printed.
        - Likert scale responses are color-coded based on their values.
    """

    likert = {
        1: "Strongly Disagree",
        2: "Disagree",
        3: "Neutral",
        4: "Agree",
        5: "Strongly Agree"
    }

    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT * from feedback WHERE pid = %s""", (pid,))
        result = cur.fetchone()
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    
    finally:
        cur.close()
        conn.close()
    
        if result is None:
            print("No feedback given!")
            return
    
        else:
            print("")
            if result[1] == "None":
                print("No descriptive feed!")
            else:
                print("Feedback given:", color.ITALIC, color.BOLD, result[1], color.END)

            answers = result[2]
            print("Likert scale rating:\n")

            statements = [
                "1.) My responses to items on this survey are accurate.",
                "2.) I exerted sufficient effort on this survey.",
                "3.) I answered items on this survey without reading them.",
                "4.) I randomly responded to some survey items.",
                "5.) I rushed through this survey.",
                "6.) I thought carefully about each of my responses on this survey.",
                "7.) The researchers should include my data in the results.",   
            ]

            for i in range(len(statements)):
                print("")
                statement = statements[i]
                if answers[i] == None:
                    print(statement, color.BOLD, color.BLUE, "No response", color.END)
                else: 
                    answer = int(answers[i])
                    if (int(answer) < 3 and i not in [2, 3, 4]) or (int(answer) > 3 and i in [2, 3, 4]):
                        print(statement, color.BOLD, color.RED, likert[answer], color.END)
                    else:
                        print(statement, color.BOLD, color.GREEN, likert[answer], color.END)

            print("")

def get_booleans(pid):
    """
    Retrieve boolean values related to a participant's study progress from the database.

    Args:
        pid (str): The participant ID. It should be a 24 character long string.

    Returns:
        tuple: A tuple containing the following boolean values:
            - attempted_colorblindness (bool): Whether the participant attempted the colorblindness test.
            - passed_colorblindness (bool): Whether the participant passed the colorblindness test.
            - attempted_comprehension (bool): Whether the participant attempted the comprehension test.
            - passed_comprehension (bool): Whether the participant passed the comprehension test.
            - completed_study (bool): Whether the participant completed the study.

    Raises:
        psycopg2.DatabaseError: If there is an error with the database connection or query execution.
    """
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

def get_total_time(pid):
    """
    Calculate the total time for a given participant ID (pid) from the site_logs table.

    This function connects to the database, retrieves the maximum and minimum time
    entries for the specified pid from the site_logs table, and calculates the difference
    between them to determine the total time.

    Args:
        pid (str): The ID of the participant for whom to calculate their total invested time. It should be a 24 character long string.

    Returns:
        datetime.timedelta: The total time duration for the given pid.

    Raises:
        psycopg2.DatabaseError: If there is an error with the database connection or query execution.
    """
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
    """
    Calculate the average time between images for a given participant ID (pid).

    This function connects to a database, retrieves the maximum and minimum
    timestamps from the image_logs table for the specified pid, and calculates
    the average time between images by dividing the difference by 106 (the amount of main study images).

    Args:
        pid (str): The participant ID for which to calculate the average image time. It should be a 24 character long string.

    Returns:
        float: The average image annotation time of participant pid.

    Raises:
        psycopg2.DatabaseError: If there is an error with the database connection or query execution.
    """
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

def how_much_to_pay(pid):
    """
    Determines the payment amount for a participant based on their progress and performance in a study.
    Args:
        pid (str): The participant's ID. It should be a 24 character long string.
    Returns:
        None: Prints the payment amount and relevant messages based on the participant's status and performance.
    The function follows these steps:
    1. Checks if the participant has consented to the study.
    2. Checks if the participant has attempted and passed the colorblindness test.
    3. Checks if the participant has attempted and passed the comprehension test.
    4. Checks if the participant has completed the study.
    5. Checks the participant's performance on attention checks.
    6. Evaluates the participant's average time spent on images.
    7. Evaluates the participant's long string statistics.
    8. Evaluates the participant's IRV (standard deviation of real and modified ratings).
    Depending on the results of these checks, the function prints the appropriate payment amount and messages.
    """
    booleans = get_booleans(pid)

    print("")

    if booleans is None:
        print(color.BOLD + color.RED + "NOTHING, participant has NOT consented to the study (yet)!" + color.END)
        return

    if booleans[0] == False:
        print("Participant has not attempted the colorblindness test!")
        print(color.UNDERLINE + color.BOLD + "Payment: Nothing (yet)" + color.END + "\n")
        return
    
    if booleans[1] == False:
        print(color.BOLD + color.RED + "Participant has not passed the colorblindness test!" + color.END)
        output = str(total_payment * (colorblindness_time / total_time)) + u"\xA3"
        print(color.UNDERLINE + color.BOLD + "Payment: " + output + color.END + "\n")
        return

    print(color.BOLD + color.GREEN + "Participant has passed the colorblindness test!" + color.END)

    if booleans[2] == False:
        print("Participant has not attempted the comprehension test!")
        output = output = str(total_payment * (colorblindness_time / total_time)) + u"\xA3"
        print(color.UNDERLINE + color.BOLD + "Payment: At least " + output + color.END + "\n")
        return

    if booleans[3] == False:
        print(color.BOLD + color.RED + "Participant has not passed the comprehension test!" + color.END)
        output = str(total_payment * (comprehension_time / total_time)) + u"\xA3"
        print(color.UNDERLINE + color.BOLD + "Payment: " + output + color.END + "\n")
        return
    
    print(color.BOLD + color.GREEN + "Participant has passed the comprehension test!" + color.END)

    if booleans[4] == False:
        print(color.BOLD + color.RED + "Participant has not completed the study!" + color.END)
        output = str(total_payment * (comprehension_time / total_time)) + u"\xA3"
        print(color.UNDERLINE + color.BOLD + "Payment: At least " + output + color.END + "\n")
        return

    if booleans[4] == True:
        print(color.BOLD + color.GREEN + "Participant has completed the study!" + color.END)
        
        output = str(total_payment * (main_study_time / total_time)) + u"\xA3"
            

        # Check if the participant has passed all attention checks
        user_data = process_ratings(pid, post_hoc=False)
        
        if user_data[-1] <= 0.67:
            print(color.BOLD + color.RED + "Participant has failed more than one attention check! (Accuracy: )" + str(user_data[-1]) + ")" + color.END)
            print(color.UNDERLINE + color.BOLD + "Payment: " + output + color.END + "\n")
            return
        
        elif user_data[-1] <= 0.83:
            print(color.BOLD + color.YELLOW + "Participant has failed one attention check!" + color.END)

        else:
            print(color.BOLD + color.GREEN + "Participant has passed all attention checks!" + color.END)

        
        verdict = color.UNDERLINE + color.BOLD + "Payment: Undecided. Please check the participants answers! Payment could be deducted to " + output + color.END + "\n"
        verdict += color.BOLD + "Deduct payment iff either 2/3 categories (time, long string, IRV) serve a purple warning, or if 1 provides a purple warning and 2 provide a yellow warning." + color.END + "\n"
        sus_time = True
        sus_long_string = False
        sus_irv = False

        print("")
        print("Checking time taken per image...")
        
        # Check if average time spent on images is less than 2 seconds
        average_image_time = get_average_image_time(pid)
        avg_in_seconds = average_image_time.total_seconds()

        if avg_in_seconds < 2:
            print(color.BOLD + color.RED + "Average time spent on images is less than 2 seconds! (" + str(avg_in_seconds) + ")" + color.END)
            output = str(total_payment * (main_study_time / total_time)) + u"\xA3"
            print(color.UNDERLINE + color.BOLD + "Payment: " + output + color.END + "\n")
            return

        elif avg_in_seconds < 3.25:
            print(color.BOLD + color.PURPLE + "Average time spent on images is less than 3.25 seconds! (" + str(avg_in_seconds) + ")" + color.END)
            output = str(total_payment * (main_study_time / total_time)) + u"\xA3"
            verdict = color.UNDERLINE + color.BOLD + "Payment: Undecided. Please check the participants answers! Payment could be deducted to " + output + color.END + "\n"
        
        elif avg_in_seconds < 4.5:
            print(color.BOLD + color.YELLOW + "Average time spent on images is less than 4.5 seconds! (" + str(avg_in_seconds) + ")" + color.END)
            output = str(total_payment * (main_study_time / total_time)) + u"\xA3"
        
        else:
            print(color.BOLD + color.GREEN + "Average time spent on images is at least 4.5 seconds!" + color.END)
            sus_time = False

        print("")
        print("Checking the long string stats...")

        # Check if the long string stats are out of the ordinary
        sequences, max_length, mean_length, median_length = get_long_string_stats(pid, intermediate=True)

        # Let's start off with the strong triggers marked in purple
        if max_length > 8:
            print(color.BOLD + color.PURPLE + "Participant has a long string of length greater than 8! (" + str(max_length) + ")" + color.END)
            sus_long_string = True

        if mean_length > 2.7:
            print(color.BOLD + color.PURPLE + "Participant's average string length is greater than 2.7! (" + str(mean_length) + ")" + color.END)
            sus_long_string = True
        
        if median_length != 2:
            print(color.BOLD + color.PURPLE + "Participant has a median length that is not equal to 2! (" + str(median_length) + ")" + color.END)
            sus_long_string = True

        # Now let's move on to the weaker triggers marked in yellow    
        if max_length == 8:
            print(color.BOLD + color.YELLOW + "Participant has a long string of length greater than 7! (" + str(max_length) + ")" + color.END)
            # print(color.BOLD + "Here are the other stats: mean length: " + str(mean_length) + ", median length: " + str(median_length) + color.END)
            sus_long_string = True
        
        if mean_length > 2.6 and mean_length <= 2.7:
            print(color.BOLD + color.YELLOW + "Participant's average string length is greater than 2.6! (" + str(mean_length) + ")" + color.END)
            sus_long_string = True

        if sus_long_string:
            print(color.BOLD + "Overview of sequences:", sequences, color.END)
        
        else:
            print(color.BOLD + color.GREEN + "Participant's long string stats are within the norm!" + color.END)
            
        print("")
        print("Checking the IRV stats... (i.e., are the standard deviation of real and modified ratings out of the ordinary?)")

        x, y = get_sample_averages([pid], only_arrays=True)

        real_images_sd = np.std(x, ddof=1)
        modified_images_sd = np.std(y, ddofpyth=1)

        # Strong triggers for high and low standard deviations (purple)
        if real_images_sd > 1.87:
            print(color.BOLD + color.PURPLE + "Participant has a high standard deviation for real images! (" + str(real_images_sd) + ")" + color.END)
            sus_irv = True
        if modified_images_sd > 1.69:
            print(color.BOLD + color.PURPLE + "Participant has a high standard deviation for modified images! (" + str(modified_images_sd) + ")" + color.END)
            sus_irv = True
        
        if real_images_sd < 0.6:
            print(color.BOLD + color.PURPLE + "Participant has a low standard deviation for real images! (" + str(real_images_sd) + ")" + color.END)
            sus_irv = True

        if modified_images_sd < 0.64:
            print(color.BOLD + color.PURPLE + "Participant has a low standard deviation for modified images! (" + str(modified_images_sd) + ")" + color.END)
            sus_irv = True

        # Weaker triggers for high and low standard deviations (yellow)
        if real_images_sd > 1.7 and real_images_sd <= 1.87:
            print(color.BOLD + color.YELLOW + "Participant has a high standard deviation for real images! (" + str(real_images_sd) + ")" + color.END)
            sus_irv = True

        if modified_images_sd > 1.62 and modified_images_sd <= 1.69:
            print(color.BOLD + color.YELLOW + "Participant has a high standard deviation for modified images! (" + str(modified_images_sd) + ")" + color.END)
            sus_irv = True
        
        if real_images_sd < 0.7 and real_images_sd >= 0.6:
            print(color.BOLD + color.YELLOW + "Participant has a low standard deviation for real images! (" + str(real_images_sd) + ")" + color.END)
            sus_irv = True

        if modified_images_sd < 0.79 and modified_images_sd >= 0.64:
            print(color.BOLD + color.YELLOW + "Participant has a low standard deviation for modified images! (" + str(modified_images_sd) + ")" + color.END)
            sus_irv = True

        if not sus_irv:
            print(color.BOLD + color.GREEN + "Participant's IRV stats are within the norm!" + color.END)

        if sus_irv or sus_long_string or sus_time:
            print("")
            print(verdict)
            return


        print("")

        # Participant has passed all vital test, full payment guaranteed
        output = str(total_payment) + u"\xA3"
        print(color.UNDERLINE + color.BOLD + "Payment: " + output + color.END + "\n")

        return

def get_long_string_stats(pid, intermediate=False):
    """
    Calculate and optionally print statistics for long sequences of ratings.

    Args:
        pid (str): The participant ID for which to retrieve and analyze ratings. It should be a 24 character long string.
        intermediate (bool, optional): If False, prints the statistics and draws a chart. Defaults to False.

    Returns:
        tuple: A tuple containing:
            - sequences (list): A list of sequences of ratings.
            - max_length (int): The maximum length of the sequences.
            - mean_length (float): The mean length of the sequences.
            - median_length (float): The median length of the sequences.
    """
    main_study_ratings = get_main_study_ratings(pid)
    main_study_ratings = [int(rating) for rating in main_study_ratings]

    sequences, max_length, mean_length, median_length = long_string(main_study_ratings)
    if not intermediate:
        print("")
        print("Long string stats:")
        print("Overview of sequences:", sequences)
        print("Maximum sequence length:", max_length)
        print("Mean sequence length:", mean_length)
        print("Median sequence length:", median_length)
        draw_chart(sequences, mean_length, median_length)
        print("")
    return sequences, max_length, mean_length, median_length

def reset_booleans(pid):
    """
    Resets the boolean values for a participant in the database to their initial state.
    This function retrieves the current boolean values for a participant identified by `pid`,
    prints the current state, and then resets the boolean values to their initial state.
    It also updates the `colorblind_answers` field to NULL.
    Args:
        pid (str): The participant ID. It should be a 24 character long string.
    Returns:
        None
    Raises:
        Exception: If there is an error with the database connection or execution of the SQL statements.
    Notes:
        - The function prints the current state of the boolean values before resetting them.
        - The function prints a message indicating that the booleans have been reset.
    """
    booleans = get_booleans(pid)
    if booleans is None:
        print("Participant does not exist!")
        return
    print("Resetting booleans for participant", pid)
    print("Current state:")
    print("Attempted colorblindness:", booleans[0])
    print("Passed colorblindness:", booleans[1])
    print("Attempted comprehension:", booleans[2])
    print("Passed comprehension:", booleans[3])
    print("Completed study:", booleans[4])
    print("Copy the following line to restore this configuration:", color.BOLD, booleans, color.END)

    try:
        conn = database_connection()
        cur = conn.cursor()
        # Change the booleans to their initial state + some former values
        cur.execute("""UPDATE participants SET attempted_colorblindness = %s, passed_colorblindness = %s, 
                    attempted_comprehension = %s, passed_comprehension = %s, completed_study = %s WHERE pid = %s""",
                    (False, None, False, None, False, pid))
        cur.execute("""UPDATE participants SET colorblind_answers = NULL WHERE pid = %s""", (pid,))
        conn.commit()
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    
    finally:
        cur.close()
        conn.close()
        print("Booleans have been reset!")

def restore_booleans(pid):
    """
    Restore boolean values for a participant in the database.
    This function prompts the user to input a string representing five boolean values 
    (True, False, or None) and updates the corresponding fields in the database for 
    the participant with the given pid.
    Args:
        pid (str): The participant ID whose boolean values are to be restored. It should be a 24 character long string.
    Raises:
        Exception: If there is an error with the database connection or execution.
    Notes:
        The input string should be in the format: (True, True, True, True, True).
        The function will validate the input and ensure it contains exactly five 
        boolean values. If the input is invalid, an error message will be printed 
        and the function will return without making any changes to the database.
    """
    input_string = input("Please enter the string to restore the booleans (e.g., (True, True, True, True, True)): ")
    
    input_string = input_string.strip()
    booleans = input_string[1:-1].split(", ")
    if len(booleans) != 5:
        print("Invalid input!")
        return
    for b in booleans:
        if b not in ["True", "False", "None"]:
            print("Invalid input!")
            return
    booleans = [True if b == "True" else False if b == "False" else None for b in booleans]

    try:
        conn = database_connection()
        cur = conn.cursor()
        # Change the booleans to their initial state
        cur.execute("""UPDATE participants SET attempted_colorblindness = %s, passed_colorblindness = %s, 
                    attempted_comprehension = %s, passed_comprehension = %s, completed_study = %s WHERE pid = %s""",
                    (booleans[0], booleans[1], booleans[2], booleans[3], booleans[4], pid))
        conn.commit()
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    
    finally:
        cur.close()
        conn.close()
        print("Booleans have been restored!")

def interface(pid=None):
    """
    Displays an interface for interacting with participant data and various options.
    Parameters:
    pid (str, optional): The participant ID. If not provided, the user will be prompted to enter one.
    The interface provides the following options:
    0. Exit
    1. Check current state
    2. Feedback
    3. How much to pay?
    4. Long string stats
    5. Reset booleans
    6. Restore booleans
    7. Check Performance
    8. Time spent
    The function connects to a database to retrieve participant information and allows the user to perform various actions based on the participant's data.
    Raises:
    Exception: If there is an error connecting to the database or executing the query.
    Notes:
    - The function will continue to prompt the user for actions until they choose to exit by entering '0'.
    - If an invalid choice is entered, the user will be notified and prompted again.
    - If a 24-character string is entered, the function will recursively call itself with the new participant ID.
    """
    print("Welcome to the interface!")
    if pid is None:
        pid = input("Enter your participant ID: ")

    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT * from participants WHERE pid = %s""", (pid,))
        result = cur.fetchone()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
        if result is None:
            print("Participant does not exist")
            return
        else:
            while True:
                now = datetime.datetime.now()
                print("Current time: ", now.strftime("%d/%m/%Y %H:%M:%S"), "UTC")
                print("What would you like to do?")
                print("0. Exit")
                print("1. Check current state")
                print("2. Feedback")
                print("3. How much to pay?")
                print("4. Long string stats")
                print("5. Reset booleans")
                print("6. Restore booleans")
                print("7. Check Performance")
                print("8. Time spent")

                choice = input("Enter choice: ")
                if choice == "1":
                    current_state(pid)
                
                elif choice == "2":
                    feedback(pid)

                elif choice == "3":
                    how_much_to_pay(pid)

                elif choice == "4":
                    get_long_string_stats(pid)

                elif choice == "5":
                    reset_booleans(pid)

                elif choice == "6":
                    restore_booleans(pid)

                elif choice == "7":
                    process_ratings(pid)

                elif choice == "8":
                    total_time_spent = get_total_time(pid)
                    print("Total time spent on the study:", total_time_spent)

                    time_per_image = get_average_image_time(pid)
                    if time_per_image is None:
                        print("No images viewed!")
                        continue
                    else:
                        print("Average time spent per image:", time_per_image.total_seconds(), "seconds")

                elif choice == "0":
                    break
                
                elif len(choice) == 24:
                    return interface(pid=choice)

                else:
                    print("\n" + color.BOLD + color.RED + "Invalid choice!" + color.END + "\n")


if __name__ == "__main__":
    interface()