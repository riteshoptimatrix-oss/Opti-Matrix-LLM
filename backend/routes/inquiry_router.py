import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from models.inquiry import InquiryCreate, InquiryAPIResponse, InquiryResponseData
from services.inquiry_service import InquiryService
from database import get_inquiries_collection

logger = logging.getLogger("inquiry_router")

router = APIRouter(prefix="", tags=["Inquiries"])

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
