# Copyright (c) 2020 - Valentin Schmidt
# valentinsch@gmail.com
# https://github.com/tinoargentino/

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import os
from slack import WebClient
from slack.errors import SlackApiError
import base64
from urllib.parse import parse_qs
from urllib.parse import unquote
import time as tm

import requests

from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import gspread

def lambda_handler(event, context):
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scopes=scope)

    servercode=200
    servermessage='Standard OK reply'
    challenge=''

    SlackKey = os.environ.get('SlackKey')
    client = WebClient(token=SlackKey)
    SheetID = os.environ.get('SheetID')

    print(event)

    menuoption=0
    eventbody= False

    if 'body' in event:
      eventbody=event['body']
      if event['isBase64Encoded']== True:
        event_dec=parse_qs(base64.b64decode(eventbody).decode('utf-8'))
        #if event_dec[:5]=='token':
        if 'token' in event_dec:
          #this is a slash command
          body_dic=event_dec
          menuoption=3
        else:
          # menuoption=4
          body_dic=json.loads(event_dec['payload'][0])
          if 'type' in body_dic:
              if body_dic['type']=="block_actions":
                  if body_dic['container']['type']=='message':
                    menuoption=4
                  elif body_dic['container']['type']=='view':
                    menuoption=8
              elif body_dic['type']=="view_submission":
                  menuoption=5
      else:
        body_dic=json.loads(event['body'])
      #With body in readable format, check for last options before going to menu
      if 'type' in body_dic:
        if body_dic['type']=='valentin':
          menuoption=1
        elif body_dic['type']=='url_verification':
          menuoption=2
        elif body_dic['type']=='contacts':
          menuoption=6
        elif body_dic['type']=='event_callback':
          menuoption=7

    #Default
    if menuoption==0:
        messagebody='No body in POST bro, or it\'s not a json who knows'
        messagetype=1

    #Send survey to list of receivers (Valentin in payload)
    elif menuoption==1:
        messagetype=2
        messagebody=body_dic['event']
        #Get list of receivers in Sheet
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(SheetID)

        ReceiverListSheet=sh.worksheet("Receiver List")
        Receivers = ReceiverListSheet.get_all_values()

        Hash=str(hash(str(tm.time())+messagebody))
        ts=tm.ctime()
        #Write Hash of event name in Google Sheet to keep track of responses
        HashSheet=sh.worksheet("[Backend] Hash List")
        HashSheet.append_row([Hash,body_dic['event'],len(Receivers[1:]),ts,tm.time()])

        #Write list of receipients to historic
        Receiver_list=list(map(lambda u: [u[0],u[1],u[2],u[3],Hash,body_dic['event']], Receivers[1:]))
        HistoricRecipientSheet=sh.worksheet("[Backend] Historic Recipient List")
        HistoricRecipientSheet.append_rows(Receiver_list)


        #Send survey to each user
        for receiver in Receivers[1:]:
            if receiver[2]!='' and receiver[2]!='Not Found':
                try:
                    response = client.chat_postMessage(channel=receiver[2],blocks=generate_message(messagebody,messagetype,Hash))
                except Exception as e:
                    pass

    #Slack challenge
    elif menuoption==2:
        messagebody='Trying to answer the challenge bro'
        messagetype=1
        challenge=body_dic['challenge']
    #Slash
    elif menuoption==3:
        messagebody='cool slash command bro'
        messagetype=1
        slashchannel=event_dec["user_id"][0]
        response = client.chat_postMessage(channel=slashchannel,blocks=generate_message(messagebody,messagetype,''))

    #Click button interaction
    elif menuoption==4:
        # change original message
        url = body_dic['response_url']
        data = {"replace_original": "true","text": "Thanks a lot!"}
        headers = {'Content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(data), headers=headers)

        #Get Values from response
        id=body_dic['user']['id']
        username=body_dic['user']['username']
        name=body_dic['user']['name']
        time=body_dic['actions'][0]['action_ts']
        selection=body_dic['actions'][0]['value']
        Hash=selection[selection.find('-')+1:]

        #Send Modal
        client.views_open(trigger_id=body_dic["trigger_id"],view=generate_message(username,3,Hash))

        # Write answer to spreadsheet
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(SheetID)
        Responses=sh.worksheet("[Backend] Responses")

        messagetype=1

        row = [id, username, name, time, selection]
        Responses.append_row(row)

    #Process Modal
    elif menuoption==5:
        block_id=body_dic['view']['blocks'][0]['block_id']
        resp=body_dic['view']['state']['values'][block_id]['plain_text_input-action']['value']
        name=body_dic['user']['name']
        userid=body_dic['user']['id']
        print(body_dic)

        #[Backend] Feedback Responses
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(SheetID)
        Responses=sh.worksheet("[Backend] Feedback Responses")
        row = [block_id,userid, name, resp]
        Responses.append_row(row)

    #Update Slack contact list
    elif menuoption==6:
        users = []
        for page in client.users_list(limit=1000):
            users = users + page['members']
        user_list=list(map(lambda u: [u["id"],u["profile"].get("email","na"),u["name"],u.get("real_name","na"),u['deleted']], users))

        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(SheetID)
        ContactSheet=sh.worksheet("[Backend] Contact List")
        ContactSheet.update('A2:E',user_list)

    #App Home Open
    elif menuoption==7:
        userID=body_dic['event']['user']
        client.views_publish(user_id=userID,view=generate_message('',4,''))

    #React to App Home submission
    elif menuoption==8:
        userid=body_dic['user']['id']
        client.views_publish(user_id=userid,view=generate_message('',5,''))
        resp=body_dic['view']['state']['values'][list(body_dic['view']['state']['values'].keys())[0]]['plain_text_input-action']['value']
        name=body_dic['user']['name']
        ts=body_dic['actions'][0]['action_ts']
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(SheetID)
        Responses=sh.worksheet("[Backend] General Feedback")
        row = [userid, name, resp,ts]
        Responses.append_row(row)

    #Send test response to Slack
    returnobject={
        "statusCode": 200,
        #'body': servermessage
        "headers": {
            "Content-Type": "application/json"
        },
        "body": "",
        "response_action": "clear",
        "challenge":challenge
    }
    return returnobject



def generate_message(messagebody,messagetype,Hash):
    if messagetype==1:
        blocks=[
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": messagebody
              }
          },
        ]
    if messagetype==2:
        blocks=[
            {
              "type": "section",
              "text": {
                "type": "plain_text",
                "text": "Thank you for attending today's " + messagebody + "! How likely are you to recommend this content to your colleagues?",
                "emoji": True
              }
            },
            {
              "type": "actions",
              "elements": [
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "10",
                        "emoji": True
                      },
                      "value": "10-"+Hash
                    },
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "9",
                        "emoji": True
                      },
                      "value": "9-"+Hash
                    },
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "8",
                        "emoji": True
                      },
                      "value": "8-"+Hash
                    },
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "7",
                        "emoji": True
                      },
                      "value": "7-"+Hash
                    },
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "6",
                        "emoji": True
                      },
                      "value": "6-"+Hash
                    },
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "5",
                        "emoji": True
                      },
                      "value": "5-"+Hash
                    },
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "4",
                        "emoji": True
                      },
                      "value": "4-"+Hash
                    },
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "3",
                        "emoji": True
                      },
                      "value": "3-"+Hash
                    },
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "2",
                        "emoji": True
                      },
                      "value": "2-"+Hash
                    },
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "1",
                        "emoji": True
                      },
                      "value": "1-"+Hash
                    }
                ]
            }
        ]
    if messagetype==3:
      blocks={
    	"title": {
    		"type": "plain_text",
    		"text": "Additional Feedback",
    		"emoji": True
    	},
    	"submit": {
    		"type": "plain_text",
    		"text": "Send",
    		"emoji": True
    	},
    	"type": "modal",
    	"blocks": [
    		{
                "block_id": Hash,
                "optional":True,
    			"hint": {
    				"type": "plain_text",
    				"text": "Try suggesting what content you would like to see more of",
    				"emoji": True
	             },
                "type": "input",
    			"element": {
    				"type": "plain_text_input",
    				"multiline": True,
    				"action_id": "plain_text_input-action"
    			},
    			"label": {
    				"type": "plain_text",
    				"text": "Any additional feedback you would like to submit?",
    				"emoji": True
    			}
    		}
       ]
    }
    if messagetype==4:
        blocks={
        	"type": "home",
        	"blocks": [
        		{
        			"type": "header",
        			"text": {
        				"type": "plain_text",
        				"text": "Suggestion Box",
        				"emoji": True
        			}
        		},
        		{
        			"hint": {
        				"type": "plain_text",
        				"text": "Eg: insert examples here",
        				"emoji": True
        			},
        			"type": "input",
        			"element": {
        				"type": "plain_text_input",
        				"multiline": True,
        				"action_id": "plain_text_input-action"
        			},
        			"label": {
        				"type": "plain_text",
        				"text": "What can we do better?",
        				"emoji": True
        			}
        		},
        		{
        			"type": "actions",
        			"elements": [
        				{
        					"type": "button",
        					"text": {
        						"type": "plain_text",
        						"text": "Submit",
        						"emoji": True
        					},
        					"value": "submitted",
        					"action_id": "submit"
        				}
        			]
        		}
        	]
        }

    if messagetype==5:
        blocks={
        	"type": "home",
        	"blocks": [
        		{
        			"type": "header",
        			"text": {
        				"type": "plain_text",
        				"text": "Thank you!",
        				"emoji": True
        			}
        		},
        		{
        			"type": "section",
        			"text": {
        				"type": "plain_text",
        				"text": "Your feedback helps us improve the quality of the content we provide you.",
        				"emoji": True
        			}
        		}
        	]
        }
    return blocks
