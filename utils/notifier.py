# utils/notifier.py
import smtplib
from email.message import EmailMessage
import os
from utils.ai_analyzer import generate_root_cause_analysis
from dotenv import load_dotenv
load_dotenv()

SESSION_DATA = {
    "api_traces": [],
    "test_results": [],
    "failure_logs": []
}

def record_api_trace(method, url, request_payload, status_code, response_body):
    SESSION_DATA["api_traces"].append({
        "method": method,
        "url": url,
        "request_payload": request_payload,
        "status_code": status_code,
        "response_body": response_body
    })

def record_test_outcome(test_name, is_passed, error_message):
    """Processa o resultado do teste e obtém a análise de IA individual se falhar."""
    ai_reason = "-"
    if not is_passed:
        # Pede ao Gemini a análise de causa raiz específica para este erro
        ai_reason = generate_root_cause_analysis(error_message)
        SESSION_DATA["failure_logs"].append(f"Test '{test_name}' failed: {error_message}")

    SESSION_DATA["test_results"].append({
        "name": test_name,
        "passed": is_passed,
        "error_message": error_message,
        "ai_reason": ai_reason
    })

def send_execution_email(exit_status):
    sender = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    receiver = os.getenv("MAIL_RECEIVER", "alagesibs@gmail.com")

    if not sender or not password:
        print(">>> Skipping email: MAIL_USERNAME or MAIL_PASSWORD environment variables not set.")
        return

    status_text = "PASSED" if exit_status == 0 else "FAILED"
    
    total_executed = len(SESSION_DATA["test_results"])
    failed_count = sum(1 for t in SESSION_DATA["test_results"] if not t["passed"])
    passed_count = total_executed - failed_count

    rows_html = ""
    if SESSION_DATA["test_results"]:
        for test in SESSION_DATA["test_results"]:
            is_passed = test["passed"]
            result_label = "PASSED" if is_passed else "FAILED"
            badge_bg = "#c6f6d5" if is_passed else "#fed7d7"
            badge_color = "#22543d" if is_passed else "#9b2c2c"
            
            if is_passed:
                error_content = "-"
            else:
                # Formata a razão com a explicação gerada pelo Gemini diretamente na coluna
                error_content = f"""
                <div style="color: #c53030; font-weight: bold; margin-bottom: 4px;">-> {test['error_message']}</div>
                <div style="background-color: #fff5f5; border-left: 3px solid #c53030; padding: 8px; font-size: 12px; color: #2d3748; border-radius: 2px; margin-top: 4px;">
                    <b>🤖 AI Analysis:</b> {test['ai_reason']}
                </div>
                """

            rows_html += f"""
            <tr style="border-bottom: 1px solid #edf2f7;">
                <td style="padding: 12px; vertical-align: top;">
                    <strong style="color: #2d3748; font-size: 13px;">{test['name']}</strong>
                </td>
                <td style="padding: 12px; vertical-align: middle; white-space: nowrap;">
                    <span style="background-color: {badge_bg}; color: {badge_color}; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold;">{result_label}</span>
                </td>
                <td style="padding: 12px; vertical-align: top; font-size: 12px;">
                    {error_content}
                </td>
            </tr>
            """
    else:
        rows_html = """
        <tr>
            <td colspan="3" style="padding: 20px; text-align: center; color: #718096; font-size: 13px;">
                No test results recorded during this execution.
            </td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; color: #333333; margin: 0; padding: 20px; background-color: #ffffff;">
        <div style="max-width: 800px; margin: auto;">
            
            <h2 style="color: #2b6cb0; border-bottom: 2px solid #3182ce; padding-bottom: 8px; margin-bottom: 20px; font-size: 20px;">
                📊 Automated Test Summary
            </h2>

            <div style="background-color: #f7fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 16px; margin-bottom: 24px; font-weight: bold; font-size: 13px; color: #4a5568;">
                <span style="margin-right: 20px;">Total Executed: <span style="font-weight: normal; color: #1a202c;">{total_executed}</span></span>
                <span style="color: #2f855a; margin-right: 20px;">Passed: <span style="font-weight: normal; color: #1a202c;">{passed_count}</span></span>
                <span style="color: #c53030;">Failed: <span style="font-weight: normal; color: #1a202c;">{failed_count}</span></span>
            </div>

            <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
                <thead>
                    <tr style="background-color: #3182ce; color: #ffffff;">
                        <th style="padding: 10px 12px; border-top-left-radius: 4px; font-weight: 600;">Test Name / IDs</th>
                        <th style="padding: 10px 12px; font-weight: 600;">Result</th>
                        <th style="padding: 10px 12px; border-top-right-radius: 4px; font-weight: 600;">Error Failure Reason</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <p style="font-size: 11px; color: #a0aec0; margin-top: 30px; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 15px;">
                Generated automatically by FP&A Automation Framework
            </p>
        </div>
    </body>
    </html>
    """

    msg = EmailMessage()
    msg['Subject'] = f"Automated Test Summary - [{status_text}]"
    msg['From'] = sender
    msg['To'] = receiver
    msg.set_content(f"Test run completed with status: {status_text}.")
    msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print(">>> Execution report email sent successfully.")
    except Exception as e:
        print(f">>> Failed to send email: {e}")