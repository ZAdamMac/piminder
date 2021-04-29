"""
This script is a component of pyminder's back-end controller.
This resource handles the registration, deletion, and modification of users and relies on an authorization
confirmation method from utilities.py.

Author: Zac Adam-MacEwen (zadammac@kenshosec.com)
An Arcana Labs utility.

Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/pyminder
"""

import bcrypt
from flask_restful import Resource
from flask import current_app, request, make_response
import pymysql
from .utilities import authenticated_exec, basic_auth, json_validate

__version__ = "prototype"


class UsersAPI(Resource):
    def get(self):
        """An authenticated user with reporting permissions may retrieve a
        full listing of all commands logged by the server set up on the server.

        :return: In the valid case, a json dictionary of (row, action) pairs
        """
        cookie = request.headers.get("Authorization")
        try:
            connection = pymysql.connect(host=current_app.config["DBHOST"],
                                         user=current_app.config["USERNAME"],
                                         password=current_app.config["PASSPHRASE"],
                                         db='pyminder',
                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error'}, 500
        except pymysql.Error:
            return {'message': 'Internal Server Error'}, 500
        proceed, user = basic_auth(cookie, connection)
        if proceed:  # A chicken ain't nothing but a bird.
            dict_return = authenticated_exec(user, 3, connection, users_get, "")
            resp = make_response(dict_return)
            resp.status_code = dict_return["error"]
            resp.content_type = "application/json"
            return resp
        else:
            return {'message': 'unauthorized'}, 401

    def post(self):
        """The post method allows the listing of a new message in the database.

        :return:
        """
        cookie = request.headers.get("Authorization")
        try:
            connection = pymysql.connect(host=current_app.config["DBHOST"],
                                         user=current_app.config["USERNAME"],
                                         password=current_app.config["PASSPHRASE"],
                                         db='pyminder',
                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error, Key error'}, 500
        except pymysql.Error as e:
            return {'message': 'Internal Server Error, sql error'}, 501
        proceed, user = basic_auth(cookie, connection)
        if proceed:  # A chicken ain't nothing but a bird.
            dict_return = authenticated_exec(user, 3, connection, users_post, request.get_json())
            resp = make_response(dict_return)
            resp.status_code = dict_return["error"]
            resp.content_type = "application/json"
            return resp
        else:
            return {'message': 'unauthorized'}, 401

    def patch(self):
        """This will mark a specified message as read. The message is not wholly discarded immediately, but will be
        garbage-collected by a cron job run against the DB itself.

        :return:
        """
        cookie = request.headers.get("Authorization")
        try:
            connection = pymysql.connect(host=current_app.config["DBHOST"],
                                         user=current_app.config["USERNAME"],
                                         password=current_app.config["PASSPHRASE"],
                                         db='pyminder',

                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error'}, 500
        except pymysql.Error:
            return {'message': 'Internal Server Error'}, 500
        proceed, user = basic_auth(cookie, connection)
        if proceed:  # A chicken ain't nothing but a bird.
            dict_return = authenticated_exec(user, 3, connection, users_patch, request.get_json())
            resp = make_response(dict_return)
            resp.status_code = dict_return["error"]
            resp.content_type = "application/json"
            return resp
        else:
            return {'message': 'unauthorized'}, 401

    def delete(self):
        """This removes a selected message from the DB entirely.

        :return:
        """
        cookie = request.headers.get("Authorization")
        try:
            connection = pymysql.connect(host=current_app.config["DBHOST"],
                                         user=current_app.config["USERNAME"],
                                         password=current_app.config["PASSPHRASE"],
                                         db='pyminder',

                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error'}, 500
        except pymysql.Error:
            return {'message': 'Internal Server Error'}, 500
        proceed, user = basic_auth(cookie, connection)
        if proceed:  # A chicken ain't nothing but a bird.
            dict_return = authenticated_exec(user, 3, connection, users_delete, request.get_json())
            resp = make_response(dict_return)
            resp.status_code = dict_return["error"]
            resp.content_type = "application/json"
            return resp
        else:
            return {'message': 'unauthorized'}, 401

# Here follow the actual actions!


def users_get(discard, connection):
    """A stored join function that gets all the currently registered users, along with permission level"""
    del discard
    cur = connection.cursor()

    # Unwieldy command handles most of the data processing in SQL which is faster than doing this in python.

    cmd = "SELECT username, memo, permlevel FROM users ORDER BY username asc;"  # we don't want the passwords!
    cur.execute(cmd)
    messages = cur.fetchall()
    response = {}
    counter = -1
    for message in messages:
        output_keys = {"username": "username", "memo": "memo", "permlevel": "permissionLevel"}
        counter += 1
        this_message = {}
        for key in output_keys.keys():
            this_message.update({output_keys[key]: message[key]})
        response.update({str(counter): this_message})
    response.update({"error": 200})

    return response


def users_post(body, connection):
    """A very simplistic function that adds a fresh user to the users table."""
    cur = connection.cursor()
    dict_schema = {"username": "", "permissionLevel": "", "memo": "", "password": ""}
    json_valid, errors = json_validate(body, dict_schema)
    dict_levels = {"service": 1, "monitor": 2, "admin": 3}  # This dictionary defines all available levels. TODO DOC
    if body["permissionLevel"] not in dict_levels.keys():
        json_valid = False
        errors.update({"errorlevel": "Error level not one of service, monitor, or admin."})
    else:
        body["permlevel"] = dict_levels[body["permissionLevel"]]  # Replace friendly string with level integer

    password = body["password"].encode('utf8')  # Bcrypt operates on byte arrays, not strings
    stored_password = bcrypt.hashpw(password, bcrypt.gensalt())  # I prefer my hash as salty as practical
    body["password"] = stored_password.decode('utf8')  # And then we drop it back to a string to run.

    if json_valid:
        d_message = {}
        d_message.update(body)
        cmd = "INSERT INTO users " \
              "(username, password, memo, permlevel) " \
              "VALUES (%(username)s, %(password)s, %(memo)s, %(permlevel)s);"
        cur.execute(cmd, d_message)
        response = {"error": 200, "message": ("User %s created successfully." % d_message["username"])}
        connection.commit()
    else:
        response = {"all_errors": errors, "error": 400}

    return response


def users_patch(body, connection):
    """This function updates an existing user and should only be callable by an admin. Mostly used to change PW"""
    cur = connection.cursor()
    dict_schema = {"username": "", "permissionLevel": "", "memo": "", "password": ""}
    json_valid, errors = json_validate(body, dict_schema)
    dict_levels = {"service": 1, "monitor": 2, "admin": 3}  # This dictionary defines all available levels.
    if body["permissionLevel"] not in dict_levels.keys():
        json_valid = False
        errors.update({"errorlevel": "Error level not one of service, monitor, or admin."})
    else:
        body["permissionLevel"] = dict_levels[body["permissionLevel"]]  # Replace friendly string with level integer

    password = body["password"].encode('utf8')  # Bcrypt operates on byte arrays, not strings
    stored_password = bcrypt.hashpw(password, bcrypt.gensalt())  # I prefer my hash as salty as practical
    body["password"] = stored_password.decode('utf8')  # And then we drop it back to a string to run.

    if json_valid:
        d_message = {}
        d_message.update(body)
        cmd = "UPDATE users " \
              "SET password=%(password)s, memo=%(memo)s, permlevel=%(permissionLevel)s " \
              "WHERE username like %(username)s;"
        cur.execute(cmd, d_message)
        response = {"error": 200, "message": ("User %s updated successfully." % d_message["username"])}
        connection.commit()
    else:
        response = {"all_errors": errors, "error": 400}

    return response


def users_delete(body, connection):
    """This function removes the selected user's permissions to do anything while leaving them in the DB."""
    cur = connection.cursor()
    dict_schema = {"username": ""}
    json_valid, errors = json_validate(body, dict_schema)

    if json_valid:
        # First, make sure this hasn't already been executed.
        cmd = "SELECT username FROM users WHERE username like %(username)s;"
        cur.execute(cmd, body)
        response = cur.fetchone()
        # Gotta be a better way to do the following line, but...
        try:
            if response:
                cmd = "UPDATE users SET permlevel=0 WHERE username like %(username)s;"
                cur.execute(cmd, body)
                response = {"error": 200}
                connection.commit()
            else:
                response = {"error": 400, "message": "Could not deactivate user"}
        except KeyError:
            response = {"error": 400, "message": "The indicated user does not exist"}
    else:
        response = {"all_errors": errors, "error": 400}

    return response

