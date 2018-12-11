import os
import logging
import io
import tarfile
import tempfile
import json
import re

from flask import Flask, Blueprint, jsonify, request
from flask.logging import default_handler
from flask_restplus import Api, Resource, reqparse, fields
import requests

application = Flask(__name__)  # noqa
# blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
# api = Api(blueprint, doc='/documentation')
#
# # ns = api.namespace('version', description='current version')
# # api.add_namespace(ns)
#
# application.register_blueprint(blueprint)
#
# application.config['SWAGGER_UI_JSONEDITOR'] = True

api = Api(application, version='0.0.1', title='AIOPS Publisher API',
    description='A simple AIOPS Publisher API',
)

ns = api.namespace('publish', description='AIOPS Publisher Operations')

parser = api.parser()
parser.add_argument('id', type=str, required=True, help='The data id', location='json')
parser.add_argument('data', required=True, help='The raw analyzed data', location='json')

todo = api.model('Todo', {
    'id': fields.String(required=True, description='The data id'),
    'data': fields.Raw(required=True, description='The raw analyzed data')
})

post_parser = reqparse.RequestParser()
post_parser.add_argument('database',  type=list, help='user data', location='json')
#
# test_fields = api.model('Test', {
#   'id': fields.String(required=True, description='...', example='123'),
#   'data': Test(example="hey")
# })

# """ Model for documenting the API"""

# insert_user_data = ns.model("Insert_user_data",
#                                  {
#                                      "id":
# fields.String(attribute='123', description="ID", required=True),
#                                      "data":
# fields.Raw(attribute=[], description="Data", required=True)


upload_json = api.schema_model('UploadJSON', {
    'required': ['id', 'data'],
    'properties': {
        'id': {
            'type': 'string',
            'example': '123'
        },
        'data': {
            'type': 'array',
            'example': []
        },
        'ai_service': {
            'type': 'string',
            'example': 'generic_ai'
        }
    },
    'type': 'object'
})


# Set up logging
ROOT_LOGGER = logging.getLogger()
ROOT_LOGGER.setLevel(application.logger.level)
ROOT_LOGGER.addHandler(default_handler)

# Upload Service
# UPLOAD_SERVICE_ENDPOINT = os.environ.get('UPLOAD_SERVICE_ENDPOINT')
UPLOAD_SERVICE_ENDPOINT = 'localhost:8888/r/insights/platform/upload/api/v1/upload'

# @api.route("/version")
# class Version(Resource):
#     def get(self):
#         return jsonify(
#             status='OK',
#             message='AIOPS Publisher Version 0.0.1'
#         )

@ns.route('/')
class Publish(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    # @api.marshal_list_with(listed_todo)
    # def get(self):
    #     '''List all todos'''
    #     return [{'id': id, 'todo': todo} for id, todo in TODOS.items()]

    @ns.expect(upload_json, validate=True)
    # @api.doc(parser=parser)
    # @api.marshal_with(todo, code=200)
    # @ns.expect(post_parser)
    # @api.expect(fields=todo)
    def post(self):
        """Endpoint for upload and publish requests."""
        input_data = request.get_json(force=True)
        data_id = input_data['id']
        ai_service_id = input_data.get('ai_service', 'generic_ai')
        raw_data = input_data['data']

        try:
            temp_file_name = tempfile.NamedTemporaryFile(delete=False).name
            with tarfile.open(temp_file_name, "w:gz") as tar:
                data = io.BytesIO(json.dumps(raw_data).encode())
                info = tarfile.TarInfo(name=f'{ai_service_id}_{data_id}.json')
                info.size = len(data.getvalue())
                temp_file_name = tar.name
                tar.addfile(info, data)

        except (IOError, tarfile.TarError) as e:
            error_msg = 'Error during TAR.GZ creation: ' + str(e)
            ROOT_LOGGER.exception("Exception: %s", error_msg)
            return jsonify(
                status='Error',
                type=str(e.__class__.__name__),
                message=error_msg
            ), 500

        ai_service_id = re.sub(r'[^a-z]', r'', ai_service_id.lower())
        files = {
            'upload': (
                temp_file_name, open(temp_file_name, 'rb'),
                f'application/vnd.redhat.{ai_service_id}.aiservice+tgz'
            )
        }

        headers = {'x-rh-insights-request-id': data_id}

        # send a POST request to upload service with files and headers info
        try:
            response = requests.post(
                f'http://{UPLOAD_SERVICE_ENDPOINT}',
                files=files,
                headers=headers
            )
            response.raise_for_status()

        except (ConnectionError, requests.HTTPError, requests.Timeout) as e:
            error_msg = "Error while posting data to Upload service: " + str(e)
            ROOT_LOGGER.exception("Exception: %s", error_msg)

            # TODO Implement Retry here # noqa
            # Retry needs to examine the status_code/exact Exception type
            # before it attempts to Retry
            # a 415 error (Unsupported Media Type) for example,
            # will continue to fail even in the next attempt
            # so there is no value in pursuing a Retry for error=415
            # A Timeout error, on the other hand, is worth Retrying

            return jsonify(
                status='Error',
                type=str(e.__class__.__name__),
                status_code=response.status_code,
                message=error_msg
            ), 500

        try:
            os.remove(temp_file_name)
        except IOError as e:
            # simply log the exception in this case
            # do not return an error since this is not a critical error
            error_msg = "Error while deleting the temporary file: " + str(e)
            ROOT_LOGGER.exception("Exception: %s", error_msg)

        return jsonify(
            status='OK',
            message='Data published via Upload service'
        )



if __name__ == '__main__':
    application.run()
