"""Main module of the server file."""

import connexion

# Create the application instance
options = {"swagger_ui": False}
application = connexion.App(__name__, specification_dir="./", options=options)   #noqa

# read the swagger.yml file to configure the endpoints
application.add_api("swagger.yml")


if __name__ == "__main__":
    application.run()
