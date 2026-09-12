# utils/notifier.py
import smtplib
from email.message import EmailMessage
import os
from utils.ai_analyzer import generate_root_cause_analysis # <-- Importar o analisador de IA
from dotenv import load_dotenv
load_dotenv()  # Carrega as variáveis do .env para o ambiente

SESSION_DATA = {
    "api_traces": [],
    "failure_logs": [] # <-- Recolher logs de erro para a IA
}

def record_api_trace(method, url, request_payload, status_code, response_body):
    SESSION_DATA["api_traces"].append({
        "method": method,
        "url": url,
        "request_payload": request_payload,
        "status_code": status_code,
        "response_body": response_body
    })
    # Se o status code indicar erro, guarda nos logs de falha
    if status_code >= 400:
        SESSION_DATA["failure_logs"].append(f"API Error {status_code} on {method} {url} - Response: {response_body}")

def record_test_failure(error_message):
    """Regista falhas de testes para a IA analisar."""
    SESSION_DATA["failure_logs"].append(error_message)

def send_execution_email(exit_status):
    sender = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    receiver = os.getenv("MAIL_RECEIVER", "alagesibs@gmail.com")

    if not sender or not password:
        print(">>> Skipping email: MAIL_USERNAME or MAIL_PASSWORD environment variables not set.")
        return

    status_text = "PASSED" if exit_status == 0 else "FAILED"
    status_color = "#28a745" if exit_status == 0 else "#dc3545"

    # Gerar análise da IA se houver registos de erro ou se a execução falhou
    ai_section_html = ""
    if exit_status != 0 or SESSION_DATA["failure_logs"]:
        combined_logs = "\n".join(SESSION_DATA["failure_logs"])
        ai_summary = generate_root_cause_analysis(combined_logs)
        ai_section_html = f"""
        <div style="border-left: 4px solid #dc3545; background: #fff5f5; padding: 12px; margin-bottom: 20px; border-radius: 0 4px 4px 0;">
            <h4 style="margin: 0 0 6px 0; color: #c53030;">🤖 AI Root-Cause Analysis (Gemini)</h4>
            <p style="margin: 0; font-size: 13px; color: #2d3748; white-space: pre-line;">{ai_summary}</p>
        </div>
        """

    traces_html = ""
    for index, trace in enumerate(SESSION_DATA["api_traces"], start=1):
        badge_color = "#28a745" if 200 <= trace['status_code'] < 300 else "#dc3545"
        traces_html += f"""
        <div style="border: 1px solid #ddd; border-radius: 6px; padding: 12px; margin-bottom: 12px; background: #fdfdfd; font-family: monospace; font-size: 12px;">
            <p style="margin: 0 0 8px 0;"><b>[{index}] {trace['method']}</b> <span style="color: #0066cc;">{trace['url']}</span></p>
            <p style="margin: 0 0 8px 0;"><b>Status Code:</b> <span style="background: {badge_color}; color: white; padding: 2px 6px; border-radius: 3px;">{trace['status_code']}</span></p>
            <p style="margin: 0 0 4px 0;"><b>Request Payload / Params:</b></p>
            <pre style="background: #f1f1f1; padding: 8px; border-radius: 4px; overflow-x: auto; margin: 0 0 8px 0;">{trace['request_payload']}</pre>
            <p style="margin: 0 0 4px 0;"><b>Response Body:</b></p>
            <pre style="background: #f1f1f1; padding: 8px; border-radius: 4px; overflow-x: auto; margin: 0;">{trace['response_body']}</pre>
        </div>
        """

    if not traces_html:
        traces_html = "<p style='color: #666;'>No API traces recorded during this execution.</p>"

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <div style="max-width: 750px; margin: auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 8px; background: #ffffff;">
            <h2 style="border-bottom: 2px solid #eaeaea; padding-bottom: 10px; margin-top: 0;">FP&A Automation Report</h2>
            <p style="font-size: 14px;"><b>Overall Status:</b> <span style="color: {status_color}; font-weight: bold; font-size: 16px;">{status_text}</span></p>
            <p style="font-size: 14px;"><b>Pytest Exit Code:</b> {exit_status}</p>
            
            {ai_section_html}
            
            <h3 style="margin-top: 25px; border-bottom: 1px solid #ddd; padding-bottom: 5px;">API Requests & Responses (Allure Trace Match)</h3>
            {traces_html}
            
            <p style="font-size: 11px; color: #888; margin-top: 30px; text-align: center; border-top: 1px solid #eaeaea;">Generated automatically by FP&A Automation Framework.</p>
        </div>
    </body>
    </html>
    """

    msg = EmailMessage()
    msg['Subject'] = f"FP&A Execution Report - [{status_text}]"
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