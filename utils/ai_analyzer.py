import os
from google import genai

def generate_root_cause_analysis(test_failure_logs: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "AI analysis skipped: GEMINI_API_KEY not configured."

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
        Act as a senior QA Automation Lead and FP&A Engineer. Analyze the test error below and provide an ULTRA-SHORT response (maximum 2 sentences). 
        Be direct: focus solely on what broke in the API payload or ledger calculation and its business impact. No introductory filler.

        Error:
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