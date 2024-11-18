import azure.functions as func
import logging
import json
from philips_scorecard.build_scorecard import build_philips_scorecard
from philips_scorecard.remediation_list_generator import FindingsDocumentGenerator
from philips_scorecard.config.config_loader import ConfigLoader

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="func_build_philips_scorecard")
def func_build_philips_scorecard(req: func.HttpRequest) -> func.HttpResponse:
    return build_philips_scorecard(req)
    

@app.route(route="func_remediation_list_generator")
async def func_remediation_list_generator(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Parse JSON data from the request body
        json_data = req.get_json()
    except ValueError:
        return func.HttpResponse(
            "Invalid JSON",
            status_code=400
        )    

    # Check if the required keys are present in the JSON data
    if 'excel_content' not in json_data or 'output_template_content' not in json_data:
        return func.HttpResponse(
            "Missing required keys: 'excel_content' and/or 'output_template_content'",
            status_code=400
        )
    # Convert the JSON object to a JSON string
    json_request = json.dumps(json_data, indent=4)

    azureOpenAI = ConfigLoader().initialize_openai_client()

    findings_document_generator = FindingsDocumentGenerator(azureOpenAI)
    # Call the async function
    json_response = await findings_document_generator.build_docx_output_in_json_format(json_request)

    return func.HttpResponse(
        json.dumps(json_response),
        mimetype="application/json",
        status_code=200
    )