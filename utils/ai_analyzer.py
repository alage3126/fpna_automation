import os
from google import genai

def generate_root_cause_analysis(test_failure_logs: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "AI analysis skipped: GEMINI_API_KEY not configured."

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert FP&A Software Engineer and QA Automation Lead. 
    Analyze the following test failure trace data from our automated financial transaction pipeline. 
    Provide a concise, direct, business-impact-driven root-cause summary (maximum 3 sentences) explaining why the test failed and what broke in the ledger calculation or API payload:

    {test_failure_logs}
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Could not generate AI diagnostic summary: {str(e)}"