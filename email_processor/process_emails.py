import json
import os
from datetime import datetime, timedelta

from fetch_emails import EmailModel, authenticate_gmail
from googleapiclient.errors import HttpError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get the current directory path
dir_path = os.path.dirname(os.path.realpath(__file__))
RULES_JSON_PATH = os.path.join(dir_path, "rules.json")


def load_rules_from_json(file_path):
    """Load rules from a JSON file."""
    with open(file_path, "r") as file:
        rules = json.load(file)
    return rules


def apply_rules_to_emails(rules, emails: list[EmailModel]):
    """Apply rules to the list of emails and perform actions."""
    for rule in rules["rules"]:
        predicate = rule["predicate"]
        conditions = rule["conditions"]
        actions = rule["actions"]

        for email in emails:
            match = (
                all(check_condition(email, condition)
                    for condition in conditions)
                if predicate == "All"
                else any(check_condition(email, condition) for condition in conditions)
            )

            if match:
                perform_actions(email, actions)


def check_condition(email: EmailModel, condition: dict):
    """Check if a single condition matches the email."""
    field = condition["field"]
    predicate = condition["predicate"]
    value = condition["value"]

    email_value = getattr(email, field)

    if predicate == "contains":
        return value in email_value
    elif predicate == "does_not_contain":
        return value not in email_value
    elif predicate == "equals":
        return email_value == value
    elif predicate == "does_not_equal":
        return email_value != value
    elif predicate == "less_than" and isinstance(email_value, datetime):
        return email_value < datetime.now() - timedelta(days=int(value))
    elif predicate == "greater_than" and isinstance(email_value, datetime):
        return email_value > datetime.now() - timedelta(days=int(value))
    return False


def perform_actions(email: EmailModel, actions: list):
    """Perform actions on the email based on the rules."""
    service = authenticate_gmail()
    for action in actions:
        if action == "mark_as_read":
            mark_as_read(service, email)
        elif action == "mark_as_unread":
            mark_as_unread(service, email)
        elif isinstance(action, dict) and "move_message" in action:
            move_message(service, email, action["move_message"])


def mark_as_read(service, email: EmailModel):
    """Mark the email as read."""
    try:
        service.users().messages().modify(
            userId="me", id=email.message_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        print(f"Marked email {email.from_email} as read.")
    except HttpError as error:
        print(
            f"An error occurred while marking {email.from_email = } as read: {error}")


def mark_as_unread(service, email: EmailModel):
    """Mark the email as unread."""
    try:
        service.users().messages().modify(userId="me", id=email.message_id,
                                          body={"addLabelIds": ["UNREAD"]}).execute()
        print(f"Marked email {email.from_email} as unread.")
    except HttpError as error:
        print(f"An error occurred while marking as unread: {error}")


def move_message(service, email: EmailModel, folder: str):
    """Move the email to the specified folder."""
    try:
        # Assuming 'folder' is a label name in Gmail
        label_results = service.users().labels().list(userId="me").execute()
        labels = label_results.get("labels", [])
        label_id = next(
            (label["id"] for label in labels if label["name"] == folder), None)

        if label_id:
            service.users().messages().modify(
                userId="me", id=email.message_id, body={"addLabelIds": [label_id], "removeLabelIds": ["INBOX"]}
            ).execute()
            print(f"Moved email {email.from_email} to folder {folder}.")
        else:
            print(f"Label {folder} not found.")
    except HttpError as error:
        print(f"An error occurred while moving the message: {error}")


def create_new_db_session():
    engine = create_engine("sqlite:///emails.db")
    session_maker = sessionmaker(bind=engine)
    session = session_maker()
    return session


def main():
    # Step 2: Load rules and apply them to emails
    try:
        session = create_new_db_session()
        emails = session.query(EmailModel).all()
    except Exception as err:
        print(f"Database not found, please run fetch_emails first | {err = }")
        return

    rules = load_rules_from_json(RULES_JSON_PATH)
    apply_rules_to_emails(rules, emails)


if __name__ == "__main__":
    main()
