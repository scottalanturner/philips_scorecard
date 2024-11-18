from openai import AzureOpenAI
import pandas as pd
import azure.functions as func
from docx import Document
from io import BytesIO
import json
from typing import List, Dict
from philips_scorecard.config.config_loader import ConfigLoader
from philips_scorecard.templates.philips import get_findings_and_recommendations_table, get_findings_and_recommendations_row
from philips_scorecard.utils.doc_converters import get_document, convert_doc_to_base64, convert_base64_to_excel_sheets
from philips_scorecard.utils.insert_html_to_docx import convert_html_to_docx_elements, replace_placeholders_in_docx
import warnings
import logging

warnings.filterwarnings('ignore', message='Data Validation extension is not supported and will be removed', category=UserWarning)

class FindingsDocumentGenerator:
    def __init__(self, openai_client: AzureOpenAI):
        self.openai_client = openai_client
        
    def clean_excel_data(self, sheets: dict) -> pd.DataFrame:
        """Clean and filter Excel data to remove empty rows."""
        df_all = pd.DataFrame()

        for sheet_name, df in sheets.items():
            if 'Finding Details' in df.columns:
                df_failures = df[df['Finding Details'].str.len() > 10]
                df_failures.loc[:, 'Floor'] = sheet_name
                df_all = pd.concat([df_all, df_failures], ignore_index=True)

        return df_all
    
    async def generate_finding_description(self, findings: pd.DataFrame) -> str:
        findings_summary = findings['Failure'].value_counts().to_dict()
        
        prompt = f"""
        Analyze these network findings and identify technical patterns:
        {findings_summary}

        Provide a short technical analysis focusing on:
        1. Most common issue types
        2. Potential root causes
        3. One specific recommendation for system improvement

        Keep response under 100 words, use technical language.
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a CWNE wireless network engineer performing a site survey of a hospital."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        
        return response.choices[0].message.content

    def create_output_html_table(self, df: pd.DataFrame) -> str:
        table_html = get_findings_and_recommendations_table(col_width='50', col_width2='50')
        floor_names = df['Floor'].unique()

        for floor in floor_names:
            findings = df[df['Floor'] == floor]['Finding Details']
            remediations = df[df['Floor'] == floor]['Remediation Detail']

            findings_list = f'{floor}<ul>'
            for finding in findings:
                findings_list += f'<li>{finding}</li>'
            findings_list += '</ul>'

            remediation_list = f'{floor}<ul>'
            for remediation in remediations:
                remediation_list += f'<li>{remediation}</li>'
            remediation_list += '</ul>'

            table_html += get_findings_and_recommendations_row(findings_list, remediation_list)

        table_html += '</table>'
        return table_html
    
    async def generate_findings_report(self, df_remediations: pd.DataFrame) -> str:
        analysis = await self.generate_finding_description(df_remediations)
        return analysis

    async def build_docx_output_in_json_format(self, json_data: str) -> str:
        json_dict = json.loads(json_data)
        docx_output_template_content_base64 = json_dict['output_template_content']
        
        excel_input_content_base64 = json_dict['excel_content']
        excel_sheets = convert_base64_to_excel_sheets(excel_input_content_base64)
        
        df_remediations = self.clean_excel_data(excel_sheets)
        remediation_html_table = self.create_output_html_table(df_remediations)
        llm_analysis = await self.generate_findings_report(df_remediations)

        document = get_document(docx_output_template_content_base64)

        html_sections = {
            'remediation_table': remediation_html_table,
            # wrap in <p> tags so html to docx conversion will work
            'remediation_ai_report': f'<p>{llm_analysis}</p>'
        }
        replace_placeholders_in_docx(document, html_sections)

        new_content = convert_doc_to_base64(document)

        response_data = {
            "new_document_content": new_content
        }
        
        return json.dumps(response_data)

    async def process_request(self, req: func.HttpRequest) -> func.HttpResponse:
        logging.info('Python HTTP trigger function processed a request.')

        try:
            json_data = req.get_json()
        except ValueError:
            return func.HttpResponse(
                "Invalid JSON",
                status_code=400
            )    

        if 'excel_content' not in json_data or 'output_template_content' not in json_data:
            return func.HttpResponse(
                "Missing required keys: 'excel_content' and/or 'output_template_content'",
                status_code=400
            )

        json_request = json.dumps(json_data, indent=4)
        json_response = await self.build_docx_output_in_json_format(json_request)

        return func.HttpResponse(
            json_response,
            mimetype="application/json",
            status_code=200
        )