import re
import logging
from typing import Optional, Dict, Any, Tuple
from models.inquiry import InquiryCreate
from services.inquiry_service import InquiryService

logger = logging.getLogger("inquiry_flow")

# Comprehensive patterns for English and Hinglish inquiry initiation
INQUIRY_START_PATTERNS = [
    # English development & build queries
    r"\b(develop|development|build|create|make|design|launch)\b.*?\b(website|web site|web app|webapp|software|application|app|portal|crm|erp|platform|project|store|ecommerce|e-commerce|shop)\b",
    r"\b(website|software|application|app|web app|portal|project|crm|erp|ecommerce)\b.*?\b(develop|development|create|build|maker|cost|price|quote|proposal)\b",
    
    # Hinglish queries ("banwana", "banwani", "karwana", "karna", "chahiye")
    r"\b(website|software|application|app|web app|portal|project)\b.*?\b(banwana|banwani|banwaana|banwaani|develop karwana|develop karna|bana do|chahiye)\b",
    r"\b(banwana|banwani|develop karwana|develop karna)\b.*?\b(website|software|app|portal|application|project)\b",
    
    # Requirement & Need queries
    r"\b(want|need|looking for|require|mujhe chahiye|hume chahiye)\b.*?\b(development|developer|agency|team to build|team to develop|website|software|app)\b",
    
    # General Inquiry & Quotation
    r"\b(project|service|development|website|software|app|business)\s+(inquiry|enquiry)\b",
    r"\b(inquiry|enquiry)\s+(for|about|regarding|karni|karna)\b",
    r"^(inquiry|enquiry|project inquiry|new inquiry)$",
    r"\b(get|request|need|chahiye)\s+(a\s+)?(quote|quotation|estimate|pricing for my project|price estimate)\b",
    r"\b(start|discuss)\s+(a\s+)?(new\s+)?project\b",
    r"\b(hire you|hire company|hire developers?)\s+(for|to)\s+(project|website|app|software|build)\b",
    r"\b(i want to|i would like to|want to)\s+(inquire|submit an inquiry|give project requirements)\b"
]

def is_inquiry_start_query(query: str) -> bool:
    """Checks if a user query is initiating a project/development inquiry."""
    q = query.lower().strip()
    
    # Exclude basic single words unless explicitly inquiry
    if q in ["inquiry", "enquiry", "project inquiry"]:
        return True
        
    if len(q) < 4:
        return False
        
    for pattern in INQUIRY_START_PATTERNS:
        if re.search(pattern, q):
            return True
            
    return False

def is_cancel_query(query: str) -> bool:
    q = query.lower().strip()
    return q in ["cancel", "cancel inquiry", "stop", "exit", "abort", "restart inquiry", "reset", "nahi chahiye", "cancel it"]

def extract_clean_name(text: str) -> str:
    """Cleans up conversational prefixes from name inputs."""
    cleaned = text.strip(" ,.-!_")
    
    # Strip common conversational patterns
    patterns = [
        r"^(my name is|i am|i'm|this is|name is|name:|mera naam hai|mera naam)\s+",
        r"\s+(here|this side|speaking)$",
        r"\s+hai$"
    ]
    for p in patterns:
        cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE).strip(" ,.-!_")
    
    # Title-case each word if all lowercase
    if cleaned.islower():
        cleaned = cleaned.title()
        
    return cleaned

def extract_clean_phone(text: str) -> Optional[str]:
    """Extracts a valid contact phone number from arbitrary text."""
    v = text.strip()
    
    # Direct check
    digits_only = re.sub(r"\D", "", v)
    if 7 <= len(digits_only) <= 15:
        # Check if entire string is reasonably formatted phone
        if re.match(r"^[+()0-9\s\-]+$", v):
            return v
            
        # Try extracting the phone segment from text like "my number is +91 9876543210"
        match = re.search(r"(\+?[0-9][0-9\s\-()]{6,16}[0-9])", v)
        if match:
            extracted = match.group(1).strip()
            ex_digits = re.sub(r"\D", "", extracted)
            if 7 <= len(ex_digits) <= 15:
                return extracted
                
    return None

