import azure.functions as func
import json
import logging
import os
import base64
from typing import Dict, Any
import requests

# Azure Function App main file
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Azure AI Foundry Configuration
AZURE_OPENAI_ENDPOINT = "https://admin-me7pqlig-swedencentral.cognitiveservices.azure.com"
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
DEPLOYMENT_NAME = "o4-mini-deploy"  # Model deployment name
API_VERSION = "2025-01-01-preview"  # API version for Azure AI Services

@app.route(route="classify", methods=["POST"])
async def classify_waste(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function endpoint for waste classification"""
    logging.info('Waste classification request received')

    try:
        # Parse request body
        req_body = req.get_json()
        
        # Extract parameters
        base64_image = req_body.get('image', '')
        user_description = req_body.get('description', '')
        
        if not base64_image and not user_description:
            return func.HttpResponse(
                json.dumps({"error": "Either image or description must be provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Prepare Azure OpenAI API call
        url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={API_VERSION}"
        
        logging.info(f'Calling Azure OpenAI at: {url}')
        
        headers = {
            "api-key": AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Build messages
        messages = []
        
        system_prompt = """You are a waste classification AI. Always output valid JSON:
        {
          "itemType": "specific item name",
          "bin": "Hazardous|Compost|Recycle|Landfill",
          "confidence": 0-100,
          "tips": "Disposal instructions",
          "certainty": "high|medium|low",
          "autoDescription": "Brief description",
          "categories": ["waste_type"],
          "reasoning": ["reasoning step"]
        }"""
        
        messages.append({"role": "system", "content": system_prompt})
        
        user_content = []
        if user_description:
            user_content.append({
                "type": "text", 
                "text": f"Classify this waste item: '{user_description}'"
            })
        
        if base64_image:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        
        messages.append({"role": "user", "content": user_content})
        
        # API request payload
        payload = {
            "messages": messages,
            "max_completion_tokens": 1000,
            "response_format": {"type": "json_object"}
        }
        
        # Make API call
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            logging.info(f'Classification successful: {user_description}')
            
            parsed_result = json.loads(content)
            parsed_result['success'] = True
            
            return func.HttpResponse(
                json.dumps(parsed_result),
                status_code=200,
                mimetype="application/json"
            )
        else:
            logging.error(f'Azure OpenAI API error: {response.status_code} - {response.text}')
            return func.HttpResponse(
                json.dumps({"error": f"AI service error: {response.status_code}"}),
                status_code=500,
                mimetype="application/json"
            )
            
    except Exception as e:
        logging.error(f'Error in waste classification: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Classification failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse("healthy", status_code=200)
