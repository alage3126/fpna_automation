# tests/test_api.py
import allure
import pytest
from utils.notifier import record_test_failure

@allure.epic("FP&A Backend Integration")
@allure.feature("Data Warehouse & ERP Synchronization")
@allure.title("Verify financial metrics endpoint with full HTTP tracing")
@allure.severity(allure.severity_level.CRITICAL)
def test_metrics_sync_status(api_client):
    """TEST 1: Deve passar com sucesso (PASSED)"""
    endpoints = ["/status/200", "/json"]
    
    for index, endpoint in enumerate(endpoints, start=1):
        with allure.step(f"Iteration {index}: Requesting endpoint {endpoint}"):
            response = api_client.get(endpoint)
            
        with allure.step(f"Iteration {index}: Validate successful HTTP status"):
            assert response.status_code == 200, f"Failed on endpoint {endpoint} with status {response.status_code}"

@allure.epic("FP&A Backend Integration")
@allure.feature("Data Warehouse & ERP Synchronization")
@allure.title("Verify creation of financial post/report entry")
@allure.severity(allure.severity_level.NORMAL)
def test_create_financial_post(api_client):
    """TEST 2: Forçado a falhar (FAILED) para testar a IA e o report"""
    payload = {
        "title": "Q3 Forecast Adjustment",
        "body": "Automated ledger entry for regional revenue variance.",
        "userId": 42
    }
    
    with allure.step("Send POST request to create a financial post entry"):
        response = api_client.post("https://jsonplaceholder.typicode.com/posts", json=payload)
    
    with allure.step("Validate post creation response code and payload structure"):
        try:
            # Forçamos uma falha intencional alterando o status esperado para 200 (sendo que o JSONPlaceholder retorna 201)
            assert response.status_code == 200, f"Ledger synchronization mismatch: Expected HTTP 200 OK for financial ledger commit, but remote ERP gateway returned HTTP {response.status_code} with payload structure error."
        except AssertionError as e:
            record_test_failure(str(e))
            raise e