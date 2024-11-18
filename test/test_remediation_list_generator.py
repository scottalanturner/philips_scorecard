import asyncio
import sys
import os
import json
import base64
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from philips_scorecard.remediation_list_generator import *
from philips_scorecard.utils.doc_converters import word_to_base64, excel_to_base64
from philips_scorecard.config.config_loader import ConfigLoader

async def test_remediation_list_generator():
    '''
    Test the remediation list generator
    1. Load the word doc template file. This would be passed in as base64 in json
    2. Load the excel file. This would be passed in as base64 in json
    3. Consolidate the results from the excel file (just pulling data, no manipulation)
    4. Call LLM to create it's report
    5. Replace placeholders in word doc with the table and llm report
    6. Save the word doc to a file (for local test)
    '''

    # Build the full path to the file
    input_template_name = 'philips_scorecard/io/remediation_template.docx'
    remediation_excel_filename = 'philips_scorecard/io/remediation_list_sample2.xlsx'
    remediation_output_filename = 'philips_scorecard/io/remediation_list_output.docx'

    document_content_base64 = word_to_base64(input_template_name)
    excel_content_base64 = excel_to_base64(remediation_excel_filename)

    # Create the JSON object
    json_data = {
        "excel_content": excel_content_base64,
        "output_template_content": document_content_base64
    }     
    # Convert the JSON object to a JSON string
    json_request = json.dumps(json_data, indent=4)

    azureOpenAI = ConfigLoader().initialize_openai_client()

    findings_document_generator = FindingsDocumentGenerator(azureOpenAI)
    # Call the async function
    json_response = await findings_document_generator.build_docx_output_in_json_format(json_request)

    # Parse the JSON response
    response_data = json.loads(json_response)

    # Extract the 'content' field which is base64 encoded
    document_content_modified_base64 = response_data['new_document_content']

    # Decode the base64 content to get the binary data
    document_content_modified = base64.b64decode(document_content_modified_base64)

    # Save the modified document to a new file. This is done locally for testing to verify the .docx is correct
    with open(remediation_output_filename, "wb") as new_file:
        new_file.write(document_content_modified)

    print(f"Document saved to {remediation_output_filename}")


if __name__ == '__main__':
    asyncio.run(test_remediation_list_generator())