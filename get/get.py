import logging

from flask import Flask, jsonify, request
from flask.logging import default_handler

application = Flask(__name__)  # noqa

# Set up logging
ROOT_LOGGER = logging.getLogger()
ROOT_LOGGER.setLevel(application.logger.level)
ROOT_LOGGER.addHandler(default_handler)


def root():
    return jsonify(
        status='OK',
        message='AIOPS Publisher up and running!'
    )
