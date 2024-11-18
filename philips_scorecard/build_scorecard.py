import json
import pandas as pd
import logging
import azure.functions as func
from philips_scorecard.utils.doc_converters import convert_doc_to_base64
from philips_scorecard.utils.doc_converters import get_document
from philips_scorecard.templates import philips
from philips_scorecard.config.config_loader import ConfigLoader
from philips_scorecard.database.azure_client import AzureClientMSSQL
from philips_scorecard.utils.insert_html_to_docx import replace_placeholders_in_docx


def load_rules_data():
    """
    Loads rules data from the database into a pandas DataFrame.
    Uses Azure SQL connection and expects a table named 'philips_rules'.
    
    Returns:
        pd.DataFrame: DataFrame containing rules with columns matching the Excel structure
        
    Raises:
        Exception: If database connection or query fails
    """
    try:
        # Load configuration
        config_loader = ConfigLoader()
        db_config = config_loader.load_database_config()
        
        # Initialize Azure client
        azure_client = AzureClientMSSQL(
            server=db_config.server, 
            database=db_config.database, 
            username=db_config.username,
            password=db_config.password
        )
        
        # Load data
        rules_df = azure_client.load_table_to_dataframe("philips_rules")
        
        # Ensure rule_id is lowercase for consistent matching
        rules_df['rule_id'] = rules_df['rule_id'].str.lower()
        
        # Sort by rule_no to maintain consistent order
        rules_df = rules_df.sort_values('rule_no')
        
        return rules_df
        
    except Exception as e:
        # Log the error (assuming you have a logging setup)
        #logger.error(f"Error loading rules data: {str(e)}")
        raise Exception(f"Failed to load rules data: {str(e)}")

def load_form_data(form_row_id:int) -> pd.DataFrame:
    """
    Loads form submission from db into a pandas DataFrame.
    Uses Azure SQL connection and expects a table named 'philips_form_submission'.
    
    Returns:
        pd.DataFrame: DataFrame containing rules with columns matching the Excel structure
        
    Raises:
        Exception: If database connection or query fails
    """
    try:
        # Load configuration
        config_loader = ConfigLoader()
        db_config = config_loader.load_database_config()
        
        # Initialize Azure client
        azure_client = AzureClientMSSQL(
            server=db_config.server, 
            database=db_config.database, 
            username=db_config.username,
            password=db_config.password
        )
        
        # Load data
        form_df = azure_client.load_table_to_dataframe(table_name="philips_form_submission",
                                                        custom_query=f"SELECT * FROM dbo.philips_form_submission WHERE id = {form_row_id}")
        
        return form_df
        
    except Exception as e:
        # Log the error (assuming you have a logging setup)
        #logger.error(f"Error loading form data: {str(e)}")
        raise Exception(f"Failed to load form data: {str(e)}")


def process_form_data(form_data_df, rules_df):
    """
    Process form data against rules and generate results.
    
    Args:
        form_data_df (pd.DataFrame): DataFrame containing form responses
        rules_df (pd.DataFrame): DataFrame containing rules from database
        
    Returns:
        list: List of dictionaries containing processed results
    """
    results = []
    
    for _, rule in rules_df.iterrows():
        rule_id = rule['rule_id']  # Already lowercase from load_rules_data
        
        # Skip if rule_id is not in form data
        if rule_id not in form_data_df.columns:
            continue
            
        # Get the answer and normalize to lowercase string
        answer = form_data_df[rule_id].iloc[0]  # Get first row's value
        answer_lower = str(answer).lower()
            
        # Get the justification field for this rule
        justification_key = f"{rule_id}_justified"
        has_justification = (justification_key in form_data_df.columns and 
                           str(form_data_df[justification_key].iloc[0]).lower() == 'yes')

        # Determine if requirement is met using correct logic structure
        if answer_lower == 'yes':
            # For YES answers, first check justification
            if justification_key in form_data_df.columns:
                # If justification column exists, pass only if justified
                meets_requirements = has_justification
            else:
                # If no justification column, use the rule's on_yes value
                meets_requirements = rule['on_yes'] == 'PASS'
                
        elif answer_lower == 'no':
            # NO answers are simple pass/fail based on rule, no justification considered
            meets_requirements = rule['on_no'] == 'PASS'
            
        else:  # handle n/a or any other answers
            meets_requirements = True

        # Convert boolean to 'Yes'/'No' string
        meets_requirements_str = 'Yes' if meets_requirements else 'No'

        result = {
            'id': rule['rule_id'],
            'category': rule['bp_section'],
            'message': rule['question'],
            'answer': answer,
            'meets_requirements': meets_requirements_str,
            'findings': rule['finding'],
            'recommendations': rule['recommendation'],
            'question_category': rule['question_category']
        }
        
        results.append(result)
    
    return results

