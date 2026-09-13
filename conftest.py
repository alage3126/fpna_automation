# conftest.py
import pytest  # Importa a biblioteca de testes Pytest
import requests  # Importa a biblioteca para fazer requisições HTTP
import allure  # Importa a biblioteca para geração de relatórios detalhados com Allure
from utils.notifier import record_api_trace, record_test_outcome, send_execution_email  # Importa funções utilitárias personalizadas de notificação

@pytest.fixture(scope="session")  # Define uma fixture que será executada uma única vez para toda a sessão de testes
def api_base_url():
    return "https://httpbin.org"  # Retorna a URL base padrão utilizada para os testes de API

@pytest.fixture(scope="session")  # Define outra fixture compartilhada por toda a sessão de testes
def api_client(api_base_url):  # Injeta a fixture api_base_url como dependência
    class AllureRequestsSession:  # Cria uma classe interna para envelopar e personalizar as chamadas da biblioteca requests
        def __init__(self):
            self.session = requests.Session()  # Cria uma sessão HTTP persistente (reutiliza conexões)
            self.session.headers.update({"Content-Type": "application/json"})  # Define o cabeçalho padrão das requisições como JSON

        def _resolve_url(self, url):  # Método utilitário privado para formatar URLs completas
            if url.startswith("http://") or url.startswith("https://"):  # Verifica se a URL enviada já é absoluta
                return url  # Se for absoluta, mantém como está
            # Se começar com '/', apenas junta com a URL base; caso contrário, adiciona a '/' intermediária
            return f"{api_base_url}{url}" if url.startswith("/") else f"{api_base_url}/{url}"

        def get(self, url, **kwargs):  # Wrapper customizado para o método HTTP GET
            full_url = self._resolve_url(url)  # Converte o caminho relativo em URL completa
            with allure.step(f"API GET -> {full_url}"):  # Agrupa a ação como um passo visual no relatório do Allure
                response = self.session.get(full_url, **kwargs)  # Executa a requisição GET real
                self._attach_to_allure(response, kwargs.get("params"))  # Anexa os dados de envio/resposta ao relatório Allure
                record_api_trace("GET", full_url, kwargs.get("params"), response.status_code, response.text)  # Registra o log no rastreador externo
                return response  # Retorna o objeto de resposta HTTP para o teste

        def post(self, url, data=None, json=None, **kwargs):  # Wrapper customizado para o método HTTP POST
            full_url = self._resolve_url(url)  # Converte o caminho relativo em URL completa
            with allure.step(f"API POST -> {full_url}"):  # Agrupa a ação como um passo visual no relatório do Allure
                response = self.session.post(full_url, data=data, json=json, **kwargs)  # Executa a requisição POST real
                self._attach_to_allure(response, json or data)  # Anexa o payload de envio e resposta ao relatório Allure
                record_api_trace("POST", full_url, json or data, response.status_code, response.text)  # Registra o log no rastreador externo
                return response  # Retorna o objeto de resposta HTTP para o teste

        def _attach_to_allure(self, response, request_payload):  # Método auxiliar para criar anexos de texto no Allure
            allure.attach(
                f"URL: {response.request.url}\nMethod: {response.request.method}\nPayload: {request_payload}",  # Monta o texto de detalhes do envio
                name="HTTP Request Trace",  # Nome exibido no painel do Allure para a requisição
                attachment_type=allure.attachment_type.TEXT  # Define o formato do anexo como texto puro
            )
            allure.attach(
                f"Status Code: {response.status_code}\nBody: {response.text}",  # Monta o texto de detalhes da resposta obtida
                name="HTTP Response Trace",  # Nome exibido no painel do Allure para a resposta
                attachment_type=allure.attachment_type.TEXT  # Define o formato do anexo como texto puro
            )

    return AllureRequestsSession()  # Retorna a instância da classe criada para ser usada nos testes

@pytest.hookimpl(tryfirst=True, hookwrapper=True)  # Intercepta a execução dos testes antes de outros plugins do Pytest
def pytest_runtest_makereport(item, call):  # Hook do Pytest que monitora o resultado/relatório de cada teste
    outcome = yield  # Pausa a execução para deixar o Pytest rodar o teste e capturar o resultado
    report = outcome.get_result()  # Obtém o objeto contendo o status final do teste

    if report.when == "call":  # Filtra apenas a fase de execução real do teste (ignora 'setup' e 'teardown')
        test_name = item.name  # Obtém o nome da função do teste
        is_passed = report.passed  # Retorna True se o teste passou e False caso tenha falhado
        error_message = "-"  # Define uma mensagem de erro padrão caso o teste passe
        
        if not is_passed:  # Se o teste falhar
            # Extrai apenas a mensagem limpa da asserção, ignorando o traceback gigante
            if hasattr(report, "longrepr") and hasattr(report.longrepr, "reprcrash"):
                error_message = report.longrepr.reprcrash.message  # Extrai a mensagem resumida e direta da falha
            else:
                error_message = str(report.longrepr)  # Caso não exista o resumo, converte o traceback completo em string

        record_test_outcome(test_name, is_passed, error_message)  # Envia o resultado do teste para a função utilitária

def pytest_sessionfinish(session, exitstatus):  # Hook executado automaticamente quando toda a suíte de testes termina
    """Trigger unified HTML email after pytest finishes."""
    send_execution_email(exitstatus)  # Envia o e-mail de relatório consolidado passando o status final do Pytest