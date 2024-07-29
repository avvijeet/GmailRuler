# Email Processor

## Overview

The Email Processor project integrates with the Gmail API to fetch emails, process them based on rules defined in a JSON file, and perform actions such as marking emails as read/unread or moving them to different folders. Optionally, the project also provides a REST API for manually triggering email processing and performing actions using Flask and Swagger for API documentation. This solution consists of two standalone Python scripts: one for fetching and storing emails in a database, and another for processing these emails based on specified rules and taking actions via the Gmail REST API.

## Features

- **Email Fetching**: Automatically fetches emails from your Gmail account and stores them in a local SQLite database.
- **Email Processing**: Processes stored emails based on user-defined rules and performs actions such as marking as read, marking as unread, and moving emails to specified labels.

## Table of Contents

- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [[OPTIONAL] Running the Server](#optional-running-the-server)
- [[OPTIONAL] API Endpoints](#optional-api-endpoints)
- [Contributing](#contributing)

## Project Structure

- email_processor/
- - **init**.py - Initializes the package
- - fetch_emails.py - Script to fetch emails from Gmail and store them in a SQLite database.
- - process_emails.py - Script to process stored emails based on rules and perform actions.
- - rules.json - Configuration file for email processing rules
- - credentials.json - Google API credentials (not included in the repository)
- - token.pickle - OAuth tokens (generated automatically using credentials.json)
- - api.py - Flask application and API definitions (Optional to use)
- requirements.txt - Python package dependencies
- README.md - Project documentation

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
git clone https://github.com/avvijeet/email-processor.git
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
pip install --upgrade pip && pip install -r requirements.txt
```

### 4. Obtain Gmail API Credentials

1. Go to the Google Cloud Console.
2. Create a new project or select an existing project.
3. Enable the Gmail API for your project. Reference[https://www.geeksforgeeks.org/how-to-read-emails-from-gmail-using-gmail-api-in-python/]
4. Go to the OAuth consent screen and configure the OAuth consent screen.
5. Go to Credentials and create OAuth 2.0 credentials (Client ID).
6. Download the credentials.json file and place it in the email_processor directory.

### 5. Configure Rules

Define rules in the rules.json file. Each rule should specify the field, condition, and action to be taken. For example:

```json
{
  "rules": [
    {
      "predicate": "All",
      "conditions": [
        {
          "field": "subject",
          "predicate": "contains",
          "value": "Invoice"
        },
        {
          "field": "from_email",
          "predicate": "equals",
          "value": "vendor@example.com"
        }
      ],
      "actions": [
        "mark_as_read",
        {
          "move_message": "Invoices"
        }
      ]
    }
  ]
}
```

## Usage

### 1. Initialize the Database and Fetching Emails

Run the first script to initialize the database and fetch emails. The database schema will be created automatically.:

```bash
python fetch_emails.py
```

### 2. Processing Emails

Edit the rules.json file to define your custom processing rules, then run the following script to apply these rules to the emails:

```bash
python process_emails.py
```

## [OPTIONAL] Running the Server

### 1. Start the Flask Server

Run the Flask application to start the server:

```bash
python email_processor/api.py
```

The server will start on <http://127.0.0.1:5001> by default.

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

## [OPTIONAL] API Endpoints

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

## Contributing

Contributions to this project are welcome! Please fork the repository and submit a pull request with your enhancements.
