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

MONGODB_URI = os.getenv("MONGODB_URI")
if MONGODB_URI:
    try:
        mongo_client = MongoClient(MONGODB_URI)
        db = mongo_client.get_database() # Gets default DB from URI
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

        # 1. Try predicting with the raw question first
        probs_raw = model.predict_proba([raw_question])[0]
        max_idx_raw = int(np.argmax(probs_raw))
        conf_raw = float(probs_raw[max_idx_raw])
        intent_raw = str(model.classes_[max_idx_raw])

        # 2. Try predicting with the augmented question (history + current)
        augmented_question = f"{session_data.get('last_query', '')} {raw_question}".strip()
        probs_aug = model.predict_proba([augmented_question])[0]
        max_idx_aug = int(np.argmax(probs_aug))
        conf_aug = float(probs_aug[max_idx_aug])
        intent_aug = str(model.classes_[max_idx_aug])

        # 3. Choose the best intent based on confidence and contextual heuristics
        # If the raw query has high confidence, it's likely a complete thought/new topic.
        # If it's low confidence, or the augmented query is significantly more confident, use context.
        if conf_raw > 0.5 and conf_raw >= conf_aug - 0.1:
            best_intent = intent_raw
            best_conf = conf_raw
            logger.info(f"Using RAW query. Intent: {best_intent} (Conf: {best_conf:.4f})")
            update_session(session_id, {"last_query": raw_question})
        elif session_data.get("last_query"):
            # Penalize the augmented intent if it just repeats the exact same topic as before
            # to force it to answer the follow-up question (e.g. hiring) rather than repeating the intro
            if intent_aug == session_data.get("last_intent") and conf_aug > 0.0:
                # Find the second best intent
                max_idx_aug_2 = np.argsort(probs_aug)[-2]
                if probs_aug[max_idx_aug_2] > CONFIDENCE_THRESHOLD:
                    intent_aug = str(model.classes_[max_idx_aug_2])
                    conf_aug = float(probs_aug[max_idx_aug_2])

            best_intent = intent_aug
            best_conf = conf_aug
            logger.info(f"Using AUGMENTED query ('{augmented_question}'). Intent: {best_intent} (Conf: {best_conf:.4f})")
            # Do NOT overwrite last_query here, so we retain the main topic!
        else:
            best_intent = intent_raw
            best_conf = conf_raw
            update_session(session_id, {"last_query": raw_question})

        confidence = best_conf
        predicted_intent = best_intent

        # Update session context
        update_session(session_id, {"last_intent": predicted_intent})

        logger.info(f"Query: '{raw_question[:60]}' -> Intent: {predicted_intent} (Conf: {confidence:.4f})")

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

        # Generate follow-up questions
        suggested_questions = []
        if patterns_db and predicted_intent:
            parts = predicted_intent.lower().replace("_", " ").split()
            # Try to get the primary technology/topic (first keyword usually)
            topic = parts[0] if parts else None
            if topic:
                candidate_questions = []
                for intent, pats in patterns_db.items():
                    if intent != predicted_intent and topic in intent.lower():
                        # Pick a random pattern from this related intent
                        import random
                        if pats:
                            candidate_questions.append(random.choice(pats))
                
                if candidate_questions:
                    import random
                    random.shuffle(candidate_questions)
                    # Limit to 3 unique suggestions
                    suggested_questions = list(set(candidate_questions))[:3]

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
