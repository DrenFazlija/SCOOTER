from getpass import getpass
import os

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

    mail_server = input("Please enter your mail server: ")
    mail_port = input("Please enter your mail port: ")
    mail_username = input("Please enter your mail username: ")
    mail_password = getpass("Please enter your mail password: ")
    mail_use_tls = input("Please enter your mail use tls: ")
    recipient = input("Please enter the recipient email address: ")

    create_file("mail.ini")
    file = open("mail.ini", "w")
    file.write("[intermediary]\n")
    file.write("MAIL_SERVER=" + mail_server + "\n")
    file.write("MAIL_PORT=" + mail_port + "\n")
    file.write("MAIL_USERNAME=" + mail_username + "\n")
    file.write("MAIL_PASSWORD=" + mail_password + "\n")
    file.write("MAIL_USE_TLS=" + mail_use_tls + "\n")

    file.write("[recipient]\n")
    file.write("ADDRESS=" + recipient + "\n")

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

def display_ascii_art(file_path):
    with open(file_path, "r") as file:
        ascii_art = file.read()
        print(ascii_art)

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

def check_debug_key():
    print("Checking for debug key file (used to enter the debug mode)...")

    if check_file_existence("debug.key"):
        print("Debug key file found.")
        return

    print("Debug key file not found.")

    ask_for_random_key = input("Do you want to generate a random debug key? If you choose no (\"n\"), you will have to provide a key in the next prompt (y/n): ")

    if ask_for_random_key == "n":
        secret_key = getpass("Please enter a secret debug key: ")
    else:
        import secrets
        secret_key = secrets.token_hex(48)

    create_file("debug.key")
    file = open("debug.key", "w")
    file.write(secret_key)
    file.close()

    print("Debug key file created.")

if __name__ == "__main__":
    try:
        # ASCII art generated via https://www.asciiart.eu/image-to-ascii
        display_ascii_art("static/images/Branding/ascii_art.txt")

    finally:
        print("")
        print("")

    print("Welcome to the setup script for the Human Image Evaluation webpage.")

    print("")
    print(
        "This script will guide you through the setup process. Please follow the instructions carefully."
    )
    print(
        "If you have any questions, please contact the developer. You can find the contact information in the README.md file."
    )
    print("")

    sk_input = None
    debug_input = None
    mail_input = None
    db_input = None

    while sk_input != "y" and sk_input != "n":
        sk_input = input("Do you want to setup the secret key (mandatory for handling Flask sessions) right now? (y/n): ")
        if sk_input == "y":
            check_secret_key()
            break
        if sk_input == "n":
            break
        else:
            print("Invalid input. Please enter either \"y\" or \"n\".")
    
    while debug_input != "y" and debug_input != "n":
        debug_input = input("Do you want to setup the debug key (used to enter the debug mode) right now? (y/n): ")
        if debug_input == "y":
            check_debug_key()
            break
        if debug_input == "n":
            break
        else:
            print("Invalid input. Please enter either \"y\" or \"n\".")

    while mail_input != "y" and mail_input != "n":
        mail_input = input("Do you want to setup the mail configuration right now? This includes the mail service that you will use to send out mails and your recipient mail. (y/n): ")
        if mail_input == "y":
            check_mail_config()
            break
        if mail_input == "n":
            break
        else:
            print("Invalid input. Please enter either \"y\" or \"n\".")
    
    while db_input != "y" and db_input != "n":
        db_input = input("Do you want to setup the database configuration right now? This includes the database that you will use to store the data. (y/n): ")
        if db_input == "y":
            check_database_config()
            break
        if db_input == "n":
            break
        else:
            print("Invalid input. Please enter either \"y\" or \"n\".")
    
    print("Setup complete.")