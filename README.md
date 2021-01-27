# SlackSurvey
Sends a Slack Survey to a list of users
The user list comes from the provided G-Sheet and the results are also dumped there

Spreadsheet:https://docs.google.com/spreadsheets/d/16aptHEARz_1HCL1pJ_Rx6uW-oTBLSpOFtfIlgJrSXwI/edit?usp=sharing

The Spreadsheet includes a script that is to be set to run periodically so that it always has the latest list of Slack User IDs to match to the emails.

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
