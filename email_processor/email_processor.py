import json
import os.path
import pickle
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.modify"]

# Database setup
Base = declarative_base()


class EmailModel(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_email = Column(String, index=True)
    subject = Column(String, index=True)
    message = Column(String)
    message_id = Column(Integer, index=True)
    received_date = Column(DateTime, index=True)


def authenticate_gmail():
    """Authenticate the user with Gmail API and return the service object."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refreshing token
            creds.refresh(Request())  # Refreshing creds
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds,
                        cache_discovery=False)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def fetch_emails(service):
    """Fetch emails from the Gmail API."""
    try:
        results = service.users().messages().list(userId="me", maxResults=10).execute()
        messages = results.get("messages", [])

        email_list = []
        for message in messages:
            msg = service.users().messages().get(
                userId="me", id=message["id"]).execute()
            email_data = {
                "from_email": next(header["value"] for header in msg["payload"]["headers"] if header["name"] == "From"),
                "subject": next(header["value"] for header in msg["payload"]["headers"] if header["name"] == "Subject"),
                "message": msg["snippet"],
                "received_date": datetime.fromtimestamp(int(msg["internalDate"]) / 1000),
                "message_id": message["id"],
            }
            email_list.append(email_data)
        return email_list
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def save_emails_to_db(email_list: list[dict]):
    """Save fetched emails to the SQLite database."""
    engine = create_engine("sqlite:///emails.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for email in email_list:
        new_email = EmailModel(
            from_email=email["from_email"],
            subject=email["subject"],
            message=email["message"],
            received_date=email["received_date"],
            message_id=email["message_id"],
        )
        session.add(new_email)

    session.commit()
    session.close()


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
                userId="me", id=email.message_id, body={"addLabelIds": [label_id]}
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
    # Step 1: Authenticate and fetch emails
    service = authenticate_gmail()
    if service:
        email_list = fetch_emails(service)
        if email_list:
            save_emails_to_db(email_list)

    # Step 2: Load rules and apply them to emails
    session = create_new_db_session()
    emails = session.query(EmailModel).all()

    rules = load_rules_from_json("rules.json")
    apply_rules_to_emails(rules, emails)


if __name__ == "__main__":
    main()
