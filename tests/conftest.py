# conftest.py
import pytest
import requests
import allure
from utils.notifier import record_api_trace, record_test_outcome, send_execution_email

@pytest.fixture(scope="session")
def api_base_url():
    return "https://httpbin.org"

@pytest.fixture(scope="session")
def api_client(api_base_url):
    class AllureRequestsSession:
        def __init__(self):
            self.session = requests.Session()
            self.session.headers.update({"Content-Type": "application/json"})

        def _resolve_url(self, url):
            if url.startswith("http://") or url.startswith("https://"):
                return url
            return f"{api_base_url}{url}" if url.startswith("/") else f"{api_base_url}/{url}"

        def get(self, url, **kwargs):
            full_url = self._resolve_url(url)
            with allure.step(f"API GET -> {full_url}"):
                response = self.session.get(full_url, **kwargs)
                self._attach_to_allure(response, kwargs.get("params"))
                record_api_trace("GET", full_url, kwargs.get("params"), response.status_code, response.text)
                return response

        def post(self, url, data=None, json=None, **kwargs):
            full_url = self._resolve_url(url)
            with allure.step(f"API POST -> {full_url}"):
                response = self.session.post(full_url, data=data, json=json, **kwargs)
                self._attach_to_allure(response, json or data)
                record_api_trace("POST", full_url, json or data, response.status_code, response.text)
                return response

        def _attach_to_allure(self, response, request_payload):
            allure.attach(
                f"URL: {response.request.url}\nMethod: {response.request.method}\nPayload: {request_payload}",
                name="HTTP Request Trace",
                attachment_type=allure.attachment_type.TEXT
            )
            allure.attach(
                f"Status Code: {response.status_code}\nBody: {response.text}",
                name="HTTP Response Trace",
                attachment_type=allure.attachment_type.TEXT
            )

    return AllureRequestsSession()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        test_name = item.name
        is_passed = report.passed
        error_message = "-"
        
        if not is_passed:
            # Extrai apenas a mensagem limpa da asserção, ignorando o traceback gigante
            if hasattr(report, "longrepr") and hasattr(report.longrepr, "reprcrash"):
                error_message = report.longrepr.reprcrash.message
            else:
                error_message = str(report.longrepr)

        record_test_outcome(test_name, is_passed, error_message)

def pytest_sessionfinish(session, exitstatus):
    """Trigger unified HTML email after pytest finishes."""
    send_execution_email(exitstatus)