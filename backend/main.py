import os
import json
import logging
import joblib
import numpy as np
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ml_service")

# Global variables for model and response database
model = None
responses_db: Dict[str, List[str]] = {}
patterns_db: Dict[str, List[str]] = {}
sessions_db: Dict[str, Dict[str, Any]] = {}

# MongoDB Client
mongo_client = None
db = None
sessions_collection = None

import certifi

MONGODB_URI = os.getenv("MONGODB_URI")
if MONGODB_URI:
    try:
        mongo_client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
        try:
            db = mongo_client.get_database()
        except Exception:
            db = mongo_client.get_database("optimatrix_chat")
        sessions_collection = db["chat_sessions"]
        logger.info("MongoDB connected successfully for session storage.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")

def get_session(session_id: str) -> dict:
    if sessions_collection is not None:
        doc = sessions_collection.find_one({"session_id": session_id})
        if doc:
            return doc
        return {"session_id": session_id, "last_query": "", "last_intent": None}
    else:
        if session_id not in sessions_db:
            sessions_db[session_id] = {"last_query": "", "last_intent": None}
        return sessions_db[session_id]

def update_session(session_id: str, updates: dict):
    if sessions_collection is not None:
        updates["updated_at"] = datetime.utcnow()
        sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": updates},
            upsert=True
        )
    else:
        if session_id not in sessions_db:
            sessions_db[session_id] = {"last_query": "", "last_intent": None}
        sessions_db[session_id].update(updates)


# Configurable fallback message and confidence threshold
DEFAULT_FALLBACK_ANSWER = (
    "I'm sorry, I don't have enough information to answer that question accurately. "
    "Please contact Opti Matrix for more information."
)
FALLBACK_ANSWER = os.getenv("FALLBACK_MESSAGE", DEFAULT_FALLBACK_ANSWER)
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.15"))

def load_artifacts():
    global model, responses_db, patterns_db
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "model.pkl")
    response_path = os.path.join(base_dir, "response_data.json")
    patterns_path = os.path.join(base_dir, "patterns_data.json")

    # Load Model Pipeline
    if not os.path.exists(model_path):
        logger.error(f"model.pkl not found at {model_path}")
        raise FileNotFoundError(f"Model file not found at {model_path}")

    logger.info(f"Loading ML pipeline from {model_path}...")
    model = joblib.load(model_path)
    logger.info(f"Model loaded successfully with {len(getattr(model, 'classes_', []))} classes.")

    # Load Responses Mapping
    if os.path.exists(response_path):
        logger.info(f"Loading response mapping from {response_path}...")
        with open(response_path, "r", encoding="utf-8") as f:
            responses_db = json.load(f)
        logger.info(f"Response mapping loaded with {len(responses_db)} intents.")

    # Load Patterns Mapping
    if os.path.exists(patterns_path):
        with open(patterns_path, "r", encoding="utf-8") as f:
            patterns_db = json.load(f)
        logger.info(f"Patterns mapping loaded with {len(patterns_db)} intents.")
    else:
        logger.warning(f"{patterns_path} not found.")

    if not responses_db:
        logger.warning(f"{response_path} not found. Building fallback response store from JSON files...")
        import glob
        responses_db = {}
        for filepath in glob.glob(os.path.join(base_dir, "**", "*.json"), recursive=True):
            if "venv" in filepath or "__pycache__" in filepath or "node_modules" in filepath:
                continue
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            intent = item.get("intent")
                            resp = item.get("responses", [])
                            if intent and resp:
                                responses_db[intent] = resp
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load ML model and response mapping once
    try:
        load_artifacts()
    except Exception as e:
        logger.critical(f"Failed to initialize ML Service: {e}", exc_info=True)
    yield
    # Shutdown
    logger.info("ML Service shutting down.")

