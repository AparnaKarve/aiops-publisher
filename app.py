"""Main module of the server file."""

import connexion

# Create the application instance
APP = connexion.App(__name__, specification_dir="./")

# read the swagger.yml file to configure the endpoints
APP.add_api("swagger.yml")


if __name__ == "__main__":
    APP.run()
