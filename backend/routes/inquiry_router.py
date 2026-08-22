import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, ValidationError

from models.inquiry import InquiryCreate, InquiryAPIResponse, InquiryResponseData, normalize_phone_number
from services.inquiry_service import InquiryService
from database import get_inquiries_collection

logger = logging.getLogger("inquiry_router")

router = APIRouter(prefix="", tags=["Inquiries"])

class InquiryHistoryRequest(BaseModel):
    contactNumber: str = Field(..., description="Registered contact phone number to query history")

class InquiryHistoryResponse(BaseModel):
    success: bool
    phone: str
    total: int
    data: List[Dict[str, Any]]
    message: str

class WhatsAppWebhookPayload(BaseModel):
    phone: Optional[str] = Field(default=None, description="Customer phone number from WhatsApp webhook")
    contactNumber: Optional[str] = Field(default=None, description="Alternative field for contact number")
    message: Optional[str] = Field(default=None, description="Text message sent by customer")
    name: Optional[str] = Field(default=None, description="Customer name if submitting inquiry")
    requirements: Optional[str] = Field(default=None, description="Project requirements if submitting inquiry")
    budget: Optional[str] = Field(default=None, description="Project budget if submitting inquiry")

@router.post(
    "/api/inquiry",
    response_model=InquiryAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Project Inquiry",
    description="Submit a new project inquiry with name, requirements, budget, and contact number. Stores in MongoDB."
)
@router.post(
    "/inquiry",
    response_model=InquiryAPIResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
async def submit_inquiry(inquiry: InquiryCreate):
    try:
        saved_record = InquiryService.create_inquiry(inquiry)
        return InquiryAPIResponse(
            success=True,
            message="Project inquiry recorded successfully in MongoDB.",
            data=InquiryResponseData(**saved_record)
        )
    except RuntimeError as e:
        logger.error(f"Service runtime error in submit_inquiry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in submit_inquiry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while saving the inquiry."
        )

@router.get(
    "/api/inquiry/history",
    response_model=InquiryHistoryResponse,
    summary="Get Inquiry History by Phone Number",
    description="Fetch complete inquiry history for a customer using their phone number as the unique identifier."
)
async def get_inquiry_history_by_phone(phone: str):
    if not phone or not phone.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number query parameter is required."
        )
    inquiries = InquiryService.get_inquiries_by_phone(phone)
    return InquiryHistoryResponse(
        success=True,
        phone=phone.strip(),
        total=len(inquiries),
        data=inquiries,
        message=f"Retrieved {len(inquiries)} inquiry record(s) for phone '{phone}'."
    )

@router.post(
    "/api/inquiry/history",
    response_model=InquiryHistoryResponse,
    summary="Post Request for Inquiry History by Phone Number"
)
async def post_inquiry_history_by_phone(payload: InquiryHistoryRequest):
    phone = payload.contactNumber.strip()
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="contactNumber field cannot be empty."
        )
    inquiries = InquiryService.get_inquiries_by_phone(phone)
    return InquiryHistoryResponse(
        success=True,
        phone=phone,
        total=len(inquiries),
        data=inquiries,
        message=f"Retrieved {len(inquiries)} inquiry record(s) for phone '{phone}'."
    )

@router.post(
    "/api/webhook/whatsapp",
    summary="WhatsApp Webhook Endpoint for Inquiry Management"
)
async def whatsapp_webhook(payload: WhatsAppWebhookPayload):
    phone_val = payload.phone or payload.contactNumber
    if not phone_val:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required in WhatsApp webhook payload."
        )

    # If payload contains inquiry creation fields (name, requirements, budget)
    if payload.name and payload.requirements and payload.budget:
        inquiry_input = InquiryCreate(
            name=payload.name,
            requirements=payload.requirements,
            budget=payload.budget,
            contactNumber=phone_val,
            source="whatsapp"
        )
        saved = InquiryService.create_inquiry(inquiry_input)
        return {
            "success": True,
            "event": "inquiry_created",
            "message": "WhatsApp inquiry recorded successfully.",
            "data": saved
        }

    # Otherwise, query history for WhatsApp user
    inquiries = InquiryService.get_inquiries_by_phone(phone_val)
    return {
        "success": True,
        "event": "inquiry_history",
        "phone": phone_val,
        "total": len(inquiries),
        "data": inquiries
    }

@router.get(
    "/api/inquiry/health",
    summary="Inquiry Service Health",
    description="Check MongoDB connectivity for the inquiries collection."
)
async def inquiry_health():
    coll = get_inquiries_collection()
    is_connected = coll is not None
    return {
        "status": "healthy" if is_connected else "unhealthy",
        "collection": "inquiries",
        "database_connected": is_connected
    }

