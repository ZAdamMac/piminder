"""
This script is a component of the Piminder's back-end controller.
It is the app-defining component of the Flask-based API system, and brings the
system up by parsing the config and feeding it back into the app framework
itself.
Author: Zac Adam-MacEwen (zadammac@kenshosec.com)

An Arcana Labs utility.
Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/Piminder
"""

from flask import Flask
from configparser import ConfigParser
from os import environ
from resources.db_autoinit import runtime as db_autoinit

__version__ = "v.1.0.0"  # This is the most recent version of the service that this script can initialize.

env_mapping = {  # This dictionary maps environment variable keys to the expected names from the old config file format
    "PIMINDER_HOST": "LISTENHOST",
    "PIMINDER_PORT": "LISTENPORT",
    "PIMINDER_DEBUG": "DEBUG",
    "PIMINDER_DB_HOST": "DBHOST",
    "PIMINDER_DB_PASSWORD": "PASSPHRASE",
    "PIMINDER_DB_USER": "USERNAME",
    "USE_SSL": "USE_SSL",
    "SSL_CERT": "SSL_CERT",
    "SSL_KEY": "SSL_KEY",
}

defaults = {  # Specifies default values for all configuration values in case for some reason they are absent.
    "LISTENHOST": "LOCALHOST",
    "LISTENPORT": 80,
    "DEBUG": False,
    "DBHOST": "localhost",
    "USERNAME": "Piminder",
    "PASSPHRASE": None,  # This will probably cause a crash but it's the sane default.
    "USE_SSL": False,
    "SSL_CERT": "cert.pem",
    "SSL_KEY": "key.pem"
}

def create_app(config_object):
    """Taken from an example by Onwuka Gideon
    :param config_object: Expects the return of parse_config()
    :return:
    """

    app = Flask(__name__)
    app.config.from_object(config_object)

    from app import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app


def parse_config(path):
    """Parse the necessary values out of the .conf and pull out all keys,
    returning them as a single object whose attributes become part of
    the app config. This will be overridden by any envvars present.
    :param path: a path (ideally absolute) to an INI config file.
    :return: an object suitable for passing to create_app.
    """
    class Conf(object):
        pass
    conf = Conf()

    parser = ConfigParser()
    parser.read(path)
    vars_config = {}
    for section in parser.sections():
        for option in parser.options(section):
            value = parser.get(section, option)
            vars_config.update({option: value})

    for key in vars_config:
        setattr(conf, str(key).upper(), vars_config[key])

    return conf


def parse_env(configBlock):  # This appears not to work, step through
    global env_mapping
    for key in env_mapping.keys(): # For each element in the mapping
        if key in environ.keys(): # If that element's envvar exists in the envvars
            setattr(configBlock, env_mapping[key], environ[key]) # override it in the config

    return configBlock


def enforce_defaults(conf):  # This currently appears to superenforce. Why?
    global defaults
    extant = conf.__dir__()
    for key in defaults:
        if key not in extant:
            setattr(conf, key, defaults[key])

    if str(conf.USE_SSL.lower()) in ['yes', 'y', 'true', '1']:
        conf.USE_SSL = True
    else:
        conf.USE_SSL = False

    if str(conf.DEBUG.lower()) in ['yes', 'y', 'true', '1']:
        conf.DEBUG = True
    else:
        conf.DEBUG = False

    return conf

if __name__ == "__main__":
    db_autoinit()
    config = parse_config("piminder-service.conf")
    config = parse_env(config)
    config = enforce_defaults(config)
    app = create_app(config)
    if config.USE_SSL:
        app.run(host=config.LISTENHOST, port=config.LISTENPORT, debug=config.DEBUG,
            ssl_context=(config.SSL_CERT, config.SSL_KEY))
    else:
        app.run(host=config.LISTENHOST, port=config.LISTENPORT, debug=config.DEBUG)
