import json
import logging
import pandas as pd
from philips_scorecard.utils.doc_converters import convert_doc_to_base64
from philips_scorecard.utils.doc_converters import get_document
from philips_scorecard.templates import philips
from philips_scorecard.config.config_loader import ConfigLoader
from philips_scorecard.database.azure_client import AzureClientMSSQL
from philips_scorecard.utils.insert_html_to_docx import replace_placeholders_in_docx


class ScorecardGenerator:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.db_config = self.config_loader.load_database_config()
        self.azure_client = AzureClientMSSQL(
            server=self.db_config.server, 
            database=self.db_config.database, 
            username=self.db_config.username,
            password=self.db_config.password
        )

    def load_rules_data(self):
        """Load rules data from the database into a pandas DataFrame."""
        try:
            rules_df = self.azure_client.load_table_to_dataframe("philips_rules")
            rules_df['rule_id'] = rules_df['rule_id'].str.lower()
            return rules_df.sort_values('rule_no')
        except Exception as e:
            raise Exception(f"Failed to load rules data: {str(e)}")

    def load_form_data(self, form_row_id: int) -> pd.DataFrame:
        """Load form submission from db into a pandas DataFrame."""
        try:
            query = f"SELECT * FROM dbo.philips_form_submission WHERE id = {form_row_id}"
            return self.azure_client.load_table_to_dataframe(
                table_name="philips_form_submission",
                custom_query=query
            )
        except Exception as e:
            raise Exception(f"Failed to load form data: {str(e)}")

    def process_form_data(self, form_data_df, rules_df):
        """Process form data against rules and generate results."""
        results = []
        
        for _, rule in rules_df.iterrows():
            rule_id = rule['rule_id']
            
            if rule_id not in form_data_df.columns:
                continue
                
            answer = form_data_df[rule_id].iloc[0]
            answer_lower = str(answer).lower()
                
            justification_key = f"{rule_id}_justified"
            has_justification = (justification_key in form_data_df.columns and 
                               str(form_data_df[justification_key].iloc[0]).lower() == 'yes')

            # We are hardcoding these changes until the next revision is put in place
            # until the next round of changes are implemented
            if rule['rule_id'] == 'bp_4_3':
                if answer_lower == 'yes':
                    meets_requirements = has_justification
                else: # answser is no, no need for justification
                    meets_requirements = True
            elif rule['rule_id'] == 'bp_4_4':
                if answer_lower == 'yes':
                    meets_requirements = False
                else: # answer is no
                    meets_requirements = True
            elif rule['rule_id'] == 'bp_4_5':
                if answer_lower == 'yes':
                    meets_requirements = True
                else: # answer is no, use justification
                    meets_requirements = has_justification
            # Are All SSID in the WLAN being broadcast?
            elif rule['rule_id'] == 'bp_8_3':
                if answer_lower == 'yes':
                    meets_requirements = True
                else: # answer is no, use justification
                    meets_requirements = has_justification
            # Is AES/CCMP encryption in use on all SSIDs?
            elif rule['rule_id'] == 'bp_9_1':
                if answer_lower == 'yes':
                    meets_requirements = True
                else:
                    meets_requirements = has_justification

            elif answer_lower == 'yes':
                if justification_key in form_data_df.columns:
                    meets_requirements = has_justification
                else:
                    meets_requirements = rule['on_yes'] == 'PASS'
                    
            elif answer_lower == 'no':
                meets_requirements = rule['on_no'] == 'PASS'
                
            else:
                meets_requirements = True

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

    def get_philips_sections(self, results):
        """Build report sections based on processed results."""
        sections = {}
        
        category = 'bp_philips'
        category_results = [r for r in results if r['category'] == category]
        
        html_content_requirement_results = philips.get_table_template()
        html_content_findings_table = philips.get_findings_and_recommendations_table()
        
        for result in category_results:
            bg_color = philips.GREEN if result['meets_requirements'] == 'Yes' else philips.RED
            html_content_requirement_results += philips.get_row_template(bg_color, result)

            if result['meets_requirements'] != 'Yes':
                html_content_findings_table += philips.get_findings_and_recommendations_row(
                    result['findings'], 
                    result['recommendations']
                )
                
        html_content_requirement_results += "</table>"
        html_content_findings_table += "</table>"
        
        sections[category] = html_content_requirement_results

        total_results = len(category_results)
        passing_results = sum(1 for r in category_results if r['meets_requirements'] == 'Yes')

        placeholder_findings = f"{category}_findings"
        sections[placeholder_findings] = (html_content_findings_table 
                                        if passing_results != total_results 
                                        else "")

        return sections

    def get_bp_sections(self, results):
        """Build report sections based on processed results."""
        sections = {}

        html_content_findings_table = philips.get_findings_and_recommendations_table()
        categories = set(result['category'] for result in results)

        for category in categories:
            if category == 'bp_philips':
                continue
            
            html_content_requirement_results = philips.get_table_template()
            group_results = [result for result in results if result['category'] == category]

            for result in group_results:
                bg_color = philips.GREEN if result['meets_requirements'] == 'Yes' else philips.RED
                html_content_requirement_results += philips.get_row_template(bg_color, result)

                if result['meets_requirements'] != 'Yes':
                    html_content_findings_table += philips.get_findings_and_recommendations_row(
                        result['findings'], 
                        result['recommendations']
                    )
                
            html_content_requirement_results += "</table>"
            sections[category] = html_content_requirement_results

            total_results = len(group_results)
            passing_results = sum(1 for r in group_results if r['meets_requirements'] == 'Yes')
            html_content_progress_bar = philips.get_progress_bar_table(passing_results, total_results)
            placeholder_pbar = f"{category}_progressbar"
            sections[placeholder_pbar] = html_content_progress_bar    
        
        html_content_findings_table += "</table>"
        sections['bp_combined_findings'] = html_content_findings_table

        return sections

    def build_scorecard(self, json_data: str) -> str:
        """Main method to build the scorecard."""
        json_dict = json.loads(json_data)
        document = get_document(json_dict['document_content'])
        form_row_id = json_dict['form_row_id']

        form_df = self.load_form_data(int(form_row_id))
        rules_df = self.load_rules_data()
        results = self.process_form_data(form_df, rules_df)
        
        html_sections = {
            **self.get_philips_sections(results),
            **self.get_bp_sections(results)
        }
        replace_placeholders_in_docx(document, html_sections)

        new_content = convert_doc_to_base64(document)
        return json.dumps({"new_document_content": new_content})