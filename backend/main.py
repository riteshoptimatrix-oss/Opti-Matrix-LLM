import os
import json
import random
import logging
import joblib
import numpy as np
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import re

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

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
        mongo_client.admin.command('ping')
        try:
            db = mongo_client.get_database()
        except Exception:
            db = mongo_client.get_database("optimatrix_chat")
        sessions_collection = db["chat_sessions"]
        # Add TTL index for automatic cleanup of abandoned sessions (expires after 24 hours)
        sessions_collection.create_index("updated_at", expireAfterSeconds=86400)
        logger.info("MongoDB connected successfully for session storage. TTL index ensured.")
    except Exception as e:
        logger.error("Failed to connect to MongoDB. Check credentials, URI format, and network connectivity.")

def get_session(session_id: str) -> dict:
    if sessions_collection is not None:
        doc = sessions_collection.find_one({"session_id": session_id})
        if doc:
            if "chat_history" not in doc:
                doc["chat_history"] = []
            return doc
        return {"session_id": session_id, "last_query": "", "last_intent": None, "chat_history": []}
    else:
        if session_id not in sessions_db:
            sessions_db[session_id] = {"last_query": "", "last_intent": None, "chat_history": []}
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
            sessions_db[session_id] = {"last_query": "", "last_intent": None, "chat_history": []}
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
        pool = [
            "What services do you offer?", 
            "How can I contact you?", 
            "Where is your office located?",
            "Can you show me your portfolio?",
            "How long have you been in business?"
        ]
        return random.sample(pool, min(3, len(pool)))
        
    if any(keyword in intent.lower() for keyword in ["greeting", "bye", "thank", "welcome"]):
        return []
    
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
        if topic.lower() == "developer":
            pool = [
                "What skills should I look for when hiring a developer?",
                "How much does it typically cost to hire a developer?",
                "Can you help me create a job description for a developer?",
                "Are your developers experienced?",
                "Do you provide dedicated developers?",
                "What hiring models do you offer for developers?"
            ]
        else:
            pool = [
                f"What skills should I look for in a {topic} developer?",
                f"How much does it typically cost to hire a {topic} developer?",
                f"Can you help me create a job description for a {topic} developer?",
                f"Are your {topic} developers experienced?",
                f"Do you provide dedicated {topic} developers?",
                f"What hiring models do you offer for {topic}?"
            ]
        return random.sample(pool, min(3, len(pool)))
    elif raw_topic in ["contact", "greeting", "greetings", "general", "company", "portfolio", "career", "ceo", "social", "privacy", "benefits", "technology", "process", "migration"]:
        pool = [
            "What services do you offer?",
            "Do you offer dedicated resource hiring models?",
            "Can you show me websites you have built?",
            "Where is your head office?",
            "What industries do you serve?",
            "How can I get a quote?"
        ]
        return random.sample(pool, min(3, len(pool)))
    elif raw_topic in ["payment", "legal", "security", "troubleshooting", "tech", "launch", "support"]:
        pool = [
            "Do I have to pay 100% upfront?",
            "Do you sign an NDA before we discuss my idea?",
            "Do you provide emergency support if my website goes down?",
            "What payment methods do you accept?",
            "How do you ensure data security?",
            "What is your refund policy?"
        ]
        return random.sample(pool, min(3, len(pool)))
    else:
        pool = [
            f"What are the benefits of using {topic} for my project?",
            f"Do you have a portfolio or case studies for {topic}?",
            f"Why should I choose {topic}?",
            f"Can you migrate my existing app to {topic}?",
            f"What is the development process for {topic}?"
        ]
        return random.sample(pool, min(3, len(pool)))

