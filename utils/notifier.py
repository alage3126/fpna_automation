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
    
    # Contadores globais baseados nos vestígios guardados
    total_executed = max(len(SESSION_DATA["api_traces"]), 1)
    failed_count = len(SESSION_DATA["failure_logs"])
    passed_count = max(total_executed - failed_count, 0)

    # Gerar análise da IA se houver registos de erro ou se a execução falhou
    ai_section_html = ""
    if exit_status != 0 or SESSION_DATA["failure_logs"]:
        combined_logs = "\n".join(SESSION_DATA["failure_logs"])
        ai_summary = generate_root_cause_analysis(combined_logs)
        ai_section_html = f"""
        <div style="border-left: 4px solid #c53030; background: #fff5f5; padding: 12px 16px; margin-bottom: 24px; border-radius: 0 4px 4px 0;">
            <h4 style="margin: 0 0 6px 0; color: #c53030; font-size: 14px;">🤖 AI Root-Cause Analysis (Gemini)</h4>
            <p style="margin: 0; font-size: 13px; color: #2d3748; white-space: pre-line; line-height: 1.4;">{ai_summary}</p>
        </div>
        """

    # Construção das linhas da tabela inspiradas no design fornecido
    rows_html = ""
    if SESSION_DATA["api_traces"]:
        for trace in SESSION_DATA["api_traces"]:
            is_success = 200 <= trace['status_code'] < 400
            result_label = "PASSED" if is_success else "FAILED"
            badge_bg = "#c6f6d5" if is_success else "#fed7d7"
            badge_color = "#22543d" if is_success else "#9b2c2c"
            
            error_reason = "-" if is_success else f"HTTP {trace['status_code']} Error"

            rows_html += f"""
            <tr style="border-bottom: 1px solid #edf2f7;">
                <td style="padding: 12px; vertical-align: top;">
                    <strong style="color: #2d3748; font-size: 13px;">{trace['method']} - {trace['url']}</strong><br>
                    <div style="background-color: #edf2f7; border-left: 3px solid #3182ce; padding: 8px 10px; margin-top: 8px; font-family: monospace; font-size: 11px; color: #2d3748; border-radius: 2px;">
                        <b>Payload:</b> {trace['request_payload']}<br>
                        <b>Response:</b> {trace['response_body']}
                    </div>
                </td>
                <td style="padding: 12px; vertical-align: middle; white-space: nowrap;">
                    <span style="background-color: {badge_bg}; color: {badge_color}; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold;">{result_label}</span>
                </td>
                <td style="padding: 12px; vertical-align: middle; color: #718096; font-size: 13px;">
                    {error_reason}
                </td>
            </tr>
            """
    else:
        rows_html = """
        <tr>
            <td colspan="3" style="padding: 20px; text-align: center; color: #718096; font-size: 13px;">
                No API traces or test items recorded during this execution.
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
            
            <!-- Cabeçalho -->
            <h2 style="color: #2b6cb0; border-bottom: 2px solid #3182ce; padding-bottom: 8px; margin-bottom: 20px; font-size: 20px;">
                📊 Automated Test Summary
            </h2>

            <!-- Bloco de Métricas Totais -->
            <div style="background-color: #f7fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 16px; margin-bottom: 24px; font-weight: bold; font-size: 13px; color: #4a5568;">
                <span style="margin-right: 20px;">Total Executed: <span style="font-weight: normal; color: #1a202c;">{total_executed}</span></span>
                <span style="color: #2f855a; margin-right: 20px;">Passed: <span style="font-weight: normal; color: #1a202c;">{passed_count}</span></span>
                <span style="color: #c53030;">Failed: <span style="font-weight: normal; color: #1a202c;">{failed_count}</span></span>
            </div>

            {ai_section_html}

            <!-- Tabela de Resultados -->
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
                Generated automatically by FP&A Automation Framework &bull; Powered by Gemini AI
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