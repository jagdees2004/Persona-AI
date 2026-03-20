"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ──────────────────────────── Onboarding ────────────────────────────

class GlobalProfileRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = None
    location: Optional[str] = None
    interests: Optional[list[str]] = None
    communication_style: Optional[str] = None


class GlobalProfileResponse(BaseModel):
    user_id: str
    name: str
    message: str = "Profile saved successfully"


# ──────────────────────── Persona Preferences ───────────────────────

class PersonaPreferencesRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    persona: str = Field(..., min_length=1)
    preferences: dict[str, Any] = Field(default_factory=dict)


class PersonaPreferencesResponse(BaseModel):
    user_id: str
    persona: str
    message: str = "Persona preferences saved"


# ────────────────────────────── Chat ────────────────────────────────

class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=4096)
    persona: Optional[str] = None  # Optional switch


class ChatResponse(BaseModel):
    user_id: str
    persona: str
    message: str
    response: str
    timestamp: str


# ──────────────────────────── Memory ────────────────────────────────

class MemoryRequest(BaseModel):
    user_id: str
    persona: str


class MemoryResponse(BaseModel):
    user_id: str
    persona: str
    recent_messages: list[dict[str, str]]
    summary: Optional[str] = None
    long_term_count: int = 0


class ResetRequest(BaseModel):
    user_id: str
    persona: str


class ResetResponse(BaseModel):
    user_id: str
    persona: str
    message: str = "Memory reset successfully"


# ──────────────────────────── Personas ──────────────────────────────

class PersonaInfo(BaseModel):
    name: str
    description: str
    tone: str
    response_style: str
    persona_specific_fields: list[str] = []


class PersonaListResponse(BaseModel):
    personas: list[PersonaInfo]


# ──────────────────────────── Health ────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    timestamp: str