def handle_chat_history_intent(query: str, chat_history: list) -> Optional[str]:
    """
    Priority Rule: Chat History Intent has higher priority than the general knowledge base.
    Detects and responds to queries about conversation history using the actual session chat_history.
    """
    query_lower = query.lower().strip()
    
    # ── Auto-Correct Common Spelling Errors ────────────────────────────────────
    # Safely corrects common typos so the regex engine doesn't break
    typo_map = {
        "cht": "chat", "chaat": "chat", "cahat": "chat", "chatt": "chat",
        "mesage": "message", "messge": "message", "mesagge": "message", "msg": "message",
        "lsat": "last", "lst": "last", "lasst": "last",
        "previus": "previous", "prev": "previous", "prevoius": "previous",
        "histroy": "history", "histry": "history",
        "qstn": "question", "ques": "question", "qestion": "question",
        "frist": "first", "frst": "first",
        "secnd": "second", "scnd": "second",
        "thrd": "third", "thrid": "third"
    }
    try:
        from thefuzz import process, fuzz
        crucial_words = ['chat', 'message', 'prompt', 'question', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'last', 'previous', 'before', 'history', 'complete']
        words = query_lower.split()
        corrected_words = []
        for w in words:
            # 1. Check explicit map first
            if w in typo_map:
                corrected_words.append(typo_map[w])
                continue
            # 2. Fuzzy match for longer words to avoid false positives on short words like "that"
            if len(w) > 4:
                match = process.extractOne(w, crucial_words, scorer=fuzz.ratio)
                if match and match[1] >= 85:
                    corrected_words.append(match[0])
                    continue
            corrected_words.append(w)
        query_lower = " ".join(corrected_words)
    except ImportError:
        # Fallback to pure dictionary map if thefuzz isn't available
        query_lower = " ".join([typo_map.get(w, w) for w in query_lower.split()])

    # ── Pattern Detection ──────────────────────────────────────────────────────
    positional_words = r"(?:first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|sixth|6th|seventh|7th|eighth|8th|ninth|9th|tenth|10th|\d+(?:st|nd|rd|th))"
    history_patterns = [
      r"complete chat history",
r"chat history",
r"my chats",
r"list of my chats",
r"show my chats",
r"show my chat history",
r"show chat history",
r"view my chats",
r"view chat history",
r"get my chats",
r"get my chat history",
r"retrieve my chats",
r"retrieve chat history",
r"conversation history",
r"my conversation history",
r"show my conversation history",
r"view my conversation history",
r"list my conversations",
r"show my conversations",
r"my conversations",
r"all my chats",
r"all my conversations",
r"previous chats",
r"past chats",
r"old chats",
r"recent chats",
r"chat records",
r"my chat records",
r"conversation records",
r"my conversation records",
r"all chat history",
r"entire chat history",
r"full chat history",
r"complete conversation history",
r"full conversation history",
r"entire conversation history",
r"history of my chats",
r"history of my conversations",
r"what did we chat about",
r"what have we chatted about",
r"show everything we talked about",
r"show all my conversations",
r"show all my chats",
        
        # Positional exact matches
        rf"\b({positional_words})\b (chat|message|prompt|question)",
        rf"(what (is|was)|show me) my ({positional_words}) (chat|message|prompt|question)",
        rf"what did i ask (you )?({positional_words})",
        rf"asked? ({positional_words})",
        
        # From the end generic (e.g., 2nd last, last 2nd)
        rf"({positional_words})[ -]last (chat|message|prompt|question)",
        rf"last ({positional_words}) (chat|message|prompt|question)",
        rf"(what (is|was)|show me) my ({positional_words})[ -]last (chat|message|prompt|question)",
        rf"(what (is|was)|show me) my last ({positional_words}) (chat|message|prompt|question)",
        r"what did i ask before my last",
        r"before my last (question|message|prompt|chat)",
        
        # simple last / previous
        r"\blast\b (chat|message|prompt|question)",
        r"\bprevious\b (chat|message|prompt|question)",
        r"(show me|what (is|was)) my (last|previous) (chat|message|prompt|question)",
        r"what did i ask (you )?before",
        r"what did i (ask|say) before",
        r"asked? you before"
    ]

    is_history_intent = any(re.search(p, query_lower) for p in history_patterns)
    if not is_history_intent:
        return None

    # ── Extract user-only messages ────────────────────────────────────────────
    user_messages = [msg["content"] for msg in chat_history if msg.get("role") == "user"]
    unavailable_msg = (
        "I currently only have access to the conversation history within this active session. "
        "I cannot retrieve older or deleted chats."
    )

    # ── Helper to parse Nth string ─────────────────────────────────────────────
    def get_nth(word: str) -> Optional[int]:
        if not word: return None
        word = word.lower().strip()
        mapping = {
            "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3,
            "fourth": 4, "4th": 4, "fifth": 5, "5th": 5, "sixth": 6, "6th": 6,
            "seventh": 7, "7th": 7, "eighth": 8, "8th": 8, "ninth": 9, "9th": 9,
            "tenth": 10, "10th": 10
        }
        if word in mapping: return mapping[word]
        m = re.match(r"^(\d+)(?:st|nd|rd|th)?$", word)
        if m: return int(m.group(1))
        return None

    # ── Complete chat history ─────────────────────────────────────────────────
    if "complete chat history" in query_lower:
        if not chat_history:
            return unavailable_msg
        formatted_history = ["Here is our conversation history for this session:\n"]
        for msg in chat_history:
            role = "You" if msg["role"] == "user" else "Opti Matrix"
            formatted_history.append(f"**{role}:** {msg['content']}")
        return "\n\n".join(formatted_history)

    # ── My chats (list user messages only) ────────────────────────────────────
    if (
        query_lower == "my chats"
        or "list my chats" in query_lower
        or re.search(r"(show me|what (is|are)) my chats", query_lower)
    ):
        if not user_messages:
            return unavailable_msg
        formatted = ["Here are the questions and messages you have sent in this session:\n"] + [
            f"{i+1}. {m}" for i, m in enumerate(user_messages)
        ]
        return "\n".join(formatted)

    # ── Position Mapping ──────────────────────────────────────────────────────

    # Nth last (e.g. 2nd last, last 5th)
    nth_last_match = re.search(rf"({positional_words})[ -]last|last ({positional_words})", query_lower)
    if nth_last_match:
        word = nth_last_match.group(1) or nth_last_match.group(2)
        idx = get_nth(word)
        if idx and len(user_messages) >= idx:
            return f"Your {word}-to-last message was:\n\n**\"{user_messages[-idx]}\"**"
        return unavailable_msg

    # Before my last (2nd last)
    if "before my last" in query_lower:
        if len(user_messages) >= 2:
            return f"The message you sent just before your last one was:\n\n**\"{user_messages[-2]}\"**"
        return unavailable_msg

    # Last / previous / asked before
    if re.search(r"\b(last|previous)\b", query_lower) or "before" in query_lower:
        if user_messages:
            return f"Your last message was:\n\n**\"{user_messages[-1]}\"**"
        return unavailable_msg

    # Nth (from the start)
    nth_match = re.search(rf"\b({positional_words})\b", query_lower)
    if nth_match:
        word = nth_match.group(1)
        idx = get_nth(word)
        if idx:
            if idx == 1 and user_messages:
                return f"The very first message you sent in this session was:\n\n**\"{user_messages[0]}\"**"
            elif len(user_messages) >= idx:
                return f"Your {word} message in this session was:\n\n**\"{user_messages[idx-1]}\"**"
            return unavailable_msg

    # Generic fallback
    return unavailable_msg
            
