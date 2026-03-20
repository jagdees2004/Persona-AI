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

# State container to avoid NameErrors with globals
_state = {
    "client": None,
    "chat_model": None
}

def get_client():
    """Lazily get or create the InferenceClient."""
    if _state["client"]: 
        return _state["client"]
    
    settings = get_settings()
    # Prioritize HF_TOKEN env var or fallback to .env config
    hf_token = os.getenv("HF_TOKEN") or settings.HUGGINGFACE_API_KEY
    
    if not hf_token:
        logger.warning("HUGGINGFACE_API_KEY is not set in settings or environment.")
        return None
        
    _state["client"] = InferenceClient(
        model=settings.LLM_MODEL, 
        token=hf_token
    )
    return _state["client"]

def get_chat_model():
    """Lazily get or create the LangChain-wrapped chat model."""
    if _state["chat_model"]: 
        return _state["chat_model"]
    
    if get_client():
        _state["chat_model"] = RunnableLambda(_async_chat_call)
    return _state["chat_model"]

MAX_RETRIES = 5

def _sync_chat_call(lc_messages: List[BaseMessage], max_tokens: int, temperature: float, top_p: float) -> AIMessage:
    """Synchronous interface logic running in thread to process LangChain formatted messages."""
    try:
        # Adapt LangChain Messages to HuggingFace schema
        dicts = []
        for m in lc_messages:
            role = "user"
            if m.type == "human": role = "user"
            elif m.type in ("ai", "assistant"): role = "assistant"
            elif m.type == "system": role = "system"
            dicts.append({"role": role, "content": m.content})

        client = get_client()
        if not client:
            raise ValueError("InferenceClient not initialized")

        response = client.chat_completion(
            messages=dicts,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=False
        )
        
        reply = response.choices[0].message.content
        return AIMessage(content=reply)
    except Exception as e:
        logger.exception(f"Critical error in _sync_chat_call: {e}")
        raise

async def _async_chat_call(inputs: dict) -> AIMessage:
    messages = inputs.get("messages")
    max_tokens = inputs.get("max_new_tokens", 512)
    temperature = inputs.get("temperature", 0.7)
    top_p = inputs.get("top_p", 0.9)
    return await asyncio.to_thread(_sync_chat_call, messages, max_tokens, temperature, top_p)

# Removed global model initialization to use lazy getters

async def generate_response(
    messages: List[Dict[str, str]],
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> str:
    """
    Send a request to HuggingFace Inference API using our custom LangChain Model interface.
    """
    model = get_chat_model()
    if not model:
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
            response = await model.ainvoke(inputs)
            
            return response.content.strip()
        except Exception as e:
            last_error = str(e)
            logger.error(f"LLM request error: {last_error} (attempt {attempt + 1})")
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
    return get_chat_model() is not None