def build_report_sections2(results):
    """
    Build report sections based on processed results.
    """
    sections = {}
    
    # Group results by category (bp_section in the rules table, such as bp1, bp2, etc.)
    for category in set(result['category'] for result in results):
        category_results = [r for r in results if r['category'] == category]
        
        # Start with table template
        html_content_requirement_results = philips.get_table_template()
        html_content_findings_table = philips.get_findings_and_recommendations_table()
        
        # Add rows for each result
        for result in category_results:
            bg_color = philips.GREEN if result['meets_requirements'] == 'Yes' else philips.RED
            html_content_requirement_results += philips.get_row_template(bg_color, result)

            # Recommendations are only shown if the requirements do not pass
            if result['meets_requirements'] != 'Yes':
                html_content_findings_table += philips.get_findings_and_recommendations_row(result['findings'], 
                                                                                        result['recommendations']
                                                                                        )
            
        html_content_requirement_results += "</table>"
        html_content_findings_table += "</table>"
        
        # Store in sections dictionary
        sections[category] = html_content_requirement_results

        # Add progress bar
        total_results = len(category_results)
        passing_results = sum(1 for r in category_results if r['meets_requirements'] == 'Yes')
        html_content_progress_bar = philips.get_progress_bar_table(passing_results, total_results)
        placeholder_pbar = f"{category}_progressbar"
        sections[placeholder_pbar] = html_content_progress_bar

        placeholder_findings = f"{category}_findings"
        # if there are any failing results, add findings and recommendations table
        if (passing_results != total_results):
            sections[placeholder_findings] = html_content_findings_table
        else:
            sections[placeholder_findings] = ""

    return sections


def get_philips_sections(results):
    """
    Build report sections based on processed results.
    """
    sections = {}
    
    # Group results by category (bp_section in the rules table, such as bp1, bp2, etc.)
    category = 'bp_philips'
    category_results = [r for r in results if r['category'] == category]
    
    # Start with table template
    html_content_requirement_results = philips.get_table_template()
    html_content_findings_table = philips.get_findings_and_recommendations_table()
    
    # Add rows for each result
    for result in category_results:
        bg_color = philips.GREEN if result['meets_requirements'] == 'Yes' else philips.RED
        html_content_requirement_results += philips.get_row_template(bg_color, result)

        # Recommendations are only shown if the requirements do not pass
        if result['meets_requirements'] != 'Yes':
            html_content_findings_table += philips.get_findings_and_recommendations_row(result['findings'], 
                                                                                    result['recommendations']
                                                                                    )
            
    html_content_requirement_results += "</table>"
    html_content_findings_table += "</table>"
    
    # Store in sections dictionary
    sections[category] = html_content_requirement_results

    # Add progress bar
    total_results = len(category_results)
    passing_results = sum(1 for r in category_results if r['meets_requirements'] == 'Yes')

    placeholder_findings = f"{category}_findings"
    # if there are any failing results, add findings and recommendations table
    if (passing_results != total_results):
        sections[placeholder_findings] = html_content_findings_table
    else:
        sections[placeholder_findings] = ""

    return sections

def get_bp_sections(results):
    """
    Build report sections based on processed results.
    """
    sections = {}

    # global table for last page
    html_content_findings_table = philips.get_findings_and_recommendations_table()
    # Extract unique categories from results
    categories = set(result['category'] for result in results)

    for category in categories:
        if category == 'bp_philips':
            continue
        
        # section table for every category/best practice
        html_content_requirement_results = philips.get_table_template()
        group_results = [result for result in results if result['category'] == category]

        for result in group_results:
            bg_color = philips.GREEN if result['meets_requirements'] == 'Yes' else philips.RED
            html_content_requirement_results += philips.get_row_template(bg_color, result)

            # Recommendations are only shown if the requirements do not pass
            if result['meets_requirements'] != 'Yes':
                html_content_findings_table += philips.get_findings_and_recommendations_row(result['findings'], 
                                                                                        result['recommendations']
                                                                                        )
            
        html_content_requirement_results += "</table>"
        # Store in sections dictionary
        sections[category] = html_content_requirement_results

        # Add progress bar
        total_results = len(group_results)
        passing_results = sum(1 for r in group_results if r['meets_requirements'] == 'Yes')
        html_content_progress_bar = philips.get_progress_bar_table(passing_results, total_results)
        placeholder_pbar = f"{category}_progressbar"
        sections[placeholder_pbar] = html_content_progress_bar    
    
    html_content_findings_table += "</table>"

    # *** Currently if there are no findings, the table would just have the header

    sections['bp_combined_findings'] = html_content_findings_table

    return sections

# Replace placeholders in the document
def build_scorecard(json_data: str) -> str:
    # Parse the JSON string into a dictionary
    json_dict = json.loads(json_data)
    document_content_base64 = json_dict['document_content']

    # Creating a Document object from the base64 content
    document = get_document(document_content_base64)

    # New version takes a record identifier for th form data that was inserted into
    # a sql table, and we will load that record from the database
    form_row_id = json_dict['form_row_id']

    form_df = load_form_data(int(form_row_id))

    # Load rules
    rules_df = load_rules_data()
    # Process form data against rules
    results = process_form_data(form_df, rules_df)
    # Get the HTML tables that will be used in the template
    html_sections = {
        **get_philips_sections(results),
        **get_bp_sections(results)
    }
    replace_placeholders_in_docx(document, html_sections)

    new_content = convert_doc_to_base64(document)

    # Create a JSON object with the new content
    response_data = {
        "new_document_content": new_content
    }
    
    # Convert the JSON object to a JSON string
    response_json = json.dumps(response_data)
    
    return response_json


def build_philips_scorecard(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

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

    json_response = build_scorecard(json_request)

    return func.HttpResponse(
        json.dumps(json_response),
        mimetype="application/json",
        status_code=200
    )