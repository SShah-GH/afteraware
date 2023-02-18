import requests
import json
import os

os.system('export GOOGLE_APPLICATION_CREDENTIALS="/Users/satvashah/Downloads/innate-summit-378204-849ac63c3e24.json"')

# Set up the request headers and body
headers = {
    "Authorization": "Bearer " + os.popen('gcloud auth application-default print-access-token').read().strip(),
    "Content-Type": "application/json"
}

data = {
    "nlpService": "projects/innate-summit-378204/locations/us-central1/services/nlp",
    "documentContent": "Insulin regimen human 5 units IV administered."
}

url = "https://healthcare.googleapis.com/v1/projects/innate-summit-378204/locations/us-central1/services/nlp:analyzeEntities"

# Send the POST request
response = requests.post(url, headers=headers, data=json.dumps(data))

# Print the response
print(response.text)
