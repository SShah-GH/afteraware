from flask import Flask, request, jsonify
import requests
import airtable
import json
import os
from twilio.rest import Client
import openai

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/aryanmahindra/Downloads/innate-summit-378204-849ac63c3e24.json'

app = Flask(__name__)

# Airtable info
AIRTABLE_API_KEY = 'keyiBU3kbqq2MMpOC'
AIRTABLE_BASE_ID = 'app8OPfKOwre37OSg'
AIRTABLE_TABLE_NAME = 'teams'

# Twilio info
account_sid = 'ACf56b45a35621d822d8ccd765eb8a34ce'
auth_token = 'a852ee16602cd2dc39eb38615deaf6f3'

# OpenAI info
openai.api_key = "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"

# Route for handling incoming messages


@app.route('/sms', methods=['POST'])
def handle_incoming_sms():
    # Get the message body and sender's phone number
    message_body = request.values.get('Body', None)
    sender_number = request.values.get('From', None)

    print(message_body)
    print(sender_number)

    airtable_client = airtable.Airtable(
        AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

    entry = airtable_client.search('Name', sender_number)
    print(entry)

    if (len(entry) is 0):
        airtable_client.insert({
            'Name': sender_number,
            'Status': message_body})
    elif 'Status' in entry[0]['fields']:
        currentStatus = entry[0]['fields']["Status"]
        currentStatus = currentStatus + message_body
        airtable_client.update(
            entry[0]['id'], {'Status': currentStatus}, typecast=True)
    else:
        airtable_client.update(
            entry[0]['id'], {'Status': message_body}, typecast=True)

    entry = airtable_client.search('Name', sender_number)

    # Set up the request headers and body
    headers = {
        "Authorization": "Bearer " + os.popen('gcloud auth application-default print-access-token').read().strip(),
        "Content-Type": "application/json"
    }

    data = {
        "nlpService": "projects/innate-summit-378204/locations/us-central1/services/nlp",
        "documentContent": entry[0]['fields']["Status"]
    }

    url = "https://healthcare.googleapis.com/v1/projects/innate-summit-378204/locations/us-central1/services/nlp:analyzeEntities"

    # Send the POST request
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Print the response
    print(response.text)

    entry = airtable_client.search('Name', sender_number)
    airtable_client.update(
        entry[0]['id'], {'StatusHealth': response.text}, typecast=True)

    prompt = "You are a nurse checking in on a patient. Write a conversation prompt to ask the patient how they are feeling."
    prompt = prompt + "Note that the patient has already told you: " + \
        entry[0]["fields"]["Status"]

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.5
    )

    print(response)

    # Send generated prompt to user
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=message_body,
        from_='+18582257875',  # Your Twilio phone number here
        to=sender_number
    )

    # Print the message SID to confirm that the message was sent
    print('Message SID:', message.sid)

    return jsonify("success")

# Route to return patient data


@app.route('/healthdata', methods=['GET'])
def return_patient_healthdata():
    patient_number = request.values.get('Number', None)

    airtable_client = airtable.Airtable(
        AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    entry = airtable_client.search('Name', patient_number)

    return jsonify(entry)

# Route to get all phone numbers


@app.route('/numbers', methods=['GET'])
def get_all_numbers():
    airtable_client = airtable.Airtable(
        AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

    numbers = set()  # use a set to store unique numbers

    for record in airtable_client.get_all():
        if 'number' in record['fields']:
            numbers.update(record['fields']['number'])

    return jsonify(list(numbers))

# Route to add a new number


@app.route('/conversation', methods=['POST'])
def start_conversation():
    patient_number = request.values.get('Number', None)
    patient_number = "+"+patient_number.strip()
    patient_number.strip()
    print(patient_number)

    airtable_client = airtable.Airtable(
        AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

    entry = airtable_client.search('Name', patient_number)
    print(entry)

    if (len(entry) is 0):
        airtable_client.insert({
            'Name': patient_number
        })

    client = Client(account_sid, auth_token)

    # Set up the message content and recipient phone number
    message_body = 'How are you feeling today?'

    # Send the message
    message = client.messages.create(
        body=message_body,
        from_='+18582257875',  # Your Twilio phone number here
        to=patient_number
    )

    # Print the message SID to confirm that the message was sent
    print('Message SID:', message.sid)

    return jsonify("success")


if __name__ == 'main':
    # Start ngrok
    ngrok_url = 'http://localhost:4040/api/tunnels'
    response = requests.get(ngrok_url)
    data = response.json()
    ngrok_tunnel = data['tunnels'][0]['public_url']
    print('ngrok tunnel:', ngrok_tunnel)

    # Set up the Twilio webhook URL
    twilio_url = ngrok_tunnel + '/sms'
    print('Twilio URL:', twilio_url)

    # Run the Flask app
    app.run(debug=True)
