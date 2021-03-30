from __future__ import print_function
from botocore.vendored import requests
from pytz import timezone
import pytz
from datetime import datetime
import urllib3
from bs4 import BeautifulSoup
import pytz
import datetime, time
import json


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Diabetes Log. " \
                    "Please tell me your operation by saying, " \
                    "Add 1.5 Rapid Insulin."

    reprompt_text = "Please tell me your operation by saying, " \
                    "Add 1.5 Rapid Insulin."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using the Diabetes Log. " \
                    "Have a nice day! "
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def create_insulin_attributes(insulinSize,insulinNotes):
    return {"insulinSize": insulinSize,
            "insulinNotes":insulinNotes}
            
def create_carb_attributes(carbs,carbNotes):
    return {"carbAmount": carbs,
            "carbNotes":carbNotes}

def set_insulin_in_session(intent, session, headers):
    """ Sets the operation in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    reprompt_text = None
    current_datetime = datetime.datetime.now(tz=pytz.utc).isoformat()
    add_url = 'https://sugarmate.io/api/v1/feed_item'

    
    if 'InsulinSize' in intent['slots']:
        print('slots',intent['slots'])
        insulin_size = intent['slots']['InsulinSize']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name']
        insulin_notes = 'API Added Data'
        if 'resolutions' in intent['slots']['InsulinType']:
            insulin_type = intent['slots']['InsulinType']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name']
        else:
            insulin_type = 'Rapid'
        if  insulin_type == 'Long':           
            print('Insulin Type: In Long')
            insulin_payload ='''feed_item={"time":"'''+current_datetime+'''","feed_item_cells":[{"temp_id":-2,"sort_order":0,"event_type":"insulin","account_insulin":{"id":12108,"account_id":7002,"insulin_id":16,"form":"Solostar (100u/ml)","name_override":"Long Acting","onset":120,"duration":1440,"peak":null,"precision":500,"is_basal":true,"is_active":true,"created_at":"2018-10-24T18:55:03.313Z","updated_at":"2018-12-24T20:02:17.033Z","secondary_precision":null,"name":"Long Acting","category":"long","description":"insulin glargine"},"account_insulin_id":12108,"amount":"'''+insulin_size+'''"}],"temp_id":-1}'''
        elif insulin_type == 'Rapid':
            print('Insulin Type: In Rapid')
            insulin_payload ='''feed_item={"time":"'''+current_datetime+'''","feed_item_cells":[{"temp_id":-2,"sort_order":0,"event_type":"insulin","account_insulin":{"id":12107,"account_id":7002,"insulin_id":5,"form":"Cartridge (100u/ml)","name_override":"Short Acting","onset":20,"duration":240,"peak":45,"precision":500,"is_basal":false,"is_active":true,"created_at":"2018-10-24T18:55:03.313Z","updated_at":"2018-12-24T20:03:17.398Z","name":"Short Acting","category":"rapid","description":"insulin aspart"},"account_insulin_id":12107,"amount":"'''+insulin_size+'''"}],"temp_id":-1}&deleted=false'''
        else:
            print('Insulin Type: In Rapid Catch')
            insulin_payload ='''feed_item={"time":"'''+current_datetime+'''","feed_item_cells":[{"temp_id":-2,"sort_order":0,"event_type":"insulin","account_insulin":{"id":12107,"account_id":7002,"insulin_id":5,"form":"Cartridge (100u/ml)","name_override":"Short Acting","onset":20,"duration":240,"peak":45,"precision":500,"is_basal":false,"is_active":true,"created_at":"2018-10-24T18:55:03.313Z","updated_at":"2018-12-24T20:03:17.398Z","name":"Short Acting","category":"rapid","description":"insulin aspart"},"account_insulin_id":12107,"amount":"'''+insulin_size+'''"}],"temp_id":-1}&deleted=false'''
        
        session_attributes = create_insulin_attributes(insulin_size,insulin_notes)

        response = requests.post(add_url,headers=headers,data=insulin_payload)
        print('--------------------')
        print(response.text)
        print('--------------------')
        speech_output = "Adding " + insulin_size +' '+ insulin_type

    else:
        speech_output = "I'm not sure what your operation is. " \
                        "Please try again."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def get_bloodsugar_in_session(intent, session, headers):
    """ Sets the operation in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    reprompt_text = None
    current_datetime = datetime.datetime.now(tz=pytz.utc).isoformat()
    get_url = 'https://sugarmate.io/api/v1/reading'

    response = requests.get(get_url,headers=headers)
    print('--------------------')
    print(response.text)
    print('--------------------')
    response_json = json.loads(response.text)
    trend = response_json['reading']['trend_words']
    if trend == 'FORTY_FIVE_DOWN':
        trend = 'Slight Down'
    if trend == 'FORTY_FIVE_UP':
        trend = 'Slight Up'
    blood_sugar_level = str(response_json['reading']['value'])
    delta = str(response_json['reading']['delta'])
    previous_blood_sugar_level = int(blood_sugar_level)-int(delta)
    
    print(blood_sugar_level,trend,delta,previous_blood_sugar_level)
    speech_output = 'Liam''s blood sugar is ' + blood_sugar_level + ' ' + delta + ' Trending ' + trend + '. Previous reading was '+ str(previous_blood_sugar_level)

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def set_carbs_in_session(intent, session, headers):
    """ Sets the operation in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    reprompt_text = None
    current_datetime = datetime.datetime.now(tz=pytz.utc).isoformat()
    add_url = 'https://sugarmate.io/api/v1/feed_item'

    amount = '25'
    print('------INTENT------')
    print(intent)
    print('------INTENT------')
    print('------SESSION------')
    print(session)
    print('------SESSION------')
    carb_notes = 'API Added Data'
    
    payload ='''feed_item={"time":"'''+current_datetime+'''","feed_item_cells":[{"temp_id":-2,"sort_order":0,"event_type":"insulin","account_insulin":{"id":12107,"account_id":7002,"insulin_id":5,"form":"Cartridge (100u/ml)","name_override":"Short Acting","onset":20,"duration":240,"peak":45,"precision":500,"is_basal":false,"is_active":true,"created_at":"2018-10-24T18:55:03.313Z","updated_at":"2018-12-24T20:03:17.398Z","name":"Short Acting","category":"rapid","description":"insulin aspart"},"account_insulin_id":12107,"amount":"'''+amount+'''"}],"temp_id":-1}&deleted=false'''
    
    
    session_attributes = create_carb_attributes(amount,carb_notes)

    response = requests.post(add_url,headers=headers,data=payload)
    print('--------------------')
    print(response.text)
    print('--------------------')
    speech_output = "Adding " + amount + " Carbs"

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    print('--------------------')
    print(intent_request)
    print('--------------------')
        
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    
    value_url = 'https://sugarmate.io/sign_in'
    login_url = 'https://sugarmate.io/sessions'
    home_url = 'https://sugarmate.io/home'
    readings_url = 'https://sugarmate.io/api/v1/readings?limit=1'
    add_url = 'https://sugarmate.io/api/v1/feed_item'
    username = ''
    password = ''
    urllib3.disable_warnings()
    
    session = requests.Session()
    source_code = session.get(value_url, timeout=5, verify=False)
    soup = BeautifulSoup(source_code.text, 'html.parser')
    authenticity_token_value = soup.find("input", {"name":"authenticity_token"})['value']
    payload = {'authenticity_token': authenticity_token_value, 'session[email]': username, 'session[password]': password}
    r = requests.post(login_url,data=payload)
    remember_token_value = r.headers['Set-Cookie'].split(' ')[0].split('=')[1].split(';')[0]
    headers = {
    'Host': 'sugarmate.io',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
    'Cookie': 'remember_token='+remember_token_value}

    # Dispatch to your skill's intent handlers
    if intent_name == "Insulin":
        return set_insulin_in_session(intent, session, headers)
    if intent_name == "Carbohydrates":
        return set_carbs_in_session(intent, session, headers)
    if intent_name == "BloodSugar":
        return get_bloodsugar_in_session(intent, session, headers)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])