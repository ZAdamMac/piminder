"""
This script is a component of the Pyminder's back-end controller.
It is the app-defining component of the Flask-based API system, and brings the
system up by parsing the config and feeding it back into the app framework
itself.
Author: Zac Adam-MacEwen (zadammac@kenshosec.com)
A Kensho Security Labs utility.
Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/pyminder
"""

from flask import Flask
from configparser import ConfigParser
from os import environ

__version__ = "v.0.1.2"


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
    """Parse the expected enumpiconfig.ini file and pull out all keys,
    returning them as a single object whose attributes become part of
    the app config. Ignores sections; keys must therefore be unique
    throughout the whole INI document.
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


if __name__ == "__main__":
    config = parse_config("pyminder-service.conf")
    app = create_app(config)
    app.run(host=config.LISTENIP, port=config.LISTENPORT, debug=config.DEBUG,
            ssl_context=(config.SSL_CERT, config.SSL_KEY))