app = FastAPI(
    title="Opti Matrix ML Chatbot Service",
    version="1.0.0",
    description="Intent classification and response retrieval ML service powered by model.pkl and JSON_Data.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request / Response Models
class PredictRequest(BaseModel):
    question: str = Field(..., description="User's natural language question", min_length=1)
    session_id: Optional[str] = Field(default=None, description="Session ID for context tracking")

class PredictResponse(BaseModel):
    success: bool
    intent: Optional[str] = None
    answer: str
    confidence: float
    matched: bool
    suggested_questions: Optional[List[str]] = Field(default_factory=list)

def retrieve_approved_response(intent: str) -> Optional[str]:
    """Retrieve approved response from company dataset deterministically."""
    if not intent or intent not in responses_db:
        return None
    responses_list = responses_db[intent]
    if isinstance(responses_list, list) and len(responses_list) > 0:
        return responses_list[0]
    elif isinstance(responses_list, str) and responses_list.strip():
        return responses_list
    return None

@app.get("/")
def read_root():
    return {"message": "Welcome to Opti Matrix ML Chatbot Service API. Use /predict to query the model."}

@app.get("/health")
def health_check():
    return {
        "status": "healthy" if model is not None and len(responses_db) > 0 else "unhealthy",
        "model_loaded": model is not None,
        "classes_count": len(getattr(model, "classes_", [])),
        "intents_mapped": len(responses_db),
        "confidence_threshold": CONFIDENCE_THRESHOLD
    }

def get_dynamic_suggestions(intent: str) -> List[str]:
    if not intent:
        return ["What services do you offer?", "How can I contact you?", "Where is your office located?"]
    
    parts = intent.lower().replace("_", " ").split()
    raw_topic = parts[0] if parts else "general"
    if raw_topic == "faq" and len(parts) > 1:
        raw_topic = parts[1]
        
    mapping = {
        "nodejs": "Node.js", "nextjs": "Next.js", "reactjs": "React.js", "vuejs": "Vue.js",
        "php": "PHP", "ios": "iOS", "uiux": "UI/UX", "wordpress": "WordPress", "ecommerce": "E-commerce"
    }
    topic = mapping.get(raw_topic, raw_topic.capitalize())
    
    is_hiring = "hire" in intent or "hiring" in intent
    
    if is_hiring:
        return [
            f"What skills should I look for in a {topic} developer?",
            f"How much does it typically cost to hire a {topic} developer?",
            f"Can you help me create a job description for a {topic} developer?"
        ]
    elif raw_topic in ["contact", "greeting", "general", "company", "portfolio"]:
        return [
            "What services do you offer?",
            "Do you offer dedicated resource hiring models?",
            "Can you show me websites you have built?"
        ]
    elif raw_topic in ["payment", "legal", "security", "troubleshooting", "tech", "launch", "support"]:
        return [
            "Do I have to pay 100% upfront?",
            "Do you sign an NDA before we discuss my idea?",
            "Do you provide emergency support if my website goes down?"
        ]
    else:
        return [
            f"What are the benefits of using {topic} for my project?",
            f"Do you have a portfolio or case studies for {topic}?",
            f"I need to hire a {topic} developer"
        ]

@app.post("/predict", response_model=PredictResponse)
async def predict_intent(request: PredictRequest):
    """
    Classify the incoming question intent and return the company-approved answer.
    """
    if model is None:
        logger.error("Predict endpoint called but model is not loaded.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not initialized."
        )

    raw_question = request.question.strip()
    if not raw_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty."
        )

    session_id = request.session_id or "default"
    
    try:
        session_data = get_session(session_id)
        
        # Explicit Context Routing for "Hire" intents
        last_intent = session_data.get("last_intent")
        if "hire" in raw_question.lower() and last_intent:
            parts = last_intent.lower().replace("_", " ").split()
            topic = parts[0] if parts else None
            if topic:
                mapped_hire_intent = None
                for intent_name in responses_db.keys():
                    if ("hire" in intent_name or "hiring" in intent_name) and topic in intent_name:
                        mapped_hire_intent = intent_name
                        break
                
                if mapped_hire_intent:
                    logger.info(f"Hard-routing 'hire' query for topic '{topic}' to '{mapped_hire_intent}'")
                    update_session(session_id, {"last_intent": mapped_hire_intent})
                    
                    company_answer = retrieve_approved_response(mapped_hire_intent)
                    if company_answer:
                        return PredictResponse(
                            success=True,
                            intent=mapped_hire_intent,
                            answer=company_answer,
                            confidence=1.0,
                            matched=True,
                            suggested_questions=[]
                        )

        # 1. Try predicting with the raw question
        probs = model.predict_proba([raw_question])[0]
        max_idx = int(np.argmax(probs))
        confidence = float(probs[max_idx])
        predicted_intent = str(model.classes_[max_idx])

        logger.info(f"Query: '{raw_question[:60]}' -> Intent: {predicted_intent} (Conf: {confidence:.4f})")

        # Update session context
        update_session(session_id, {
            "last_query": raw_question,
            "last_intent": predicted_intent
        })

        # Confidence threshold check
        if confidence < CONFIDENCE_THRESHOLD:
            logger.info(f"Low confidence ({confidence:.4f} < {CONFIDENCE_THRESHOLD}). Returning fallback.")
            return PredictResponse(
                success=True,
                intent=None,
                answer=FALLBACK_ANSWER,
                confidence=round(confidence, 4),
                matched=False
            )

        # Retrieve company response
        company_answer = retrieve_approved_response(predicted_intent)
        if not company_answer:
            logger.warning(f"No response found for intent '{predicted_intent}'. Returning fallback.")
            return PredictResponse(
                success=True,
                intent=predicted_intent,
                answer=FALLBACK_ANSWER,
                confidence=round(confidence, 4),
                matched=False
            )

        # Generate follow-up questions using dynamic templates
        suggested_questions = get_dynamic_suggestions(predicted_intent)

        return PredictResponse(
            success=True,
            intent=predicted_intent,
            answer=company_answer,
            confidence=round(confidence, 4),
            matched=True,
            suggested_questions=suggested_questions
        )

    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        return PredictResponse(
            success=False,
            intent=None,
            answer=FALLBACK_ANSWER,
            confidence=0.0,
            matched=False
        )

# Backward-compatible /ask endpoint
@app.post("/ask")
async def ask_question(request: PredictRequest):
    result = await predict_intent(request)
    return {
        "intent": result.intent or "unknown",
        "answer": result.answer,
        "confidence": result.confidence,
        "matched": result.matched,
        "suggested_questions": result.suggested_questions
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
