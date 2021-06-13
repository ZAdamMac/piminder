from setuptools import setup

with open("../README.md", "r") as f:
      long_description = f.read()

setup(name='piminder',
      version='1.0.5',
      description='Piminder is a special network messanging service for status alerts.',
      long_description=long_description,
      author='Zac Adam-MacEwen',
      author_email='zadammac@kenshosec.com',
      url='https://www.github.com/zadammac/Piminder',
      packages=['piminder_helpers', 'piminder_monitor', 'piminder_service'],
      install_requires=['bcrypt', 'flask', 'flask_restful', 'pymysql'],
      long_description_content_type="text/markdown"
     )
