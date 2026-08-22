import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

from database import get_inquiries_collection
from models.inquiry import InquiryCreate, InquiryResponseData

logger = logging.getLogger("inquiry_service")

class InquiryService:
    @staticmethod
    def create_inquiry(inquiry_input: InquiryCreate) -> Dict[str, Any]:
        """
        Validates, prepares, and securely stores an inquiry document in MongoDB.
        Returns the formatted saved inquiry record.
        """
        now = datetime.now(timezone.utc)
        
        doc = {
            "name": inquiry_input.name,
            "requirements": inquiry_input.requirements,
            "budget": inquiry_input.budget,
            "contactNumber": inquiry_input.contactNumber,
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
                "source": doc["source"],
                "createdAt": now.isoformat(),
                "updatedAt": now.isoformat()
            }
        except PyMongoError as e:
            logger.error(f"MongoDB error while inserting inquiry: {e}", exc_info=True)
            raise RuntimeError(f"Database error while saving inquiry: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while saving inquiry: {e}", exc_info=True)
            raise RuntimeError("An unexpected error occurred while processing the inquiry.")
