"""
This script is a component of pycharm's back-end controller.
Specifically, it is a helper utility to be used to intialize a database for
the C2 service to operate from, provided a few basic arguments.
Author: Zac Adam-MacEwen (zadammac@kenshosec.com)
A Kensho Security Labs utility.
Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/pycharm
"""

import getpass
import os
import pymysql

__version__ = "odb-1"

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
        except pymysql.err.InternalError as error:
            if str(error.args[0]) == '1050':
                pass
            else:
                print(error)
    connection.commit()


if __name__ == "__main__":
    print("Now Creating Tables")
    mariadb = connect_to_db()
    create_tables(spec_tables, mariadb)
    mariadb.commit()
    mariadb.close()
    print("Done.")
