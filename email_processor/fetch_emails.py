import os.path
import pickle
from datetime import datetime

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Database setup
Base = declarative_base()

# Get the current directory path
dir_path = os.path.dirname(os.path.realpath(__file__))
TOKEN_PICKLE_PATH = os.path.join(dir_path, "token.pickle")
CREDENTIALS_JSON_PATH = os.path.join(dir_path, "credentials.json")


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
    if os.path.exists(TOKEN_PICKLE_PATH):
        with open(TOKEN_PICKLE_PATH, "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refreshing token
            creds.refresh(Request())  # Refreshing creds
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_JSON_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PICKLE_PATH, "wb") as token:
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


def main():
    # Step 1: Authenticate and fetch emails
    service = authenticate_gmail()
    if service:
        email_list = fetch_emails(service)
        if email_list:
            save_emails_to_db(email_list)


if __name__ == "__main__":
    main()
