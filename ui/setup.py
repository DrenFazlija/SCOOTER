from getpass import getpass
import os
from db_utils import execute_sql_file, configure_image_db
import psycopg2
from configparser import ConfigParser
from tqdm import tqdm


def check_file_existence(filename):
    """
    This function checks whether the given file exists in the current directory.
    :return: boolean indicating existence of file
    """
    directory = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(directory):
        if file == filename:
            return True
    return False


def create_file(filename):
    """
    This function creates a file with the given filename in the current directory.
    :return: None
    """
    directory = os.path.dirname(os.path.abspath(__file__))
    file = open(filename, "w")
    file.close()


def check_mail_config():
    print("Checking for mail configuration file...")

    if check_file_existence("mail.ini"):
        print("Mail configuration file found.")
        return

    print("Mail configuration file not found.")

    dummy = input("Would you like to set up a dummy mail configuration for quick testing? (y/n): ")

    if dummy == "y":
        print("Setting up dummy mail configuration...")
        create_file("mail.ini")
        file = open("mail.ini", "w")
        file.write("[intermediary]\n")
        file.write("MAIL_SERVER=smtp.gmail.com\n")
        file.write("MAIL_PORT=587\n")
        file.write("MAIL_USERNAME=DUMMY_USERNAME\n")
        file.write("MAIL_PASSWORD=DUMMY_PASSWORD\n")
        file.write("MAIL_USE_TLS=True\n")
        file.write("[recipient]\n")
        file.write("ADDRESS=DUMMY_ADDRESS\n")
        file.close()
        print("Dummy mail configuration set up.")
        print("Important: This is a dummy configuration and will not work for actual email sending.")
        print("Please delete the dummy configuration after testing and setup the real configuration.")
    
    else:
        print("Please enter your mail server: ")
        mail_server = input()
        print("Please enter your mail port: ")
        mail_port = input()
        print("Please enter your mail username: ")
        mail_username = input()
        print("Please enter your mail password: ")
        mail_password = getpass()
        print("Please enter your mail use tls: ")
        mail_use_tls = input()
        print("Please enter the address of the recipient: ")
        recipient_address = input()
        
        create_file("mail.ini")
        file = open("mail.ini", "w")
        file.write("[intermediary]\n")
        file.write("MAIL_SERVER=" + mail_server + "\n")
        file.write("MAIL_PORT=" + mail_port + "\n")
        file.write("MAIL_USERNAME=" + mail_username + "\n")
        file.write("MAIL_PASSWORD=" + mail_password + "\n")
        file.write("MAIL_USE_TLS=" + mail_use_tls + "\n")
        file.write("[recipient]\n")
        file.write("ADDRESS=" + recipient_address + "\n")
        file.close()
        print("Mail configuration file created.")


def check_database_config():
    print("Checking for database configuration file...")

    if check_file_existence("database.ini"):
        print("Database configuration file found.")

    else:
        print("Database configuration file not found.")

        postgresql = input("Do you have a PostgreSQL database? (y/n): ")

        if postgresql == "n":
            print("This script only supports PostgreSQL databases.")
            print("Please contact the developer for support.")
            print("You can find the contact information in the README.md file.")
            exit()

        host = input("Please enter your database host: ")
        dbname = input("Please enter your database name: ")
        user = input("Please enter your database username: ")
        password = getpass("Please enter your database password: ")

        create_file("database.ini")
        file = open("database.ini", "w")
        file.write("[postgresql]\n")
        file.write("host=" + host + "\n")
        file.write("dbname=" + dbname + "\n")
        file.write("user=" + user + "\n")
        file.write("password=" + password + "\n")
        file.close()

        print("Database configuration file created.")

        print("")


def setup_database():
    continue_setup = input("Would you like to continue setup? (y/n): ")
    if continue_setup == "n":
        print("Setup cancelled.")
        return

    print("")
    #file_path = input("Please enter the relative path to the SQL script: ")
    #print("")
    print("Setting up database...")
    execute_sql_file('schema.sql')
    config = ConfigParser()
    config.read('database.ini')
    db_params = config['postgresql']
    user = db_params['user']
    print("Granting privileges to the web agent...")
    grant_user(user)


