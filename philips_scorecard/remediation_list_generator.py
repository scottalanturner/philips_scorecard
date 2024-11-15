from openai import AzureOpenAI
import pandas as pd
from docx import Document
from typing import List, Dict
from philips_scorecard.config.config_loader import ConfigLoader
from philips_scorecard.templates.philips import get_findings_and_recommendations_table, get_findings_and_recommendations_row
from philips_scorecard.utils.insert_html_to_docx import convert_html_to_docx_elements
import warnings
warnings.filterwarnings('ignore', message='Data Validation extension is not supported and will be removed', category=UserWarning)

# Rest of your imports and code follows...
class FindingsDocumentGenerator:
    def __init__(self, openai_client: AzureOpenAI):
        self.openai_client = openai_client
        
    def clean_excel_data(self, excel_file_path: str) -> pd.DataFrame:
        """Clean and filter Excel data to remove empty rows."""

        sheets = pd.read_excel(excel_file_path, sheet_name=None)
        # Iterate over each sheet
        df_all = pd.DataFrame()

        # **Be aware in the original Excel file every sheet has hidden cells. So watch out for what is selected, because it could pick up
        # caculated fields that aren't shown. It will also pick up other sheets which don't match the Floor sheets.
        for sheet_name, df in sheets.items():
            if 'Finding Details' in df.columns:
                # Fill NaN values in Floor column (to handle merged cells)
               # Filter rows where the length of 'Finding Details' is greater than 10
                df_failures = df[df['Finding Details'].str.len() > 10]
                df_failures.loc[:, 'Floor'] = sheet_name
                # Concatenate the filtered DataFrame to the main DataFrame
                df_all = pd.concat([df_all, df_failures], ignore_index=True)

        return df_all
    
    async def generate_finding_description(self, findings: pd.DataFrame) -> str:
        # Group findings by type
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




    def create_document(self, df: pd.DataFrame, analysis: str) -> Document:
        doc = Document()
        
        # Create table with 2 columns
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        
        # Add header row
        header_cells = table.rows[0].cells
        header_cells[0].text = 'Finding'
        header_cells[1].text = 'Remediation'

        floor_names = df['Floor'].unique()

        for floor in floor_names:
            #df_floor = df[df['Floor'] == floor]
            findings = df[df['Floor'] == floor]['Finding Details']
            remediations = df[df['Floor'] == floor]['Remediation Detail']
            new_row = table.add_row().cells

            findings_text = new_row[0].paragraphs[0]
            findings_text.add_run(floor + '\n\n')
            remediation_text = new_row[1].paragraphs[0]
            remediation_text.add_run(floor + '\n\n')

            for finding in findings:
                findings_text.add_run('• ' + finding + '\n')

            for remediation in remediations:
                remediation_text.add_run('• ' + remediation + '\n')    

        # Add data rows
      #  for _, row in df.iterrows():
     #       floor = df['Floor']
        #    data_row = table.add_row().cells
        #    data_row[0].text = f"F{row['Finding Details']}"
        #    data_row[1].text = f"{row['Remediation Detail']}"
            # Add findings with bullets
    #        findings_row = table.add_row().cells
   #         findings_text = findings_row[0].paragraphs[0]
  #          for finding in df[df['Floor'] == floor]['Finding Details']:
 #               findings_text.add_run('• ' + finding + '\n')
           
            # Add remediations with bullets
 #           remediation_text = findings_row[1].paragraphs[0]
#            for remediation in df[df['Floor'] == floor]['Remediation Detail']:
#                remediation_text.add_run('• ' + remediation + '\n')


        # Add AI analysis section
        doc.add_heading('Technical Analysis', level=1)
        doc.add_paragraph(analysis)
        
        return doc


    def create_output_html_table(self, df: pd.DataFrame, analysis: str) -> str:

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
    
async def generate_findings_report(excel_file_path: str, output_doc_path: str) -> str:
    # Initialize config loader
    config_loader = ConfigLoader()

    # Load API configuration
    api_config = config_loader.load_api_config()

    # Initialize OpenAI client
    openai_client = AzureOpenAI(
        api_key=api_config.api_key,
        api_version=api_config.api_version,
        azure_endpoint=api_config.azure_endpoint
    )
    
    # Initialize generator
    generator = FindingsDocumentGenerator(openai_client)

    # Load Excel file
    df_remediations = generator.clean_excel_data(excel_file_path)
    # Analyze findings and generate commentary
    analysis = await generator.generate_finding_description(df_remediations)
    #analysis = ''

    html = generator.create_output_html_table(df_remediations, analysis)

    # Convert HTML to docx elements
    doc = Document()
    elements = convert_html_to_docx_elements(doc, html)

    # Add table to document
    doc._element.body.append(elements[0]._element)

    # Add AI analysis section
    doc.add_heading('Technical Analysis', level=1)
    doc.add_paragraph(analysis)

    # Generate document
    #doc = generator.create_document(df_remediations, analysis)
    
    # Save document
    doc.save(output_doc_path)
    
    return output_doc_path

# Example of generated content:
"""
Finding: RSSI and SNR below threshold

A signal strength and signal-to-noise ratio issue was identified across multiple patient rooms in the facility. The finding affects five patient rooms (200 through 204), all showing RSSI and SNR measurements below acceptable thresholds. To remediate this issue, new access points (AP-01 through AP-05) will be installed in each affected room to improve wireless coverage and signal quality. This enhancement will ensure reliable wireless connectivity for medical devices and patient care systems in these areas.

Affected Locations:
• in patient room 200
• in patient room 201
• in patient room 202
• in patient room 203
• in patient room 204

Remediation Steps:
• Add NEW Access Point AP-01in patient room 200
• Add NEW Access Point AP-02in patient room 201
• Add NEW Access Point AP-03in patient room 202
• Add NEW Access Point AP-04in patient room 203
• Add NEW Access Point AP-05in patient room 204
"""