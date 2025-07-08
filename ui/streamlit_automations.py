from db_utils import database_connection
import psycopg2
import numpy as np
import datetime
from data_processing import process_ratings, get_ratings, get_main_study_image_ids, get_sample_averages, get_comprehension_check_image, get_booleans, get_total_time, get_colorblindness_time, get_comprehension_check_time
import streamlit as st
import pandas as pd
from automations import get_booleans, get_average_image_time, get_long_string_stats
import matplotlib.pyplot as plt




def home():
    st.header('Welcome to the SCOOTER Data Analysis App')
    st.write('This application allows you to analyze scooter data collected from various sources. '
             'You can explore different metrics, visualize trends, and gain insights into scooter usage patterns.')

    st.subheader('Features:')
    st.write('- View and analyze scooter ratings')
    st.write('- Process and visualize main study ratings')
    st.write('- Calculate and display sample averages')
    st.write('- Generate charts and graphs for better understanding')

    st.info('Use the sidebar to navigate through different sections of the app.')

def check_pid():
    pid = st.session_state.pid
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT pid FROM participants WHERE pid = %s""", (pid,))
        result = cur.fetchone()
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Database error: {error}")
    finally:
        cur.close()
        conn.close()
        if result is None:
            st.error("Participant ID not found in the database!")
            return False
        return True

def current_state():
    try:
        conn = database_connection()
        cur = conn.cursor()
        
        cur.execute("""SELECT attempted_colorblindness, passed_colorblindness, 
                    attempted_comprehension, passed_comprehension, completed_study
                    FROM participants WHERE pid = %s""", (st.session_state.pid,))
        result = cur.fetchone()

        cur.execute("""SELECT url, time FROM site_logs WHERE pid = %s ORDER BY time DESC""", (st.session_state.pid,))
        last_page = cur.fetchone()

    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Database error: {error}")
    finally:
        cur.close()
        conn.close()

        if result:
            # Create a DataFrame from the result
            df = pd.DataFrame([result], columns=[
                'Attempted Colorblindness', 
                'Passed Colorblindness', 
                'Attempted Comprehension', 
                'Passed Comprehension', 
                'Completed Study'
            ])
            # Don't show the index
            df.index = ['']

            # Replace boolean values with 'Yes' or 'No'
            df = df.replace({True: 'Yes', False: 'No', None: ''})
            st.table(df)

            if last_page is not None:
                # Make the page name more readable
                page_name = last_page[0].split("/")[-1]
                page_name = page_name.split("?")[0]
                page_name = page_name.split("-")
                page_name = [s.capitalize() for s in page_name]    
                page_name = " ".join(page_name)

                # Make the time more readable by formatting it as DD/MM/YYYY HH:MM:SS
                time = last_page[1].strftime("%d/%m/%Y %H:%M:%S") + " UTC"

                st.text(f"Last visited page: {page_name}")
                st.text(f"Time last visited: {time}")
            else:
                st.text("No pages visited!")
        else:
            st.text("No data found for the given participant ID.")

def time_setup():
    st.session_state.colorblindness_time = st.number_input("Time required for the colorblindness test (in minutes):", value=st.session_state.colorblindness_time)
    st.session_state.comprehension_time = st.number_input("Time required for the comprehension test (in minutes):", value=st.session_state.comprehension_time)
    st.session_state.main_study_time = st.number_input("Time required for the main study (in minutes):", value=st.session_state.main_study_time)
    
    # Calculate the total time
    st.session_state.total_time = st.session_state.colorblindness_time + st.session_state.comprehension_time + st.session_state.main_study_time
    st.info(f"Calculated Total Time: {st.session_state.total_time} minutes")
    
    st.session_state.total_payment = st.number_input("Total payment for the study (in pounds):", value=st.session_state.total_payment)

def participant_time_stats():
    pid = st.session_state.pid

    try:
        average_image_time = get_average_image_time(pid)
        avg_img_in_seconds = average_image_time.total_seconds()
        
        thresholds = [2, 3.25, 4.5]
        if avg_img_in_seconds < thresholds[0]:
            st.error(f"Average time spent on images is less than 2 seconds! ({avg_img_in_seconds:.2f} seconds)")
        elif avg_img_in_seconds < thresholds[1]:
            st.warning(f"Average time spent on images is less than 3.25 seconds! ({avg_img_in_seconds:.2f} seconds)")
        elif avg_img_in_seconds < thresholds[2]:
            st.info(f"Average time spent on images is less than 4.5 seconds! ({avg_img_in_seconds:.2f} seconds)")
        else:
            st.success(f"Average time spent on images: {avg_img_in_seconds:.2f} seconds")
    except Exception as e:
        st.error(f"Main study time could not be calculated! (Probably because the participant has not completed the study yet.)")

    total_time = get_total_time(pid)
    colorblindness_time = get_colorblindness_time(pid)
    comprehension_time = get_comprehension_check_time(pid)

    # Initialize time variables
    total_time_minutes = "N/A"
    total_time_seconds = "N/A"
    colorblindness_time_minutes = "N/A"
    colorblindness_time_seconds = "N/A"
    comprehension_time_minutes = "N/A"
    comprehension_time_seconds = "N/A"
    main_study_time_minutes = "N/A"
    main_study_time_seconds = "N/A"

    if total_time is None:
        st.error("Total time could not be calculated! (Probably because the participant has not completed the study yet.)")
    else:
        total_time_minutes = int(total_time.total_seconds() // 60)
        total_time_minutes = str(total_time_minutes) if total_time_minutes >= 10 else "0" + str(total_time_minutes)

        total_time_seconds = int(total_time.total_seconds() % 60)
        total_time_seconds = str(total_time_seconds) if total_time_seconds >= 10 else "0" + str(total_time_seconds)

    if colorblindness_time is None:
        st.error("Colorblindness time could not be calculated! (Probably because the participant has not completed the colorblindness test yet.)")
    else:
        colorblindness_time_minutes = int(colorblindness_time.total_seconds() // 60)
        colorblindness_time_minutes = str(colorblindness_time_minutes) if colorblindness_time_minutes >= 10 else "0" + str(colorblindness_time_minutes)

        colorblindness_time_seconds = int(colorblindness_time.total_seconds() % 60)
        colorblindness_time_seconds = str(colorblindness_time_seconds) if colorblindness_time_seconds >= 10 else "0" + str(colorblindness_time_seconds)

    if comprehension_time is None:
        st.error("Comprehension time could not be calculated! (Probably because the participant has not completed the comprehension test yet.)")
    else:
        comprehension_time_minutes = int(comprehension_time.total_seconds() // 60)
        comprehension_time_minutes = str(comprehension_time_minutes) if comprehension_time_minutes >= 10 else "0" + str(comprehension_time_minutes)

        comprehension_time_seconds = int(comprehension_time.total_seconds() % 60)
        comprehension_time_seconds = str(comprehension_time_seconds) if comprehension_time_seconds >= 10 else "0" + str(comprehension_time_seconds)

    if total_time is not None and colorblindness_time is not None and comprehension_time is not None:
        main_study_time = total_time - colorblindness_time - comprehension_time
        main_study_time_minutes = int(main_study_time.total_seconds() // 60)
        main_study_time_minutes = str(main_study_time_minutes) if main_study_time_minutes >= 10 else "0" + str(main_study_time_minutes)
        main_study_time_seconds = int(main_study_time.total_seconds() % 60)
        main_study_time_seconds = str(main_study_time_seconds) if main_study_time_seconds >= 10 else "0" + str(main_study_time_seconds)
    else:
        st.error("Main study time could not be calculated! (Probably because the participant has not completed all parts of the study yet.)")

    # Create a DataFrame for the time metrics
    time_data = {
        'Metric': ['Colorblindness Time', 'Comprehension Time', 'Main Study Time' , 'Total Time'],
        'Time (minutes)': [f"{colorblindness_time_minutes}:{colorblindness_time_seconds}", 
                           f"{comprehension_time_minutes}:{comprehension_time_seconds}", 
                           f"{main_study_time_minutes}:{main_study_time_seconds}", 
                           f"{total_time_minutes}:{total_time_seconds}"]
    }
    time_df = pd.DataFrame(time_data)
    
    # Display the DataFrame as a table
    st.table(time_df)

# Initialize session state variables
if 'total_time' not in st.session_state:
    st.session_state.total_time = 18
if 'colorblindness_time' not in st.session_state:
    st.session_state.colorblindness_time = 0.5
if 'comprehension_time' not in st.session_state:
    st.session_state.comprehension_time = 6.0
if 'main_study_time' not in st.session_state:
    st.session_state.main_study_time = 11.5
if 'total_payment' not in st.session_state:
    st.session_state.total_payment = 2.70

def how_much_to_pay():
    pid = st.session_state.pid
    booleans = get_booleans(pid)
    prolific_minimum = 0.10

    st.session_state.total_time = st.session_state.colorblindness_time + st.session_state.comprehension_time + st.session_state.main_study_time
    total_time = st.session_state.total_time
    colorblindness_time = st.session_state.colorblindness_time
    comprehension_time = st.session_state.comprehension_time
    main_study_time = st.session_state.main_study_time
    total_payment = st.session_state.total_payment

    if booleans is None:
        st.error("NOTHING, participant has NOT consented to the study (yet)!")
        return

    if not booleans[0]:
        st.warning("Participant has not attempted the colorblindness test!")
        st.info(f"Payment: {max(prolific_minimum, 0):.2f}£")
        return
    
    if not booleans[1]:
        st.error("Participant has not passed the colorblindness test!")
        output = max(prolific_minimum, total_payment * (colorblindness_time / total_time))
        st.info(f"Payment: {output:.2f}£")
        return

    st.success("Participant has passed the colorblindness test!")

    if not booleans[2]:
        st.warning("Participant has not attempted the comprehension test!")
        output = max(prolific_minimum, total_payment * (colorblindness_time / total_time))
        st.info(f"Payment: At least {output:.2f}£")
        return

    if not booleans[3]:
        st.error("Participant has not passed the comprehension test!")
        output = max(prolific_minimum, total_payment * (comprehension_time / total_time))
        st.info(f"Payment: {output:.2f}£")
        return
    
    st.success("Participant has passed the comprehension test!")

    if not booleans[4]:
        st.error("Participant has not completed the study!")
        output = max(prolific_minimum, total_payment * (comprehension_time / total_time))
        st.info(f"Payment: At least {output:.2f}£")
        return

    st.success("Participant has completed the study!")
    output = max(prolific_minimum, total_payment * (main_study_time / total_time))

    user_data = process_ratings(pid, post_hoc=False)
    if user_data[-1] <= 0.67:
        st.error(f"Participant has failed more than one attention check! (Accuracy: {user_data[-1]:.2f})")
        st.info(f"Payment: {output:.2f}£")
        return
    elif user_data[-1] <= 0.83:
        st.warning("Participant has failed one attention check!")
    else:
        st.success("Participant has passed all attention checks!")

    verdict = f"Payment: Undecided. Please check the participants answers! Payment could be deducted to {output:.2f}£"
    verdict += "\nDeduct payment if either 2/3 categories (time, long string, IRV) serve a purple warning, or if 1 provides a purple warning and 2 provide a yellow warning."
    sus_time = True
    sus_long_string = False
    sus_irv = False

    average_image_time = get_average_image_time(pid)
    avg_in_seconds = average_image_time.total_seconds()

    if avg_in_seconds < 2:
        st.error(f"Average time spent on images is less than 2 seconds! ({avg_in_seconds:.2f})")
        st.info(f"Payment: {output:.2f}£")
        return
    elif avg_in_seconds < 3.25:
        st.warning(f"Average time spent on images is less than 3.25 seconds! ({avg_in_seconds:.2f})")
    elif avg_in_seconds < 4.5:
        st.warning(f"Average time spent on images is less than 4.5 seconds! ({avg_in_seconds:.2f})")
    else:
        st.success("Average time spent on images is at least 4.5 seconds!")
        sus_time = False

    sequences, max_length, mean_length, median_length = get_long_string_stats(pid, intermediate=True)

    if max_length > 8 or mean_length > 2.7 or median_length != 2:
        st.warning(f"Participant has unusual long string stats! (Max: {max_length}, Mean: {mean_length:.2f}, Median: {median_length})")
        sus_long_string = True
    else:
        st.success("Participant's long string stats are within the norm!")

    x, y = get_sample_averages([pid], only_arrays=True)
    real_images_sd = np.std(x, ddof=1)
    modified_images_sd = np.std(y, ddof=1)

    if real_images_sd > 1.87 or modified_images_sd > 1.69 or real_images_sd < 0.6 or modified_images_sd < 0.64:
        st.warning(f"Participant has unusual IRV stats! (Real SD: {real_images_sd:.2f}, Modified SD: {modified_images_sd:.2f})")
        sus_irv = True
    else:
        st.success("Participant's IRV stats are within the norm!")

    if sus_irv or sus_long_string or sus_time:
        st.info(verdict)
        return

    st.success(f"Payment: {total_payment:.2f}£")

def feedback():
    pid = st.session_state.pid

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
            st.info("No feedback given!")
            return
        
        if result[1] == "None" or result[1] == "":
            st.info("No descriptive feedback provided.")
        else:
            st.write("**Feedback given:**")
            st.write(result[1])

        answers = result[2]
        if answers is None:
            st.info("No Likert scale rating provided.")
            return
        st.write("**Likert scale rating:**")

        statements = [
            "1.) My responses to items on this survey are accurate.",
            "2.) I exerted sufficient effort on this survey.",
            "3.) I answered items on this survey without reading them.",
            "4.) I randomly responded to some survey items.",
            "5.) I rushed through this survey.",
            "6.) I thought carefully about each of my responses on this survey.",
            "7.) The researchers should include my data in the results.",   
        ]

        for i, statement in enumerate(statements):
            if answers[i] is None:
                st.write(f"{statement} **No response**")
        else: 
            answer = int(answers[i])
            color = "green" if (answer >= 3 and i not in [2, 3, 4]) or (answer <= 3 and i in [2, 3, 4]) else "red"
            st.write(f"{statement} **:{color}[{likert[answer]}]**")

from PIL import Image
import io

# def display_image_from_bytes(image_bytes):
#     # Convert bytes data to a streamlit compatible image
#     image = Image.open(io.BytesIO(image_bytes))
#     st.image(image, use_column_width=True)

def get_colorblind_image(id, answer):
    try:
        connection = database_connection()
        cursor = connection.cursor()
        cursor.execute("""SELECT * 
                          FROM ishihara_test_cards 
                          WHERE id = %s""", (id,))
        
        row = cursor.fetchone()
        if row:
            image = row[1]
            color_type = row[2]
            digit = row[3]

    except (Exception, psycopg2.Error) as error:
        st.error(f"Error while fetching data from PostgreSQL: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
        image = Image.open(io.BytesIO(image))
        correct = "Correct" if answer == digit else "Incorrect"
        is_success = answer == digit
        return image, color_type, digit, answer, correct, is_success
        #return st.image(image, caption=f"Color Type: {color_type}, Digit: {digit}", use_container_width=True), st.info(f"Answer: {answer} is {correct}", color=color)

def colorblindness_data():
    pid = st.session_state.pid

    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT ishihara_test_cards, colorblind_answers
                       FROM participants 
                       WHERE pid = %s""", (pid,))
        result = cur.fetchone()

    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Database error: {error}")
    finally:
        cur.close()
        conn.close()

        if not result:
            st.error("No data found for the given participant ID.")
            return

        if 'image_index' not in st.session_state:
            st.session_state.image_index = 0

        def next_image():
            st.session_state.image_index = (st.session_state.image_index + 1) % len(result[0])

        def prev_image():
            st.session_state.image_index = (st.session_state.image_index - 1) % len(result[0])

        current_card = result[0][st.session_state.image_index]
        current_answer = result[1][st.session_state.image_index]

        output = get_colorblind_image(current_card, current_answer)

        if output[5]:
            st.success(f"Answer: {output[3]} is {output[4]}")
        else:
            st.error(f"Answer: {output[3]} is {output[4]}")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.button("Previous", on_click=prev_image)
        with col3:
            st.button("Next", on_click=next_image)
        with col2:
            st.image(output[0], caption=f"Color Type: {output[1]}, Digit: {output[2]}", use_container_width=True)

