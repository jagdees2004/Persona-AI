"""
LLM Service: calls to HuggingFace Inference API using standard LangChain interfaces.
Wraps the highly reliable huggingface_hub InferenceClient within a LangChain Runnable layout.
"""

import logging
import asyncio
import os
from typing import List, Dict
from core.config import get_settings

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableLambda
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)
settings = get_settings()

client = None
chat_model = None

# Prioritize HF_TOKEN env var or fallback to .env config
hf_token = os.getenv("HF_TOKEN") or settings.HUGGINGFACE_API_KEY

if hf_token:
    client = InferenceClient(
        model=settings.LLM_MODEL, 
        token=hf_token
    )

MAX_RETRIES = 5

def _sync_chat_call(lc_messages: List[BaseMessage], max_tokens: int, temperature: float, top_p: float) -> AIMessage:
    """Synchronous interface logic running in thread to process LangChain formatted messages."""
    
    # Adapt LangChain Messages to HuggingFace schema
    dicts = []
    for m in lc_messages:
        role = "user"
        if m.type == "human": role = "user"
        elif m.type in ("ai", "assistant"): role = "assistant"
        elif m.type == "system": role = "system"
        dicts.append({"role": role, "content": m.content})

    response_stream = client.chat_completion(
        messages=dicts,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        stream=True
    )
    
    full_text = ""
    for chunk in response_stream:
        if hasattr(chunk, "choices") and chunk.choices:
            if hasattr(chunk.choices[0], "delta") and hasattr(chunk.choices[0].delta, "content"):
                content = chunk.choices[0].delta.content
                if content:
                    full_text += content
                
    return AIMessage(content=full_text)

async def _async_chat_call(inputs: dict) -> AIMessage:
    messages = inputs.get("messages")
    max_tokens = inputs.get("max_new_tokens", 512)
    temperature = inputs.get("temperature", 0.7)
    top_p = inputs.get("top_p", 0.9)
    return await asyncio.to_thread(_sync_chat_call, messages, max_tokens, temperature, top_p)

# Create a LangChain Runnable to process invocations conforming to the Runnable API
if client:
    chat_model = RunnableLambda(_async_chat_call)

async def generate_response(
    messages: List[Dict[str, str]],
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> str:
    """
    Send a request to HuggingFace Inference API using our custom LangChain Model interface.
    """
    if not chat_model:
        return "⚠️ API key not configured. Please set HUGGINGFACE_API_KEY in your .env file."

    # Convert dictionaries to LangChain message objects
    lc_messages = []
    for msg in messages:
        role = msg.get("role", "").lower()
        content = msg.get("content", "")
        if role == "system":
            lc_messages.append(SystemMessage(content=content))
        elif role in ["user", "human"]:
            lc_messages.append(HumanMessage(content=content))
        elif role in ["assistant", "ai"]:
            lc_messages.append(AIMessage(content=content))
        else:
            lc_messages.append(HumanMessage(content=content))

    last_error = "Unknown error"
    inputs = {
        "messages": lc_messages,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Calling LLM api via LangChain setup (attempt {attempt+1})")
            
            # Utilize LangChain's invoke structure which processes asynchronously natively through RunnableLambda
            response = await chat_model.ainvoke(inputs)
            
            return response.content.strip()
        except Exception as e:
            last_error = str(e)
            logger.error(f"LLM request error: {e} (attempt {attempt + 1})")
            if "loading" in last_error.lower() or "503" in last_error:
                await asyncio.sleep(10)
            elif "429" in last_error:
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(2)

    logger.error(f"All LLM retries exhausted. Last error: {last_error}")
    return "I'm experiencing technical difficulties. Please try again in a moment."

async def health_check() -> bool:
    """Check if the API key is configured and valid."""
    if not chat_model: return False
    return True
