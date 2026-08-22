import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

from database import get_inquiries_collection
from models.inquiry import InquiryCreate, InquiryResponseData, normalize_phone_number

logger = logging.getLogger("inquiry_service")

# Indian Standard Time timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def format_datetime_ist(dt: Any) -> str:
    """Converts a datetime object or ISO string to formatted IST string (e.g. 'Aug 22, 2026 05:30 PM IST')."""
    if not dt:
        return "N/A"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return dt

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ist_dt = dt.astimezone(IST)
        return ist_dt.strftime("%b %d, %Y %I:%M %p IST")
        
    return str(dt)

class InquiryService:
    @staticmethod
    def create_inquiry(inquiry_input: InquiryCreate) -> Dict[str, Any]:
        """
        Validates, prepares, and securely stores an inquiry document in MongoDB.
        Returns the formatted saved inquiry record with IST timestamp.
        """
        now = datetime.now(IST)
        norm_phone = inquiry_input.normalizedPhone or normalize_phone_number(inquiry_input.contactNumber)
        
        doc = {
            "name": inquiry_input.name,
            "requirements": inquiry_input.requirements,
            "budget": inquiry_input.budget,
            "contactNumber": inquiry_input.contactNumber,
            "normalizedPhone": norm_phone,
            "source": inquiry_input.source or "api",
            "createdAt": now,
            "updatedAt": now
        }

        coll = get_inquiries_collection()
        if coll is None:
            logger.error("MongoDB inquiries collection is not available.")
            raise RuntimeError("Database connection is not available. Please verify MongoDB setup.")

        try:
            result = coll.insert_one(doc)
            doc_id = str(result.inserted_id)
            logger.info(f"Successfully stored new inquiry with ID: {doc_id}")

            return {
                "id": doc_id,
                "name": doc["name"],
                "requirements": doc["requirements"],
                "budget": doc["budget"],
                "contactNumber": doc["contactNumber"],
                "normalizedPhone": doc["normalizedPhone"],
                "source": doc["source"],
                "createdAt": format_datetime_ist(now),
                "updatedAt": format_datetime_ist(now)
            }
        except PyMongoError as e:
            logger.error(f"MongoDB error while inserting inquiry: {e}", exc_info=True)
            raise RuntimeError(f"Database error while saving inquiry: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while saving inquiry: {e}", exc_info=True)
            raise RuntimeError("An unexpected error occurred while processing the inquiry.")

    @staticmethod
    def get_inquiries_by_phone(phone_number: str) -> List[Dict[str, Any]]:
        """
        Fetches all inquiries matching a given phone number across all sources (PHP, WhatsApp, Chatbot, API).
        Uses exact matching, normalized digits matching, and last 10 digits regex matching.
        Formatted with IST timestamps.
        """
        coll = get_inquiries_collection()
        if coll is None:
            logger.error("MongoDB inquiries collection is not available.")
            return []

        clean_phone = phone_number.strip()
        digits = re.sub(r"\D", "", clean_phone)
        last_10 = digits[-10:] if len(digits) >= 10 else digits

        or_conditions = [
            {"contactNumber": clean_phone},
            {"contactNumber": digits},
            {"normalizedPhone": digits},
            {"normalizedPhone": last_10}
        ]

        if last_10:
            pattern = re.compile(re.escape(last_10) + r"$")
            or_conditions.extend([
                {"contactNumber": {"$regex": pattern}},
                {"normalizedPhone": {"$regex": pattern}}
            ])

        try:
            cursor = coll.find({"$or": or_conditions}).sort("createdAt", -1)
            results = []
            for doc in cursor:
                created_at_str = format_datetime_ist(doc.get("createdAt"))
                updated_at_str = format_datetime_ist(doc.get("updatedAt"))

                results.append({
                    "id": str(doc.get("_id")),
                    "name": doc.get("name", "N/A"),
                    "requirements": doc.get("requirements", "N/A"),
                    "budget": doc.get("budget", "N/A"),
                    "contactNumber": doc.get("contactNumber", "N/A"),
                    "normalizedPhone": doc.get("normalizedPhone", digits),
                    "source": doc.get("source", "unknown"),
                    "createdAt": created_at_str,
                    "updatedAt": updated_at_str
                })

            logger.info(f"Found {len(results)} inquiries for phone '{phone_number}' (last 10: '{last_10}')")
            return results

        except PyMongoError as e:
            logger.error(f"MongoDB error fetching inquiries by phone: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching inquiries by phone: {e}", exc_info=True)
            return []


