import os

from flasgger import Swagger, swag_from
from flask import Flask, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy

from email_processor import (
    EmailModel,
    apply_rules_to_emails,
    authenticate_gmail,
    create_new_db_session,
    fetch_emails,
    load_rules_from_json,
    mark_as_read,
    mark_as_unread,
    move_message,
    save_emails_to_db,
)

# Get the current directory path
dir_path = os.path.dirname(os.path.realpath(__file__))
RULES_JSON_PATH = os.path.join(dir_path, "rules.json")


app = Flask(__name__)
DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
app.config["DEBUG"] = DEBUG
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///emails.db"
db = SQLAlchemy(app)
api = Api(app)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/",
}

swagger = Swagger(app, config=swagger_config)


class FetchEmails(Resource):
    @swag_from({"responses": {200: {"description": "Fetched and saved emails from Gmail"}}})
    def get(self):
        service = authenticate_gmail()
        if service:
            email_list = fetch_emails(service)
            if email_list:
                save_emails_to_db(email_list)
                return {"message": "Emails fetched and saved."}
        return {"message": "Failed to fetch emails."}


class ProcessEmails(Resource):
    @swag_from({"responses": {200: {"description": "Processed emails based on rules"}}})
    def get(self):
        with app.app_context():
            db.create_all()  # Ensure tables are created
            session = create_new_db_session()
            emails = session.query(EmailModel).all()
            rules = load_rules_from_json(RULES_JSON_PATH)
            apply_rules_to_emails(rules, emails)
        return {"message": "Emails processed based on rules."}


class EmailActions(Resource):
    @swag_from(
        {
            "parameters": [
                {
                    "name": "action",
                    "in": "query",
                    "type": "string",
                    "required": True,
                    "enum": ["mark_as_read", "mark_as_unread", "move_message"],
                    "description": "The action to perform (mark_as_read, mark_as_unread, move_message)",
                },
                {
                    "name": "email_id",
                    "in": "query",
                    "type": "string",
                    "required": True,
                    "description": "The emailID of the email to perform the action on",
                },
                {
                    "name": "folder",
                    "in": "query",
                    "type": "string",
                    "required": False,
                    "description": "The folder to move the email to (required for move_message action)",
                },
            ],
            "responses": {200: {"description": "Action performed on email"}},
        }
    )
    def post(self):
        data = request.args
        action = data.get("action")
        email_id = data.get("email_id")
        folder = data.get("folder")

        service = authenticate_gmail()
        if not service:
            return {"message": "Failed to authenticate."}, 401

        with app.app_context():
            session = create_new_db_session()
            email = session.query(EmailModel).get(email_id)
            if not email:
                return {"message": "Email not found."}, 404

            if action == "mark_as_read":
                mark_as_read(service, email)
            elif action == "mark_as_unread":
                mark_as_unread(service, email)
            elif action == "move_message":
                if folder:
                    move_message(service, email, folder)
                else:
                    return {"message": "Folder name is required for move_message action."}, 400
            else:
                return {"message": "Invalid action."}, 400

            return {"message": f"Action {action} performed on email {email_id}."}


api.add_resource(FetchEmails, "/fetch_emails")
api.add_resource(ProcessEmails, "/process_emails")
api.add_resource(EmailActions, "/email_actions")

if __name__ == "__main__":
    HOST = os.getenv("HOST", "localhost")
    PORT = os.getenv("PORT", 5001)
    print(
        f"Started Server with {DEBUG = } on {HOST = } {PORT = } | Documentation at http://{HOST}:{PORT}/docs/")
    app.run(host=HOST, port=PORT, debug=DEBUG)
