import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from philips_scorecard.remediation_list_generator import *

async def test_remediation_list_generator():

    # Build the full path to the file
    remediation_excel_filename = 'philips_scorecard/io/remediation_list_sample.xlsx'
    remediation_output_filename = 'philips_scorecard/io/remediation_list_output.docx'

    # Call the async function
    result = await generate_findings_report(remediation_excel_filename, 
                                            remediation_output_filename)

    print(f"Result: {result}")

if __name__ == '__main__':
    asyncio.run(test_remediation_list_generator())