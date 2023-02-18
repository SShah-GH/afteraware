
from flask import Flask, request, jsonify
import requests
import airtable
import json
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/aryanmahindra/Downloads/innate-summit-378204-849ac63c3e24.json'

app = Flask(__name__)

AIRTABLE_API_KEY = 'keyiBU3kbqq2MMpOC'
AIRTABLE_BASE_ID = 'app8OPfKOwre37OSg'
AIRTABLE_TABLE_NAME = 'teams'

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

    # Send a response message
    response = jsonify({
        'message': 'ur doc will get back to u'
    })

    return response


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
