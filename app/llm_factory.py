import os
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

def get_llm_engine():
    # 1. Primary: Groq API
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip():
        groq_key = settings.GROQ_API_KEY.strip()
        
        # Try active Groq models in sequence
        for model in ["openai/gpt-oss-120b", "llama-3.1-8b-instant", "llama-3.3-70b-versatile"]:
            try:
                llm = ChatGroq(
                    groq_api_key=groq_key,
                    model_name=model,
                    temperature=0.3
                )
                # Test invocation to confirm model availability
                llm.invoke("Test ping")
                print(f"🤖 [LLM Factory] Active Groq model connected: '{model}'")
                return llm
            except Exception as e:
                print(f"⚠️ [Groq Model '{model}' unavailable]: {e}")

    # 2. Fallback: Google Gemini API
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        try:
            print("🤖 [LLM Factory] Connecting Google Gemini Fallback ('gemini-2.0-flash')...")
            return ChatGoogleGenerativeAI(
                google_api_key=settings.GEMINI_API_KEY.strip(),
                model="gemini-2.0-flash",
                temperature=0.3
            )
        except Exception as e:
            print(f"⚠️ [Gemini Init Error]: {e}")
    
    raise RuntimeError("No valid Groq or Gemini API models are accessible with provided keys.")

llm_engine = get_llm_engine()