def grant_user(new_user):
    # Read database config
    config = ConfigParser()
    config.read('database.ini')
    db_params = config['postgresql']

    # Connect as admin user
    conn = psycopg2.connect(
        host=db_params['host'],
        dbname=db_params['dbname'],
        user="postgres",
        password="postgres"
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Create new user
    cur.execute(f"CREATE USER {new_user} WITH PASSWORD '{new_user}';")

    # Grant rights on all existing tables
    cur.execute(f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO {new_user};")

    cur.close()
    conn.close()
    print(f"User {new_user} privileges granted.")


def display_ascii_art(file_path):
    with open(file_path, "r") as file:
        ascii_art = file.read()
        print(ascii_art)


def create_image_db(path, image_type="ishihara"):
    """
    This function creates the image database for all phases of the study.
    :param path: the relative path to the image directory
    :param image_type: the type of image to upload
    :return: None
    """

    # Check if the image directory exists
    if not os.path.isdir(path):
        print("Image directory not found.")
        print("Please check the path and try again.")

        print("")
        try_again = input("Would you like to try again? (y/n): ")
        if try_again == "y":
            print("")
            ishihara_path = input(
                "Please enter the relative path to the ishihara test cards for the colorblindness tests: "
            )
            print("")
            create_image_db(ishihara_path)
        else:
            continue_setup = input("Would you like to continue setup? (y/n): ")
            if continue_setup == "y":
                upload_images(skip_ishihara=True)
            else:
                exit()

    else:
        name_of_db = None
        print("Creating image database...")

        if image_type == "ishihara":
            print("Uploading ishihara test cards...")
            name_of_db = "ishihara_test_cards"

        elif image_type == "attention_check":
            print("Uploading attention check images...")
            name_of_db = "attention_check_images"

        elif image_type == "real":
            print("Uploading real images...")
            name_of_db = "real_images"

        elif image_type == "modified":
            print("Uploading modified images...")
            name_of_db = "modified_images"

        print("")

        # Connect to the database
        configure_image_db(path, name_of_db)


def upload_images(
    skip_ishihara=False,
    skip_attention_check=False,
    skip_real_images=False,
    skip_modified_images=False,
):
    if not skip_ishihara:
        ready_for_ishihara = input(
            "Are you ready to upload the ishihara test cards? (y/n): "
        )

        if ready_for_ishihara == "y":
            ishihara_path = input(
                "Please enter the relative path to the ishihara test cards for the colorblindness tests: "
            )
            print("")
            create_image_db(ishihara_path)

        else:
            print("Skipping ishihara test cards...")
            print("")
    
    if not skip_attention_check:
        ready_for_attention_check = input(
            "Are you ready to upload the attention check images? (y/n): "
        )

        if ready_for_attention_check == "y":
            attention_check_path = input(
                "Please enter the relative path to the attention check images: "
            )
            print("")
            create_image_db(attention_check_path, image_type="attention_check")

        else:
            print("Skipping attention check images...")
            print("")

    if not skip_real_images:
        ready_for_real_images = input(
            "Are you ready to upload the real images? (y/n): "
        )

        if ready_for_real_images == "y":
            real_images_path = input(
                "Please enter the relative path to the real images: "
            )
            print("")
            create_image_db(real_images_path, image_type="real")

        else:
            print("Skipping real images...")
            print("")
    
    if not skip_modified_images:
        ready_for_modified_images = input(
            "Are you ready to upload the modified images? (y/n): "
        )

        if ready_for_modified_images == "y":
            modified_images_path = input(
                "Please enter the relative path to the modified images: "
            )
            print("")
            create_image_db(modified_images_path, image_type="modified")

        else:
            print("Skipping modified images...")
            print("")
   

def setup_existing_data():
    print("Setting up existing data...")
    directory = input("Enter the path to the directory containing the CSV files: ")

    table_names = {
        "atc": "attention_check_images",
        "real": "real_images",
        "modified": "modified_images",
        "ishihara": "ishihara_test_cards",
        "cc": "comprehension_check_images"
    }

    # Read database config
    config = ConfigParser()
    config.read('database.ini')
    db_params = config['postgresql']

    try:
        conn = psycopg2.connect(
            host=db_params['host'],
            dbname=db_params['dbname'],
            user="postgres",
            password="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        print("Importing data (this may take a while)...")
        print("")
        for file in tqdm(os.listdir(directory), desc="Importing data"):
            if file.endswith('.csv'):
                base = file.split('.')[0]  # gets 'modified' from 'modified.csv'
                if base in table_names:
                    table_name = table_names[base]
                    with open(os.path.join(directory, file), 'r') as f:
                        sql = f"COPY {table_name} FROM STDIN WITH CSV HEADER DELIMITER ','"
                        cur.copy_expert(sql, f)
                else:
                    print(f"Warning: No table mapping for file {file}")
        cur.close()
        conn.close()
        print(f"Data imported successfully into!")
    except Exception as e:
        print(f"Failed to import data: {e}")


def check_secret_key():
    print("Checking for secret key file...")

    if check_file_existence("secret.key"):
        print("Secret key file found.")
        return

    print("Secret key file not found.")

    ask_for_random_key = input("Do you want to generate a random secret key? If you choose no (\"n\"), you will have to provide a secret key in the next prompt (y/n): ")

    if ask_for_random_key == "n":
        secret_key = getpass("Please enter a secret key: ")
    else:
        import secrets
        secret_key = secrets.token_hex(48)

    create_file("secret.key")
    file = open("secret.key", "w")
    file.write(secret_key)
    file.close()

    print("Secret key file created.")

def check_attack_config():
    print("Checking for attack configuration file...")

    file_exists = check_file_existence("attack.ini")
    overwrite = "n"

    if file_exists:
        print("Attack configuration file found.")
        overwrite = input("Would you like to overwrite the attack configuration file? (y/n): ")

    if overwrite == "y" or not file_exists:
        print("Make sure to use the same name as in the setup of the data")
        print("Here is the list of the available options:")
        print("1) semanticadv (SemanticAdv)")
        print("2) ncf (Natural Color Fool)")
        print("3) cadv (cAdv)")
        print("4) diffattack (DiffAttack)")
        print("5) advpp (AdvPP)")
        print("6) aca (ACA)")
        print("7) Your own attack")
        
        print("")
        option = input("Please enter the number of the attack: ")

        if option == "1":
            attack_name = "semanticadv"
        elif option == "2":
            attack_name = "ncf"
        elif option == "3":
            attack_name = "cadv"
        elif option == "4":
            attack_name = "diffattack"
        elif option == "5":
            attack_name = "advpp"
        elif option == "6":
            attack_name = "aca"
        elif option == "7":
            attack_name = input("Please enter the name of the attack: ")
        else:
            print("Invalid option. Please try again.")
            return

        print("Overwriting attack configuration file...")
        create_file("attack.ini")
        file = open("attack.ini", "w")
        file.write("[attack]\n")
        file.write("name=" + attack_name + "\n")
        file.close()
        print("Attack configuration file created.")


if __name__ == "__main__":
    try:
        # ASCII art generated via https://www.asciiart.eu/image-to-ascii
        display_ascii_art("static/images/Branding/ascii_art.txt")

    finally:
        print("")
        print("")

    print("Welcome to the setup script for the SCOOTER web app.")

    print("")
    print(
        "This script will guide you through the setup process. Please follow the instructions carefully."
    )
    print(
        "If you have any questions, please contact the developer. You can find the contact information in the README.md file."
    )
    print("")

    choice_input = input(
        "What would you like to do? (1) Setup the database (2) Setup existing data (3) Upload new images: "
    )

    if choice_input == "1":
        print("")
        check_mail_config()
        check_attack_config()
        check_secret_key()
        check_database_config()
        setup_database()

    elif choice_input == "2":
        print("")
        setup_existing_data()

    elif choice_input == "3":
        print("")

        ishihara_input = input("Would you like to setup the colorblindness test images? (y/n): ")
        atc_input = input("Would you like to setup the attention check images? (y/n): ")
        real_input = input("Would you like to setup the real images? (y/n): ")
        modified_input = input("Would you like to setup the modified images? (y/n): ")

        skip_ishihara = ishihara_input == "n"
        skip_attention_check = atc_input == "n"
        skip_real_images = real_input == "n"
        skip_modified_images = modified_input == "n"

        upload_images(skip_ishihara=skip_ishihara, skip_attention_check=skip_attention_check, skip_real_images=skip_real_images, skip_modified_images=skip_modified_images)

    else:
        print("Invalid choice. Please try again.")
        exit()


    print("Setup complete.")
