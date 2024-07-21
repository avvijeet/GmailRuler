# Email Processor

## Overview

The Email Processor project integrates with the Gmail API to fetch emails, process them based on rules defined in a JSON file, and perform actions such as marking emails as read/unread or moving them to different folders. The project also provides a REST API for manually triggering email processing and performing actions using Flask and Swagger for API documentation.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the Server](#running-the-server)
- [API Endpoints](#api-endpoints)
- [Swagger Documentation](#swagger-documentation)
- [Project Structure](#project-structure)
- [License](#license)

## Prerequisites

Before setting up the project, ensure you have the following installed:

- Python 3.7 or later
- `pip` (Python package installer)
- A Google Cloud project with Gmail API enabled
- Required Python packages

## Setup

### 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/yourusername/email-processor.git
cd email-processor
```

### 2. Create and Activate a Virtual Environment
Create a virtual environment to isolate project dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies
Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Obtain Gmail API Credentials
1. Go to the Google Cloud Console.
2. Create a new project or select an existing project.
3. Enable the Gmail API for your project.
4. Go to the OAuth consent screen and configure the OAuth consent screen.
5. Go to Credentials and create OAuth 2.0 credentials (Client ID).
6. Download the credentials.json file and place it in the email_processor directory.

### 5. Initialize the Database
The database schema will be created automatically when you run the Flask server for the first time, but you can also create the database manually:

```bash
python email_processor/api.py create_db
```

### 6. Configure Rules
Create a rules.json file in the email_processor directory with the desired rules for processing emails. Refer to the Rules Example section for a format example.


## Running the Server
### 1. Start the Flask Server
Run the Flask application to start the server:

```bash
python email_processor/api.py
```
The server will start on http://127.0.0.1:5001 by default.

### 2. Fetch Emails
Trigger the fetching of emails from Gmail and save them to the database:

```bash
curl http://127.0.0.1:5001/fetch_emails
```
### 3. Process Emails
Apply the rules from the rules.json file to the emails in the database:

```bash
curl http://127.0.0.1:5001/process_emails
```
### 4. Perform Actions
Perform actions on a specific email by specifying the action and email ID:

```bash
curl -X POST http://127.0.0.1:5001/email_actions -H "Content-Type: application/json" -d '{"action": "mark_as_read", "email_id": 1}'
```
For moving an email to a specific folder:

```bash
curl -X POST http://127.0.0.1:5001/email_actions -H "Content-Type: application/json" -d '{"action": "move_message", "email_id": 1, "folder": 
"Important"}'
```

## API Endpoints
### /fetch_emails (GET)
Fetches emails from Gmail and saves them to the database.

### /process_emails (GET)
Processes the emails in the database based on the rules defined in rules.json.

### /email_actions (POST)
Performs actions on an email. Requires action and email_id parameters, with an optional folder parameter for moving messages.

## Swagger Documentation
Swagger-UI provides an interactive interface for exploring the API documentation. Access it at:

```
http://127.0.0.1:5001/docs/
```

## Project Structure
- email_processor/
- - __init__.py - Initializes the package
- - api.py - Flask application and API definitions
- - email_processor.py - Core functionality for interacting with Gmail and processing emails
- - rules.json - Configuration file for email processing rules
- - credentials.json - Google API credentials (not included in the repository)
- - token.pickle - OAuth tokens (generated automatically)
- requirements.txt - Python package dependencies
- README.md - Project documentation
