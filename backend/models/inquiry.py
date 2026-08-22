import re
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator

def normalize_phone_number(phone_str: str) -> str:
    """
    Standardizes a phone number by extracting digits only.
    Returns digits string (e.g. '9876543210' or '919876543210').
    """
    if not phone_str:
        return ""
    return re.sub(r"\D", "", phone_str)

class InquiryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the user inquiring")
    requirements: str = Field(..., min_length=5, max_length=5000, description="Project specifications and requirements")
    budget: str = Field(..., min_length=2, max_length=200, description="Estimated or preferred budget")
    contactNumber: str = Field(..., min_length=7, max_length=30, description="Contact phone number")
    normalizedPhone: Optional[str] = Field(default=None, description="Normalized digits-only phone number")
    source: Optional[str] = Field(default="api", description="Source of inquiry (chatbot, whatsapp, api, web_form, php)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Name must contain valid alphabetical characters.")
        return v

    @field_validator("requirements")
    @classmethod
    def validate_requirements(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Requirements must provide at least 5 characters of description.")
        return v

    @field_validator("budget")
    @classmethod
    def validate_budget(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Budget cannot be empty.")
        return v

    @field_validator("contactNumber")
    @classmethod
    def validate_contact_number(cls, v: str) -> str:
        v = v.strip()
        # Clean phone string to digits
        digits_only = re.sub(r"\D", "", v)
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValueError("Contact number must contain between 7 and 15 digits.")
        # Check allowed characters in raw format (+, -, (), spaces, digits)
        if not re.match(r"^[+()0-9\s\-]+$", v):
            raise ValueError("Contact number contains invalid characters.")
        return v

class InquiryResponseData(BaseModel):
    id: str
    name: str
    requirements: str
    budget: str
    contactNumber: str
    normalizedPhone: Optional[str] = None
    createdAt: str
    updatedAt: str
    source: Optional[str] = "api"

class InquiryAPIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[InquiryResponseData] = None
    error: Optional[str] = None