def log_and_create_response(session_id: str, question: str, intent: Optional[str], answer: str, confidence: float, matched: bool, suggested_questions: List[str] = None):
    if suggested_questions is None:
        suggested_questions = []
    
    session_data = get_session(session_id)
    chat_history = session_data.get("chat_history", [])
    
    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": answer})
    
    update_session(session_id, {
        "last_query": question,
        "last_intent": intent,
        "chat_history": chat_history
    })
    
    return PredictResponse(
        success=True,
        intent=intent,
        answer=answer,
        confidence=confidence,
        matched=matched,
        suggested_questions=suggested_questions
    )

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
        chat_history = session_data.get("chat_history", [])
        
        # Priority Rule: Chat History Intent has higher priority
        chat_history_response = handle_chat_history_intent(raw_question, chat_history)
        if chat_history_response:
            return log_and_create_response(
                session_id=session_id,
                question=raw_question,
                intent="chat_history_intent",
                answer=chat_history_response,
                confidence=1.0,
                matched=True,
                suggested_questions=[]
            )
        
        # Explicit Context Routing for "Hire" intents
        last_intent = session_data.get("last_intent")
        
        # Don't route candidate phrases to client hiring logic
        candidate_phrases = ["hire me", "can you hire me", "please hire me"]
        is_candidate = any(phrase in raw_question.lower() for phrase in candidate_phrases)

        if "hire" in raw_question.lower() and last_intent and not is_candidate:
            parts = last_intent.lower().replace("_", " ").split()
            # Extract meaningful topic by ignoring common prefix/suffix words
            ignore_words = {"career", "service", "dev", "development", "developer", "design", "designer", "general"}
            tech_keywords = [w for w in parts if w not in ignore_words]
            topic = tech_keywords[0] if tech_keywords else parts[0] if parts else None
            
            if topic:
                mapped_hire_intent = None
                for intent_name in responses_db.keys():
                    if ("hire" in intent_name or "hiring" in intent_name) and topic in intent_name:
                        mapped_hire_intent = intent_name
                        break
                
                # Fallback to web developer hiring if no specific tech matched but context was web/career
                if not mapped_hire_intent and ("web" in last_intent.lower() or topic == "career"):
                    mapped_hire_intent = "hire_web_developer_direct"

                if mapped_hire_intent:
                    logger.info(f"Hard-routing 'hire' query for topic '{topic}' to '{mapped_hire_intent}'")
                    
                    company_answer = retrieve_approved_response(mapped_hire_intent)
                    if company_answer:
                        return log_and_create_response(
                            session_id=session_id,
                            question=raw_question,
                            intent=mapped_hire_intent,
                            answer=company_answer,
                            confidence=1.0,
                            matched=True
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
            return log_and_create_response(
                session_id=session_id,
                question=raw_question,
                intent=None,
                answer=FALLBACK_ANSWER,
                confidence=round(confidence, 4),
                matched=False
            )

        # Retrieve company response
        company_answer = retrieve_approved_response(predicted_intent)
        if not company_answer:
            logger.warning(f"No response found for intent '{predicted_intent}'. Returning fallback.")
            return log_and_create_response(
                session_id=session_id,
                question=raw_question,
                intent=predicted_intent,
                answer=FALLBACK_ANSWER,
                confidence=round(confidence, 4),
                matched=False
            )

        # Generate follow-up questions using dynamic templates
        suggested_questions = get_dynamic_suggestions(predicted_intent)

        return log_and_create_response(
            session_id=session_id,
            question=raw_question,
            intent=predicted_intent,
            answer=company_answer,
            confidence=round(confidence, 4),
            matched=True,
            suggested_questions=suggested_questions
        )

    except (PyMongoError, ServerSelectionTimeoutError) as db_err:
        logger.error("Database connection error during prediction.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error. Please try again later."
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

@app.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    session_data = get_session(session_id)
    return {
        "session_id": session_id,
        "chat_history": session_data.get("chat_history", [])
    }

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Explicitly clear a session and its history."""
    if sessions_collection is not None:
        result = sessions_collection.delete_one({"session_id": session_id})
        deleted = result.deleted_count > 0
    else:
        deleted = sessions_db.pop(session_id, None) is not None
        
    if deleted:
        return {"success": True, "message": f"Session {session_id} cleared successfully."}
    else:
        raise HTTPException(status_code=404, detail="Session not found.")
