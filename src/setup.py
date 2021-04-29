from setuptools import setup

with open("../README.md", "r") as f:
      long_description = f.read()

setup(name='pyminder',
      version='0.2.0',
      description='Pyminder is a special network messanging service for status alerts.',
      long_description=long_description,
      author='Zac Adam-MacEwen',
      author_email='zadammac@kenshosec.com',
      url='https://www.github.com/zadammac/pyminder',
      packages=['pyminder_helpers', 'pyminder_monitor', 'pyminder_service'],
      install_requires=['bcrypt', 'flask', 'flask_restful', 'pymysql'],
      long_description_content_type="text/markdown"
     )
