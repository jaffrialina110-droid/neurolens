from google import genai

SYSTEM_PROMPT = """You are Ayna, NeuroLens's educational AI guide. Discuss cognition, behavior, neuroscience, learning, attention, memory, decision-making, and wellbeing carefully. Do not diagnose medical or mental-health conditions. Do not claim games, questionnaires, camera images, or self-reports measure brain activity or reveal true internal emotion. Distinguish evidence from hypotheses and uncertainty."""

def ask_ayna(prompt: str, language: str, api_key: str) -> str:
    if not api_key:
        raise RuntimeError("Gemini API key is not configured.")
    client = genai.Client(api_key=api_key)
    rule = "Reply in Roman English (Urdu/Hindi written in Latin letters)." if language == "Roman English" else "Reply in English."
    response = client.models.generate_content(model="gemini-2.5-flash", contents=f"{SYSTEM_PROMPT}\n{rule}\n\nUser: {prompt}")
    return (response.text or "").strip() or "I couldn't generate a response."
