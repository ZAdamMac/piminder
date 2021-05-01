"""
This script is a component of Piminder's back-end controller.
Specifically, it is a helper utility to be used to intialize a database for the user and message tables.
Author: Zac Adam-MacEwen (zadammac@kenshosec.com)

An Arcana Labs utility.
Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/Piminder
"""

import bcrypt
import getpass
import os
import pymysql

__version__ = "1.0.0"  # This is the version of service that we can init, NOT the version of the script itself.

spec_tables = [
    """CREATE TABLE `messages` (
      `id` CHAR(36) NOT NULL,
      `name` VARCHAR(255) NOT NULL,
      `message` TEXT DEFAULT NULL,
      `errorlevel` CHAR(5) DEFAULT NULL,
      `time_raised` TIMESTAMP,
      `read_flag` BIT DEFAULT 0,
      PRIMARY KEY (`id`)
    )""",
    """CREATE TABLE `users` (
      `username` CHAR(36) NOT NULL,
      `password` VARCHAR(255) NOT NULL,
      `permlevel` INT(1) DEFAULT 1,
      `memo` TEXT DEFAULT NULL,
      PRIMARY KEY (`username`)
    )"""
]


def connect_to_db():
    """Detects if it is necessary to prompt for the root password, and either way,
    establishes the db connection, returning it.
    :return:
    """
    print("We must now connect to the database.")
    try:
        db_user = os.environ['PIMINDER_DB_USER']
    except KeyError:
        print("Missing envvar: Piminder_DB_USER")
        exit(1)
    root_password = None
    try:
        root_password = os.environ['PIMINDER_DB_PASSWORD']
    except KeyError:
        print("Missing envvar: Piminder_DB_PASSWORD")
        exit(1)
    try:
        db_host = os.environ['PIMINDER_DB_HOST']
    except KeyError:
        print("Missing envvar: Piminder_DB_HOST")
        exit(1)
    finally:
        conn = pymysql.connect(host=db_host, user=db_user,
                               password=root_password, db='Piminder',
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

    return conn


def create_tables(list_tables, connection):
    """Accepts a list of create statements for tables and pushes them to the DB.
    :param list_tables: A list of CREATE statements in string form.
    :param connection: a pymysql.connect() object, such as returned by connect_to_db
    :return:
    """
    cursor = connection.cursor()
    connection.begin()
    for table in list_tables:
        try:
            cursor.execute(table)
        except pymysql.err.ProgrammingError:
            print("Error in the following statement; table was skipped.")
            print(table)
        except pymysql.err.OperationalError as error:
            if str(error.args[0]) == 1050:  # This table already exists
                print("%s, skipping" % error.args[1])
            else:
                print(error)
    connection.commit()


def create_administrative_user(connection):
    """Creates an administrative user if it does not already exist.

    :param connection:
    :return:
    """

    print("Validating an admin user exists:")
    try:
        admin_name = os.environ['PIMINDER_ADMIN_USER']
    except KeyError:
        print("Missing envvar: Piminder_ADMIN_USER")
        exit(1)

    cur = connection.cursor()
    command = "SELECT count(username) AS howmany FROM users WHERE permlevel like 3;"
    # Wait, how many admins are there?
    cur.execute(command)
    count = cur.fetchone()["howmany"]

    if count < 1:  # Only do this if no more than 0 exists.
        command = "INSERT INTO users (username, password, memo, permlevel) VALUES (%s, %s, 'Default User', 3);"
        try:
            root_password = os.environ['PIMINDER_ADMIN_PASSWORD']
        except KeyError:
            print("Missing envvar: Piminder_ADMIN_PASSWORD")
            exit(1)
        hashed_rootpw = bcrypt.hashpw(root_password.encode('utf8'), bcrypt.gensalt())
        cur.execute(command, (admin_name, hashed_rootpw))
        print("Created administrative user: %s" % admin_name)
    else:
        print("Administrative user already exists, skipping.")
    connection.commit()


def runtime():
    print("Now Creating Tables")
    mariadb = connect_to_db()
    create_tables(spec_tables, mariadb)
    create_administrative_user(mariadb)
    mariadb.commit()
    mariadb.close()
    print("Done.")
