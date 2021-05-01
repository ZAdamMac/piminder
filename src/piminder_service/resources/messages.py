"""
This script is a component of Piminder's back-end controller.
This resource handles the registration of messages and handling existing messages through various restful methods.

Author: Zac Adam-MacEwen (zadammac@kenshosec.com)
An Arcana Labs utility.

Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/Enumpi-C2
"""

import datetime
from flask_restful import Resource
from flask import current_app, request, make_response
import pymysql
import uuid
from .utilities import authenticated_exec, basic_auth, json_validate

__version__ = "0.2.0"


class MessageAPI(Resource):
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
                                         db='Piminder',
                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error'}, 500
        except pymysql.Error:
            return {'message': 'Internal Server Error'}, 500
        proceed, user = basic_auth(cookie, connection)
        if proceed:  # A chicken ain't nothing but a bird.
            dict_return = authenticated_exec(user, 2, connection, messages_get, "")
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
                                         db='Piminder',
                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error, Key error'}, 500
        except pymysql.Error as e:
            return {'message': 'Internal Server Error, sql error'}, 501
        proceed, user = basic_auth(cookie, connection)
        if proceed:  # A chicken ain't nothing but a bird.
            dict_return = authenticated_exec(user, 1, connection, messages_post, request.get_json())
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
                                         db='Piminder',

                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error'}, 500
        except pymysql.Error:
            return {'message': 'Internal Server Error'}, 500
        proceed, user = basic_auth(cookie, connection)
        if proceed:  # A chicken ain't nothing but a bird.
            dict_return = authenticated_exec(user, 2, connection, messages_patch, request.get_json())
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
                                         db='Piminder',

                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error'}, 500
        except pymysql.Error:
            return {'message': 'Internal Server Error'}, 500
        proceed, user = basic_auth(cookie, connection)
        if proceed:  # A chicken ain't nothing but a bird.
            dict_return = authenticated_exec(user, 2, connection, messages_delete, request.get_json())
            resp = make_response(dict_return)
            resp.status_code = dict_return["error"]
            resp.content_type = "application/json"
            return resp
        else:
            return {'message': 'unauthorized'}, 401

# Here follow the actual actions!


def messages_get(body, connection):
    """A stored join function that gets all the currently registered commands,
    their relevant metadata, the name of the client they are associated with
    and the message, if any. This is returned to the requestor in a JSON
    format for further processing."""
    cur = connection.cursor()
    del body
    # Unwieldy command handles most of the data processing in SQL which is faster than doing this in python.

    cmd = "SELECT * FROM messages ORDER BY time_raised desc;"
    cur.execute(cmd)
    messages = cur.fetchall()
    response = {}
    counter = -1
    for message in messages:
        output_keys = {"id": "messageId", "name": "name", "read_flag": "read", "errorlevel": "errorLevel",
                       "time_raised": "timestamp", "message": "message"}
        counter += 1
        this_message = {}
        for key in output_keys.keys():
            this_message.update({output_keys[key]: message[key]})
        if this_message["read"] == b'\x00':
            this_message.update({"read": False})
        else:
            this_message.update({"read": True})
        time_out = this_message["timestamp"].strftime("%Y-%m-%dT%H:%M:%SZ")  # It is nice to have ISO 8601 compliance
        this_message.update({"timestamp": time_out})
        response.update({str(counter): this_message})
    response.update({"error": 200})

    return response


def messages_post(body, connection):
    """A very simplistic function that adds a fresh command to the commands table."""
    cur = connection.cursor()
    dict_schema = {"name": "", "timestamp": "", "errorlevel": "", "message": ""}
    json_valid, errors = json_validate(body, dict_schema)
    if body["errorlevel"] not in ["info", "minor", "major"]:
        json_valid = False
        errors.update({"errorlevel": "Error level not one of info, minor, or major."})

    if json_valid:
        d_message = {}
        d_message.update(body)
        d_message.update({"id": str(uuid.uuid4())})
        d_message.update({"read": False})
        d_message.update({"timestamp": datetime.datetime.strptime(body["timestamp"], "%Y-%m-%dT%H:%M:%SZ").timestamp()})
        cmd = "INSERT INTO messages " \
              "(id, name, time_raised, errorlevel, message, read_flag) " \
              "VALUES (%(id)s, %(name)s, FROM_UNIXTIME(%(timestamp)s), %(errorlevel)s, " \
              "%(message)s, %(read)s)"
        cur.execute(cmd, d_message)
        response = {"error": 200}
        connection.commit()
    else:
        response = {"all_errors": errors, "error": 400}

    return response


def messages_patch(body, connection):
    """This function indicates in the DB that a message has been read.
    A stored procedure or cron job will garbage collect."""
    cur = connection.cursor()
    dict_schema = {"messageId": ""}
    json_valid, errors = json_validate(body, dict_schema)

    if json_valid:
        # First, make sure this hasn't already been executed.
        cmd = "SELECT id, read_flag " \
              "FROM messages " \
              "WHERE id=%s"
        cur.execute(cmd, body["messageId"])
        response = cur.fetchone()
        print(response)
        # Gotta be a better way to do the following line, but...
        try:
            if response["read_flag"] == b'\x00':
                cmd = "UPDATE messages " \
                      "SET read_flag=TRUE " \
                      "WHERE id=%s"
                cur.execute(cmd, body["messageId"])
                response = {"error": 200}
                connection.commit()
            else:
                response = {"error": 400, "message": "Could not delete command - already acknowledged."}
        except KeyError:
            response = {"error": 400, "message": "The indicated ID does not exist in the messages table."}
    else:
        response = {"all_errors": errors, "error": 400}

    return response


def messages_patch(body, connection):
    """This function indicates in the DB that a message has been read.
    A stored procedure or cron job will garbage collect."""
    cur = connection.cursor()
    dict_schema = {"messageId": ""}
    json_valid, errors = json_validate(body, dict_schema)

    if json_valid:
        # First, make sure this hasn't already been executed.
        cmd = "SELECT id, read_flag FROM messages WHERE id=%s"
        cur.execute(cmd, body["messageId"])
        response = cur.fetchone()
        # Gotta be a better way to do the following line, but...
        try:
            if response["read_flag"] == b'\x00':
                cmd = "UPDATE messages " \
                      "SET read_flag=TRUE " \
                      "WHERE id=%s"
                cur.execute(cmd, body["messageId"])
                response = {"error": 200}
                connection.commit()
            else:
                response = {"error": 400, "message": "Could not mark message as read; already read."}
        except KeyError:
            response = {"error": 400, "message": "The indicated ID does not exist in the messages table."}
    else:
        response = {"all_errors": errors, "error": 400}

    return response


def messages_delete(body, connection):
    """This function removes the selected entity from database prior to garbage collection."""
    cur = connection.cursor()
    dict_schema = {"messageId": ""}
    json_valid, errors = json_validate(body, dict_schema)

    if json_valid:
        # First, make sure this hasn't already been executed.
        cmd = "SELECT id FROM messages WHERE id=%s"
        cur.execute(cmd, body["messageId"])
        response = cur.fetchone()
        # Gotta be a better way to do the following line, but...
        try:
            if response:
                cmd = "DELETE FROM messages WHERE id=%s"
                cur.execute(cmd, body["messageId"])
                response = {"error": 200}
                connection.commit()
            else:
                response = {"error": 400, "message": "Could not delete message, already deleted?"}
        except KeyError:
            response = {"error": 400, "message": "The indicated ID does not exist in the messages table."}
    else:
        response = {"all_errors": errors, "error": 400}

    return response