def get_comprehension_check_image(id):
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT image
                       FROM comprehension_check_images 
                       WHERE id = %s""", (id,))
        row = cur.fetchone()
        image = row[0]

    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Database error: {error}")
    finally:
        cur.close()
        conn.close()

        image = Image.open(io.BytesIO(image))
        return image

def comprehension_check_data():
    pid = st.session_state.pid
    
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT comprehension_check_images, comprehension_check_answers, correct_comprehension_check_answers
                       FROM participants 
                       WHERE pid = %s""", (pid,))
        result = cur.fetchone()

    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Database error: {error}")
    finally:
        cur.close()
        conn.close()

        if 'cc_image_pair_index' not in st.session_state:
            st.session_state.cc_image_pair_index = 0

        def next_image():
            st.session_state.cc_image_pair_index = (st.session_state.cc_image_pair_index + 1) % (len(result[0]) // 2)

        def prev_image():
            st.session_state.cc_image_pair_index = (st.session_state.cc_image_pair_index - 1) % (len(result[0]) // 2)

        index = st.session_state.cc_image_pair_index * 2
        current_card_1 = result[0][index]
        current_card_2 = result[0][index + 1]
        current_answer = result[1][st.session_state.cc_image_pair_index]
        correct_answer = result[2][st.session_state.cc_image_pair_index]

        image_1 = get_comprehension_check_image(current_card_1)
        image_2 = get_comprehension_check_image(current_card_2)

        correct = int(current_answer) == correct_answer
        chosen_side = "left"

        if current_answer == current_card_2:
            chosen_side = "right"

        if correct:
            st.success(f"Participant chose the correct image on the **{chosen_side}** side!")
        else:
            st.error(f"Participant chose the wrong image on the *{chosen_side}* side!")

        col1, col2 = st.columns([1, 1])
        with col1:
            st.button("Previous", on_click=prev_image, key="prev_cc_pair")
        with col2:
            st.button("Next", on_click=next_image, key="next_cc_pair")
 
        col3, col4 = st.columns([1, 1])
        with col3:
            st.image(image_1, use_container_width=True)
        with col4:
            st.image(image_2, use_container_width=True)

def get_attention_check_image(id):
    try:
        conn = database_connection()
        cur = conn.cursor()
        cur.execute("""SELECT image, is_imc, correct_value
                       FROM attention_check_images 
                       WHERE id = %s""", (id,))
        row = cur.fetchone()
        image = row[0]
        is_imc = row[1]
        correct_value = row[2]

    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Database error: {error}")
    finally:
        cur.close()
        conn.close()

        image = Image.open(io.BytesIO(image))
        return image, is_imc, correct_value

def atc_data():
    pid = st.session_state.pid
    data = get_ratings(pid)
    image_ids = get_main_study_image_ids(pid)
    if data is None:
        st.error("No data found for the given participant ID.")
        return
    main_study_answers = data[0][0]
    imc_indices = data[0][3]
    atc_indices = data[0][4]

    # Concat the two indices lists
    indices = imc_indices + atc_indices

    if 'atc_image_index' not in st.session_state:
        st.session_state.atc_image_index = 0
    
    def next_image():
        st.session_state.atc_image_index = (st.session_state.atc_image_index + 1) % len(indices)
    
    def prev_image():
        st.session_state.atc_image_index = (st.session_state.atc_image_index - 1) % len(indices)
    
    index = indices[st.session_state.atc_image_index]
    image, is_imc, correct_value = get_attention_check_image(image_ids[index])

    if is_imc:
        info_text = "This is an instruction manipulation check, which means the participant should choose a specific option."

        if main_study_answers[index] == correct_value:
            st.success(info_text + "\n" + "Participant chose the correct option!")
        
        else:
            st.error(info_text + "\n" + "Participant chose the wrong option! (Rating: " + main_study_answers[index] + ") --- Correct option: " + str(correct_value))
    
    else:
        info_text = "This is an attention check, which means the participant should rate an obviosly modified image as such."

        if int(main_study_answers[index]) < 0:
            st.success(info_text + "\n" + "Participant correctly rated the image as modified! (Rating: " + main_study_answers[index] + ")")
        
        else:
            st.error(info_text + "\n" + "Participant chose the wrong option! (Rating: " + main_study_answers[index] + ")")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.button("Previous", on_click=prev_image, key="prev_atc")
    with col3:
        st.button("Next", on_click=next_image, key="next_atc")
    with col2:
        st.image(image, use_container_width=True)



# Set up the Streamlit app
st.title('SCOOTER Data Analysis')

img_icon = Image.open('static/images/Branding/ScooterFavicon.png')
st.logo(img_icon)

# Sidebar
st.sidebar.title('Navigation')

# Sidebar options
option = st.sidebar.selectbox(
    'Select a feature',
    ('Home', 'Current User Overview', 'How Much to Pay?'),
    index=0  # Set 'Home' as the default option
)

if option == 'Home':
    home()

# PID input widget
if 'pid' not in st.session_state:
    st.session_state.pid = ''

st.sidebar.text_input('Enter your participant ID:', key='pid')

if not st.session_state.pid:
    st.sidebar.error('Please enter a participant ID to proceed.')

if option == 'Current User Overview':
    
    if not st.session_state.pid:
        st.error('Please enter a participant ID to view the current state.')
    
    elif check_pid():
        st.info('Participant ID: **' + st.session_state.pid + '**')

        booleans = get_booleans(st.session_state.pid)

        st.subheader('Current State of Participant', divider=True)
        current_state()

        st.subheader('Time Statistics', divider=True)
        participant_time_stats()

        st.subheader('Performance Overview', divider=True)
        data = process_ratings(st.session_state.pid, post_hoc=False)
        if data is None:
            st.error("Participant has not completed the study!")
        
        if data is not None:
            performance_data = {
                'Metric': ['Overall Accuracy', 'Real Accuracy', 'Modified Accuracy' , 'Check Accuracy'],
                'Performance (max. = 1.0)': ["%1.2f" % data[1], data[2], data[3], data[4]]
            }

            performance_df = pd.DataFrame(performance_data)
    
            # Display the DataFrame as a table
            st.table(performance_df)

            sequences, max_length, mean_length, median_length = get_long_string_stats(st.session_state.pid, intermediate=True)

            x, y = get_sample_averages([st.session_state.pid], only_arrays=True)
            real_images_sd = np.std(x, ddof=1)
            modified_images_sd = np.std(y, ddof=1)

            st.subheader("Long String Statistics", divider=True)
            ls_data = {
                'Metric': ['Max Length', 'Mean Length', 'Median Length'],
                'Values': [max_length, mean_length, median_length]
            }

            ls_df = pd.DataFrame(ls_data)
            st.table(ls_df)

            st.subheader("IRV Statistics", divider=True)
            irv_data = {
                'Metric': ['Real Images SD', 'Modified Images SD'],
                'Values': [real_images_sd, modified_images_sd]
            }

            irv_df = pd.DataFrame(irv_data)
            st.table(irv_df)

        if booleans[0] == False:
            st.info("Participant has not attempted the colorblindness test!")
            st.subheader("Comprehension Check Data", divider=True)
            st.info("Participant has not attempted the comprehension check!")
            st.subheader("Attention Check Data", divider=True)
            st.info("Participant has not completed the study!")

        if booleans[0] == True:
            st.subheader("Colorblindness Test Data", divider=True)
            if booleans[1] == False:
                st.warning("Participant has not passed the colorblindness test!")
            else:
                st.success("Participant has passed the colorblindness test!")
            colorblindness_data()

            if booleans[2] == False:
                st.subheader("Comprehension Check Data", divider=True)
                st.warning("Participant has not attempted the comprehension check!")
                st.subheader("Attention Check Data", divider=True)
                st.info("Participant has not completed the study!")
            
            if booleans[2] == True:
                st.subheader("Comprehension Check Data", divider=True)

                if booleans[3] == False:
                    st.warning("Participant has not passed the comprehension check!")
                    comprehension_check_data()
                    st.subheader("Attention Check Data", divider=True)
                    st.info("Participant has not completed the study!")
                    
                else:
                    st.success("Participant has passed the comprehension check!")

                    comprehension_check_data()
                    st.subheader("Attention Check Data", divider=True)
                    if booleans[4] == False:
                            st.warning("Participant has not completed the study!")
                    else:
                        st.success("Participant has completed the study!")
                        atc_data()

        st.subheader('Feedback of Participant', divider=True)
        feedback()

if option == 'How Much to Pay?':

    st.text("""This section calculates the payment for the participant based on the study completion status and other factors""")

    if not st.session_state.pid:
        st.error('Please enter a participant ID to calculate the payment.')

    elif check_pid():
        st.subheader('Study Parameters', divider=True)
        st.text("""You can use the below inputs to adjust the study parameters if needed.""")
        time_setup()

        st.subheader('Calculate Payment', divider=True)
        st.text("Click the button below to calculate the payment for the participant.")
        if st.button("Calculate Payment"):
            how_much_to_pay()