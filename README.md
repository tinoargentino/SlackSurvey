# Slack Survey for AWS Lambda
Sends a Slack NPS Survey to a list of users

The Survey includes 10 buttons from 1 to 10 to provide a full NPS survey, and asks for additional text feedback after the score is provided.

Additionally, the Home of the Slack App provides a text input interface, so that users can provide valuable feedback at any moment

All of this data is captured, stored, and organized in the Google Spreadsheet template provided

The Script is intended to be hosted in AWS Lambda, and triggered from the spreadsheet once the contact list has been entered

Spreadsheet: https://docs.google.com/spreadsheets/d/16aptHEARz_1HCL1pJ_Rx6uW-oTBLSpOFtfIlgJrSXwI/edit?usp=sharing

The Spreadsheet includes a script that is to be set to run periodically so that it always has the latest list of Slack User IDs to match to the emails.

The Spreadsheet matches user emails to their Slack IDs in order to send them the survey

You will need to create a Slack App in order to send the actual survey's

Spreadsheet <------> AWS Lambda <------> Slack <------> Slack Users

The Spreadsheet triggers requests from the AWS Lambda via get requests, and the AWS Lambda interfaces with Slack via the API

The AWS Lambda script access the Spreadsheet via Gspread, which allows it to read (Slack User IDs) and write data (Survey responses)


# Customization
You can create your own Modals and Slack interactions here: https://app.slack.com/block-kit-builder/

You will need a creds.json to access Google Sheets service, and authorize the Google sheet with the email from your credential

The cred.json file is not included in the repository, but it must be at the same level as the lambda_function.py

Additionally, you will need a Slack API user

You will have to set up 2 environment variables in AWS Lambda console:
- SheetID (ID of your spreadsheet)
- SlackKey (your slack secret key)


# Code Details

## Menu options
 0 - Default, fallback if all else fails

 1 - Send survey to list of receivers (Valentin in payload) (Test post trigger from terminal (Valentin type))

 2 - URL Challenge from slack

 3 - Slash command: test

 4 - Button Click

 5 - Process Modal Submission

 6 - Update contact list

 7 - App Home Opened

 8 - React to App Home submission


## Message Types
 1 - Pure text

 2 - Click buttons

 3 - Modal test