def process_inquiry_turn(
    session_id: str,
    user_query: str,
    session_data: Dict[str, Any]
) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Processes a conversation turn in the step-by-step inquiry collection flow.
    Returns:
        (bot_response_text, session_updates_dict, saved_inquiry_data_or_None)
        If not an inquiry turn, returns (None, None, None).
    """
    inquiry_state = session_data.get("inquiry_state")
    inquiry_draft = session_data.get("inquiry_draft", {}) or {}
    q = user_query.strip()

    # If user wants to cancel an active inquiry flow
    if inquiry_state and is_cancel_query(q):
        updates = {
            "inquiry_state": None,
            "inquiry_draft": {}
        }
        resp = "❌ Your inquiry process has been cancelled. Let me know if there's anything else I can help you with!"
        return resp, updates, None

    # Step 0: Inquiry Initiation
    if not inquiry_state:
        if is_inquiry_start_query(q):
            updates = {
                "inquiry_state": "awaiting_name",
                "inquiry_draft": {
                    "initial_intent": q
                }
            }
            resp = (
                "I would love to assist you with your development project! 🚀\n\n"
                "To understand your requirements and connect you with our technical team, "
                "I will collect a few quick details step-by-step.\n\n"
                "First, **what is your full name?**"
            )
            return resp, updates, None
        else:
            return None, None, None

    # Step 1: Collecting Name
    if inquiry_state == "awaiting_name":
        clean_name = extract_clean_name(q)
        if len(clean_name) < 2 or not re.search(r"[a-zA-Z]", clean_name):
            resp = "Please enter your valid name (at least 2 characters):"
            return resp, {"inquiry_state": "awaiting_name"}, None
            
        inquiry_draft["name"] = clean_name
        updates = {
            "inquiry_state": "awaiting_requirements",
            "inquiry_draft": inquiry_draft
        }
        resp = (
            f"Nice to meet you, **{clean_name}**! 👋\n\n"
            "Could you please describe your **project requirements**? "
            "(e.g., type of website, mobile app, software, key features, or technologies you prefer)"
        )
        return resp, updates, None

    # Step 2: Collecting Requirements
    if inquiry_state == "awaiting_requirements":
        req_clean = q.strip()
        if len(req_clean) < 5:
            resp = "Please share a little more detail about your project requirements (at least a brief description):"
            return resp, {"inquiry_state": "awaiting_requirements"}, None
            
        inquiry_draft["requirements"] = req_clean
        updates = {
            "inquiry_state": "awaiting_budget",
            "inquiry_draft": inquiry_draft
        }
        resp = (
            "Got it! That sounds like an exciting project. 💼\n\n"
            "What is your **estimated or preferred budget** for this project? "
            "(e.g., $1,000 - $3,000, 50,000 INR, or Flexible)"
        )
        return resp, updates, None

    # Step 3: Collecting Budget
    if inquiry_state == "awaiting_budget":
        budget_clean = q.strip()
        if len(budget_clean) < 2:
            resp = "Please provide your approximate budget or specify if it is 'Flexible':"
            return resp, {"inquiry_state": "awaiting_budget"}, None
            
        inquiry_draft["budget"] = budget_clean
        updates = {
            "inquiry_state": "awaiting_contact",
            "inquiry_draft": inquiry_draft
        }
        resp = (
            "Thank you! Almost done. 📱\n\n"
            "Please share your **contact number** (with country code if applicable) so our team can reach out to you."
        )
        return resp, updates, None

    # Step 4: Collecting Contact Number & Final Submission to MongoDB
    if inquiry_state == "awaiting_contact":
        valid_phone = extract_clean_phone(q)
        if not valid_phone:
            resp = (
                "⚠️ Please provide a valid phone or mobile number with 7 to 15 digits "
                "(e.g., +91 9876543210 or +1 234 567 8900):"
            )
            return resp, {"inquiry_state": "awaiting_contact"}, None
            
        inquiry_draft["contactNumber"] = valid_phone
        
        # Prepare and validate Pydantic model
        try:
            inquiry_model = InquiryCreate(
                name=inquiry_draft["name"],
                requirements=inquiry_draft["requirements"],
                budget=inquiry_draft["budget"],
                contactNumber=inquiry_draft["contactNumber"],
                source="chatbot"
            )
            
            # Save into MongoDB
            saved_doc = InquiryService.create_inquiry(inquiry_model)
            
            # Reset inquiry state in session
            updates = {
                "inquiry_state": None,
                "inquiry_draft": {}
            }
            
            name = inquiry_draft["name"]
            reqs = inquiry_draft["requirements"]
            budget = inquiry_draft["budget"]
            contact = inquiry_draft["contactNumber"]
            
            resp = (
                "🎉 **Project Inquiry Submitted Successfully!**\n\n"
                f"Thank you, **{name}**! We have safely recorded your project inquiry in our database:\n\n"
                f"• **Name:** {name}\n"
                f"• **Requirements:** {reqs}\n"
                f"• **Budget:** {budget}\n"
                f"• **Contact Number:** {contact}\n\n"
                "Our development and solutions team at **Opti Matrix** will review your requirements "
                "and get in touch with you shortly. 🚀\n\n"
                "Feel free to ask if you have any other questions in the meantime!"
            )
            
            return resp, updates, saved_doc
            
        except Exception as e:
            logger.error(f"Failed to complete inquiry saving: {e}", exc_info=True)
            resp = (
                "We encountered a temporary issue while saving your inquiry to the database. "
                "Please try again or contact us directly at info@opti-matrix.com."
            )
            # Retain state so user can re-submit
            return resp, {"inquiry_state": "awaiting_contact"}, None

    return None, None, None
