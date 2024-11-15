import azure.functions as func
import logging
from philips_scorecard.build_scorecard import build_philips_scorecard
from philips_scorecard.remediation_list_generator import remediation_list_generator

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="func_build_philips_scorecard")
def func_build_philips_scorecard(req: func.HttpRequest) -> func.HttpResponse:
    return build_philips_scorecard(req)
    

@app.route(route="func_remediation_list_generator")
def func_remediation_list_generator(req: func.HttpRequest) -> func.HttpResponse:
    return remediation_list_generator(req)
