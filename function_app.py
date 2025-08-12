import azure.functions as func
import json
import logging
import os
import requests

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

AZURE_OPENAI_ENDPOINT = "https://admin-me7pqlig-swedencentral.cognitiveservices.azure.com"
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
DEPLOYMENT_NAME = "o4-mini-deploy"
API_VERSION = "2025-01-01-preview"

@app.route(route="classify", methods=["POST"])
def classify_waste(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Waste classification request received')
    
    try:
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON"}),
                status_code=400,
                mimetype="application/json"
            )
        
        user_description = req_body.get('description', '')
        if not user_description:
            return func.HttpResponse(
                json.dumps({"error": "Description required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={API_VERSION}"
        headers = {
            "api-key": AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a waste classifier. Output JSON: {\"itemType\": \"item name\", \"bin\": \"Recycle|Compost|Landfill|Hazardous\", \"confidence\": 85, \"tips\": \"disposal instructions\", \"certainty\": \"high\", \"categories\": [\"category\"], \"reasoning\": [\"reason\"]}"
                },
                {
                    "role": "user", 
                    "content": f"Classify this waste item: {user_description}"
                }
            ],
            "max_completion_tokens": 500,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            content = json.loads(result['choices'][0]['message']['content'])
            content['success'] = True
            return func.HttpResponse(
                json.dumps(content),
                status_code=200,
                mimetype="application/json"
            )
        else:
            logging.error(f'API error: {response.status_code}')
            return func.HttpResponse(
                json.dumps({"error": f"AI service error: {response.status_code}"}),
                status_code=500,
                mimetype="application/json"
            )
            
    except Exception as e:
        logging.error(f'Error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("healthy", status_code=200)
