
RED = "#ffb2b5"
GREEN = "#b0e396"
YELLOW = "#f2d268"

def get_table_template() -> str:
    table_template = """
            <table style="padding:8px; width:100%; border-collapse:collapse; border:1px solid #c1c6cc;">
                <colgroup>
                    <col width="25%">
                    <col width="50%">
                    <col width="10%">
                    <col width="15%">
                </colgroup>
                <tr style="background-color:#ffffff;">
                    <th style="border:1px solid #c1c6cc; padding:6px; text-align:left;">Category</th>
                    <th style="border:1px solid #c1c6cc; padding:6px; text-align:left;">Message</th>
                    <th style="border:1px solid #c1c6cc; padding:6px; text-align:center;">Answer</th>
                    <th style="border:1px solid #c1c6cc; padding:6px; text-align:center;">Meets<br>Requirement</th>
                </tr>
    """
    return table_template

def get_row_template(bgcolor: str, data: dict) -> str:
    row_template = f"""
        <tr>
            <td style="border:1px solid #c1c6cc; padding:6px; text-align:left;">{data['question_category']}</td>
            <td style="border:1px solid #c1c6cc; padding:6px; text-align:left;">{data['message']}</td>
            <td style="border:1px solid #c1c6cc; padding:6px; text-align:center;">{data['answer']}</td>
            <td style="border:1px solid #c1c6cc; padding:6px; text-align:center; background-color:{bgcolor};">{data['meets_requirements']}</td>
        </tr>
    """

    #<br><b>Findings: </b>{data['findings']}<br>
    #<b>Recommendations: </b>{data['recommendations']}    
    return row_template

def get_findings_and_recommendations_table(col_width: str = '60', col_width2: str = '40') -> str:
    return f"""
        <table style="padding:8px; width:100%; border-collapse:collapse; border:1px solid #c1c6cc;">
            <colgroup>
                <col width="{col_width}%">
                <col width="{col_width2}%">
            </colgroup>            
            <tr style="background-color:#ffffff;">
                <th style="border:1px solid #c1c6cc; padding:6px; text-align:left;">Finding(s)</th>
                <th style="border:1px solid #c1c6cc; padding:6px; text-align:left;">Recommendation(s)</th>
            </tr>
   """

def get_findings_and_recommendations_row(findings: str, recommendations: str) -> str:
    return f"""
        <tr>
            <td style="border:1px solid #c1c6cc; padding:6px; text-align:left;">{findings}</td>
            <td style="border:1px solid #c1c6cc; padding:6px; text-align:left;">{recommendations}</td>
        </tr>
    """

def get_progress_bar_table(passing_results, total_results):
    """
    Create a progress bar table showing percentage of passing results.
    Using percentage-based widths for cells.
    
    Args:
        passing_results (int): Number of passing results
        total_results (int): Total number of results
        
    Returns:
        str: HTML table showing progress bar
    """
    pass_percentage = (passing_results / total_results * 100) if total_results > 0 else 0
    progress_width = f"{pass_percentage:.0f}"
    not_progress_width = f"{100 - pass_percentage:.0f}"

    # If 100%, only create one cell
    if pass_percentage == 100:
        return f"""
            <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                <tr>
                    <td style="width:100%; background-color:{GREEN}; border:1px solid #c1c6cc; padding:4px; text-align:center;">
                        <b>100%</b>
                    </td>
                </tr>
            </table>
        """
    else:
        return f"""
            <table style="width:100%; border-collapse:collapse; margin-top:10px; border:1px solid #c1c6cc;">
                <colgroup>
                    <col width="{progress_width}%">
                    <col width="{not_progress_width}%">
                </colgroup>
                <tr>
                    <td style="background-color:{GREEN}; border:1px solid #c1c6cc; padding:4px; text-align:center;">
                        <b>{progress_width}%</b>
                    </td>
                    <td style="background-color:#ffffff; border:1px solid #c1c6cc; padding:4px;">
                    </td>
                </tr>
            </table>
        """