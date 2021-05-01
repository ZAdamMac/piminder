"""
This script is a component of Piminder's back-end controller.
This resource is a collection of helper classes which are imported selectively
into other resources that make up part of Piminder, to commonize handling tasks.

Author: Zac Adam-MacEwen (zadammac@kenshosec.com)
An Arcana Labs utility.

Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/Enumpi-C2
"""

import base64
import bcrypt


def authenticated_exec(token_id, permission, connection, func, body):
    """
    Accepts the noted arguments to determine if a given user may take an action
    and then allows them to execute it.

    For this to work the function in question should accept the json body and
    the database connection as its only arguments and in that order.

    :param token_id: the value returned by token_validate[0].
    :param permission: The integer representing the minimum permission level (1-3) needed to achieve this task.
    :param connection: a database connection object.
    :param func: the function to be executed if the client is permitted
    :param body: the json body of the request.
    :return: the response body to be sent to the remote user.
    """
    cur = connection.cursor()
    cmd = "SELECT * FROM users WHERE username=%s"
    cur.execute(cmd, token_id)
    d_user = cur.fetchone()
    user_permission_level = d_user["permlevel"]

    if user_permission_level >= permission:  # This is a highly simplistic check, but it works.
        response = func(body, connection)
        connection.commit()
        connection.close()
    else:
        response = {'error': 400, 'msg': "Unauthorized"}
        connection.close()

    return response


def basic_auth(token, db_connect):
    """A simplistic function to handle breaking a basic auth token into the requisite connections and testing them
    against the database in a simplistic way. returns true or false depending on validtity, along with a username

    :param token: the value from the authorization header
    :param db_connect: a pymysql database connection.
    :return:
    """

    list_token_components = token.split(" ")  # never assume a sane input
    token_type = list_token_components[0]     # Authorization headers standard would expect this
    token_value = list_token_components[1]    # In basic, this will be the actual token.
    token_decoded = base64.b64decode(token_value).decode('utf8')
    token_decoded = token_decoded.split(":")
    if token_type.lower() == "basic":  # Secondary sanity check; this should probably be filtered off somewhere else
        username = token_decoded[0]
        password = token_decoded[1].encode('utf8')

        command = "SELECT password FROM users WHERE username=%s"
        cur = db_connect.cursor()
        cur.execute(command, username)
        dict_stored_password = cur.fetchone()
        if dict_stored_password:  # We need a sanity check in case the user doesn't exist.
            stored_password = dict_stored_password["password"].encode('utf8')
        else:
            return False, username

        if bcrypt.checkpw(password, stored_password):
            return True, username
        else:
            return False, username
    else:  # In this case, we're looking at a token type we don't know how to handle with this function.
        return False, "invalid_authtype"


def json_validate(test_json, dict_schema):
    """A simplistic JSON validator for pre-clearing missing or incorrectly-
    typed arguments in a request body. Controlled by arguments and returns
    a tuple in (boolean, errors) format indicating whether or not the body
    passed and what, if any, errors are indicated.

    :param test_json: A deserialized JSON object (usually a dict)
    :param dict_schema: a dictionary of the object schema with key-value pairs
    where value should be of the same type as the expected type in the JSON.
    :return: tuple of boolean and an error dictionary.
    """
    list_response = []
    testable = {0: (test_json, dict_schema)}
    counter = 0
    for thing in testable:
        test_object, active_schema = testable[thing]
        for field in active_schema:
            try:
                value = test_json[field]
            except KeyError:
                list_response.append({str(field): "Field missing from request"})
                continue
            expect_type = dict_schema[field]
            if not isinstance(value, type(expect_type)):
                # We use type(expect_type) here because sometimes the value is a dict or list
                # rather than being a type object
                list_response.append({str(field): ("Value is not of the expected type: %s" % type(expect_type))})
                continue
            if expect_type == dict:
                counter += 1
                testable.update({counter: (value, dict_schema[field])})
        if len(list_response) == 0:
            return True, list_response
        else:
            dict_response = {}
            for error in list_response:
                dict_response.update(error)
            return False, dict_response