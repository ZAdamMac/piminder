"""
This script is a component of pycharm's back-end controller.
Specifically, it is a helper utility to be used to intialize a database for
the C2 service to operate from, provided a few basic arguments.
Author: Zac Adam-MacEwen (zadammac@kenshosec.com)

An Arcana Labs utility.
Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/pyminder
"""

import bcrypt
import getpass
import os
import pymysql

__version__ = "0.2.0"  # This is the version of service that we can init, NOT the version of the script itself.

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
        db_user = os.environ['PYMINDER_DB_USER']
    except KeyError:
        db_user = input("Username: ")
    root_password = None
    try:
        root_password = os.environ['PYMINDER_DB_PASSWORD']
    except KeyError:
        print("The DB password was not pasted into the environment variables.")
        root_password = getpass.getpass("Password: ")
    finally:
        conn = pymysql.connect(host='127.0.0.1', user=db_user,
                               password=root_password, db='pyminder',
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
        admin_name = os.environ['PYMINDER_ADMIN_USER']
    except KeyError:
        admin_name = input("Username: ")
    root_password = None

    cur = connection.cursor()
    command = "SELECT count(username) AS howmany FROM users WHERE username like %s;"
    cur.execute(command, admin_name)
    count = cur.fetchone()["howmany"]

    if count < 1:
        command = "INSERT INTO users (username, password, memo, permlevel) VALUES (%s, %s, 'Default User', 3);"
        try:
            root_password = os.environ['PYMINDER_ADMIN_PASSWORD']
        except KeyError:
            print("The admin password was not pasted into the environment variables.")
            root_password = getpass.getpass("Password: ")
        hashed_rootpw = bcrypt.hashpw(root_password.encode('utf8'), bcrypt.gensalt())
        cur.execute(command, (admin_name, hashed_rootpw))
        print("Created administrative user: %s" % admin_name)
    else:
        print("Administrative user already exists, skipping.")
    connection.commit()


if __name__ == "__main__":
    print("Now Creating Tables")
    mariadb = connect_to_db()
    create_tables(spec_tables, mariadb)
    create_administrative_user(mariadb)
    mariadb.commit()
    mariadb.close()
    print("Done.")
