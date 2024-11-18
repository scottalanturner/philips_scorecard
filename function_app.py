import inspect
import logging
import json
import azure.functions as func
from philips_scorecard.build_scorecard import ScorecardGenerator
from philips_scorecard.remediation_list_generator import FindingsDocumentGenerator
from philips_scorecard.config.config_loader import ConfigLoader


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="func_build_philips_scorecard")
def func_build_philips_scorecard(req: func.HttpRequest) -> func.HttpResponse:
    """Process HTTP request to build Philips scorecard from provided JSON data.

    Args:
        req (func.HttpRequest): The HTTP request containing JSON data.

    Returns:
        func.HttpResponse: JSON response with scorecard data or error message.
    """
    logging.info('%s processed a request.', inspect.currentframe().f_code.co_name)

    try:
        # Parse JSON data from the request body
        json_data = req.get_json()
    except ValueError:
        return func.HttpResponse(
            "Invalid JSON",
            status_code=400
        )    

    # Check if the required keys are present in the JSON data
    if 'form_row_id' not in json_data or 'document_content' not in json_data:
        return func.HttpResponse(
            "Missing required keys: 'form_row_id' and/or 'document_content'",
            status_code=400
        )
    # Convert the JSON object to a JSON string
    json_request = json.dumps(json_data, indent=4)

    json_response = ScorecardGenerator().build_scorecard(json_request)

    return func.HttpResponse(
        json.dumps(json_response),
        mimetype="application/json",
        status_code=200
    )
    

@app.route(route="func_remediation_list_generator")
async def func_remediation_list_generator(req: func.HttpRequest) -> func.HttpResponse:
    """Process HTTP request to generate remediation list from provided Excel and template data.

    Args:
        req (func.HttpRequest): The HTTP request containing JSON data.

    Returns:
        func.HttpResponse: JSON response with generated document data or error message.
    """
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

    azure_openai = ConfigLoader().initialize_openai_client()

    findings_document_generator = FindingsDocumentGenerator(azure_openai)
    # Call the async function
    json_response = await findings_document_generator.build_docx_output_in_json_format(json_request)

    return func.HttpResponse(
        json.dumps(json_response),
        mimetype="application/json",
        status_code=200
    )