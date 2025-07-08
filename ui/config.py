from configparser import ConfigParser
import os


def config(filename="database.ini", section="postgresql"):
    # Use the os.path.dirname to get the current directory
    directory = os.path.dirname(os.path.abspath(__file__))
    # Use the os.path.join to concatenate the directory with the filename
    filename = os.path.join(directory, filename)
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(
            "Section {0} not found in the {1} file".format(section, filename)
        )

    return db


def config_mail(filename="mail.ini", section="intermediary"):
    # Use the os.path.dirname to get the current directory
    directory = os.path.dirname(os.path.abspath(__file__))
    # Use the os.path.join to concatenate the directory with the filename
    filename = os.path.join(directory, filename)
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to mail
    mail = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            mail[param[0]] = param[1]
    else:
        raise Exception(
            "Section {0} not found in the {1} file".format(section, filename)
        )

    return mail


def config_recipient(filename="mail.ini", section="recipient"):
    # Use the os.path.dirname to get the current directory
    directory = os.path.dirname(os.path.abspath(__file__))
    # Use the os.path.join to concatenate the directory with the filename
    filename = os.path.join(directory, filename)
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to mail
    mail = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            mail[param[0]] = param[1]
    else:
        raise Exception(
            "Section {0} not found in the {1} file".format(section, filename)
        )

    return mail


def config_data_storage(filename="data_storage.ini", section="ishihara"):
    # Use the os.path.dirname to get the current directory
    directory = os.path.dirname(os.path.abspath(__file__))
    # Use the os.path.join to concatenate the directory with the filename
    filename = os.path.join(directory, filename)
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # Get section
    data_storage = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            data_storage[param[0]] = param[1]
    else:
        raise Exception(
            "Section {0} not found in the {1} file".format(section, filename)
        )
    return data_storage
