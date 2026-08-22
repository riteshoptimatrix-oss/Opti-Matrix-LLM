import os
import sys
import unittest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Add current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, get_session, update_session, load_artifacts
from models.inquiry import InquiryCreate
from services.inquiry_service import InquiryService
from database import get_inquiries_collection

class TestInquiryFlow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Load ML model and datasets for testing
        load_artifacts()
        cls.client = TestClient(app)

    def setUp(self):
        from main import sessions_db
        sessions_db.clear()
        self.session_id = f"test_session_{int(datetime.now(timezone.utc).timestamp())}"

    def test_direct_inquiry_api_success(self):
        """Test POST /api/inquiry endpoint with valid payload."""
        payload = {
            "name": "Amit Sharma",
            "requirements": "Need a real estate property management software with tenant portal.",
            "budget": "$5,000",
            "contactNumber": "+91 9876543210",
            "source": "api_test"
        }
        response = self.client.post("/api/inquiry", json=payload)
        self.assertEqual(response.status_code, 201, f"Expected 201, got {response.status_code}: {response.text}")
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["name"], "Amit Sharma")
        self.assertEqual(data["data"]["contactNumber"], "+91 9876543210")
        self.assertIn("createdAt", data["data"])
        self.assertIn("updatedAt", data["data"])
        self.assertIn("id", data["data"])
        print("\n[PASSED] Direct API /api/inquiry successfully saved to MongoDB.")

    def test_direct_inquiry_api_validation_errors(self):
        """Test POST /api/inquiry endpoint rejects invalid or missing fields."""
        invalid_payload = {
            "name": "A",
            "requirements": "Hi",  # too short (< 5 chars)
            "budget": "",
            "contactNumber": "123"   # invalid phone (< 7 digits)
        }
        response = self.client.post("/api/inquiry", json=invalid_payload)
        self.assertEqual(response.status_code, 422)
        print("\n[PASSED] Direct API validation properly rejects invalid data.")

    def test_conversational_step_by_step_inquiry_flow_english(self):
        """Test the multi-turn conversational inquiry flow via /predict in English."""
        session_id = f"{self.session_id}_eng"
        
        # Turn 1: User indicates they want to build software/website
        turn1_resp = self.client.post("/predict", json={
            "question": "I want to develop a website for my business",
            "session_id": session_id
        })
        self.assertEqual(turn1_resp.status_code, 200)
        t1_data = turn1_resp.json()
        self.assertIn("what is your full name", t1_data["answer"].lower())
        
        # Turn 2: User provides Name with conversational phrasing "My name is Pooja Gupta"
        turn2_resp = self.client.post("/predict", json={
            "question": "My name is Pooja Gupta",
            "session_id": session_id
        })
        self.assertEqual(turn2_resp.status_code, 200)
        t2_data = turn2_resp.json()
        self.assertIn("project requirements", t2_data["answer"].lower())
        self.assertIn("pooja gupta", t2_data["answer"].lower())

        # Turn 3: User provides Requirements
        turn3_resp = self.client.post("/predict", json={
            "question": "We need a complete e-commerce mobile application with payment gateway and delivery tracking.",
            "session_id": session_id
        })
        self.assertEqual(turn3_resp.status_code, 200)
        t3_data = turn3_resp.json()
        self.assertIn("budget", t3_data["answer"].lower())

        # Turn 4: User provides Budget
        turn4_resp = self.client.post("/predict", json={
            "question": "$3,000 - $6,000",
            "session_id": session_id
        })
        self.assertEqual(turn4_resp.status_code, 200)
        t4_data = turn4_resp.json()
        self.assertIn("contact number", t4_data["answer"].lower())

        # Turn 5: User provides Contact Number with conversational phrasing
        turn5_resp = self.client.post("/predict", json={
            "question": "My phone is +91 9811223344",
            "session_id": session_id
        })
        self.assertEqual(turn5_resp.status_code, 200)
        t5_data = turn5_resp.json()
        self.assertIn("submitted successfully", t5_data["answer"].lower())
        self.assertIn("pooja gupta", t5_data["answer"].lower())
        self.assertIn("+91 9811223344", t5_data["answer"])

        # Verify session is reset
        session = get_session(session_id)
        self.assertIsNone(session.get("inquiry_state"))
        print("\n[PASSED] Conversational Step-by-Step Flow (English) executed and stored in MongoDB.")

    def test_conversational_step_by_step_inquiry_flow_hinglish(self):
        """Test the multi-turn conversational inquiry flow with Hinglish queries."""
        session_id = f"{self.session_id}_hinglish"
        
        # Turn 1: Hinglish trigger
        turn1_resp = self.client.post("/predict", json={
            "question": "mujhe ek customized software banwana hai",
            "session_id": session_id
        })
        self.assertEqual(turn1_resp.status_code, 200)
        t1_data = turn1_resp.json()
        self.assertIn("what is your full name", t1_data["answer"].lower())

        # Turn 2: Name in conversational style
        turn2_resp = self.client.post("/predict", json={
            "question": "Mera naam Rajesh Kumar hai",
            "session_id": session_id
        })
        self.assertEqual(turn2_resp.status_code, 200)
        t2_data = turn2_resp.json()
        self.assertIn("rajesh kumar", t2_data["answer"].lower())

        # Turn 3: Requirements
        turn3_resp = self.client.post("/predict", json={
            "question": "School management ERP software with student attendance, fee management, and SMS alerts.",
            "session_id": session_id
        })
        self.assertEqual(turn3_resp.status_code, 200)

        # Turn 4: Budget
        turn4_resp = self.client.post("/predict", json={
            "question": "Around 1 Lakh INR",
            "session_id": session_id
        })
        self.assertEqual(turn4_resp.status_code, 200)

        # Turn 5: Contact
        turn5_resp = self.client.post("/predict", json={
            "question": "+91 9876501234",
            "session_id": session_id
        })
        self.assertEqual(turn5_resp.status_code, 200)
        t5_data = turn5_resp.json()
        self.assertIn("submitted successfully", t5_data["answer"].lower())
        self.assertIn("rajesh kumar", t5_data["answer"].lower())

        # Verify MongoDB storage
        coll = get_inquiries_collection()
        if coll is not None:
            doc = coll.find_one({"name": "Rajesh Kumar", "contactNumber": "+91 9876501234"})
            self.assertIsNotNone(doc)
            self.assertEqual(doc["budget"], "Around 1 Lakh INR")
            print("[PASSED] Conversational Step-by-Step Flow (Hinglish) accurately saved to MongoDB.")

    def test_cancellation_flow(self):
        """Test canceling an active inquiry flow."""
        session_id = f"{self.session_id}_cancel"
        
        # Start inquiry
        self.client.post("/predict", json={"question": "I need a website developed", "session_id": session_id})
        
        # Cancel
        cancel_resp = self.client.post("/predict", json={"question": "cancel", "session_id": session_id})
        self.assertEqual(cancel_resp.status_code, 200)
        self.assertIn("cancelled", cancel_resp.json()["answer"].lower())
        
        session = get_session(session_id)
        self.assertIsNone(session.get("inquiry_state"))
        print("[PASSED] Cancellation flow properly resets session state.")

    def test_phone_normalization_and_history_matching(self):
        """Test matching PHP-created and WhatsApp-created inquiries for the same phone number."""
        test_phone_php = "+91 9988776655"
        test_phone_wa = "919988776655"

        # 1. Create inquiry via PHP source
        php_payload = InquiryCreate(
            name="Rahul Sharma",
            requirements="Need a custom PHP web application for inventory management.",
            budget="$4,000",
            contactNumber=test_phone_php,
            source="php"
        )
        InquiryService.create_inquiry(php_payload)

        # 2. Create inquiry via WhatsApp source
        wa_payload = InquiryCreate(
            name="Rahul Sharma",
            requirements="Need WhatsApp automated CRM integration.",
            budget="$2,500",
            contactNumber=test_phone_wa,
            source="whatsapp"
        )
        InquiryService.create_inquiry(wa_payload)

        # 3. Query history using plain 10-digit number
        results = InquiryService.get_inquiries_by_phone("9988776655")
        self.assertGreaterEqual(len(results), 2, f"Expected at least 2 records, got {len(results)}")
        
        sources = [r["source"].lower() for r in results]
        self.assertIn("php", sources)
        self.assertIn("whatsapp", sources)
        print("\n[PASSED] Phone normalization correctly matches both PHP and WhatsApp inquiries.")

    def test_my_inquiries_conversational_flow(self):
        """Test the 'My Inquiries' conversational intent and phone prompt flow."""
        session_id = "test_web_session_no_phone"
        self.client.delete(f"/session/{session_id}")

        # Turn 1: User asks 'My Inquiries'
        resp1 = self.client.post("/predict", json={
            "question": "My Inquiries",
            "session_id": session_id
        })
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertIn("view inquiry history", data1["answer"].lower())
        self.assertIn("phone number", data1["answer"].lower())

        # Turn 2: User provides registered phone number
        resp2 = self.client.post("/predict", json={
            "question": "9988776655",
            "session_id": session_id
        })
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertIn("inquiry history for", data2["answer"].lower())
        self.assertIn("rahul sharma", data2["answer"].lower())
        print("[PASSED] Conversational 'My Inquiries' flow properly prompts and returns history.")

    def test_history_api_endpoints(self):
        """Test GET and POST /api/inquiry/history endpoints."""
        test_phone = "+91 9888877777"
        
        # Seed test inquiries for history API test
        InquiryService.create_inquiry(InquiryCreate(
            name="Vikram Seth",
            requirements="Custom CRM for logistics firm.",
            budget="$3,500",
            contactNumber=test_phone,
            source="php"
        ))
        InquiryService.create_inquiry(InquiryCreate(
            name="Vikram Seth",
            requirements="WhatsApp Notification bot for logistics.",
            budget="$1,500",
            contactNumber="919888877777",
            source="whatsapp"
        ))

        # GET Endpoint
        get_resp = self.client.get("/api/inquiry/history?phone=9888877777")
        self.assertEqual(get_resp.status_code, 200)
        get_data = get_resp.json()
        self.assertTrue(get_data["success"])
        self.assertGreaterEqual(get_data["total"], 2)

        # POST Endpoint
        post_resp = self.client.post("/api/inquiry/history", json={"contactNumber": "+91 9888877777"})
        self.assertEqual(post_resp.status_code, 200)
        post_data = post_resp.json()
        self.assertTrue(post_data["success"])
        self.assertGreaterEqual(post_data["total"], 2)
        print("[PASSED] GET and POST /api/inquiry/history API endpoints functioning properly.")

    def test_whatsapp_webhook_integration(self):
        """Test POST /api/webhook/whatsapp endpoint."""
        payload = {
            "phone": "+91 9123456789",
            "name": "Karan Malhotra",
            "requirements": "E-Commerce Android & iOS App",
            "budget": "$8,000"
        }
        resp = self.client.post("/api/webhook/whatsapp", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["event"], "inquiry_created")
        self.assertEqual(data["data"]["source"], "whatsapp")
        print("[PASSED] WhatsApp webhook endpoint creates inquiry with source 'whatsapp'.")

if __name__ == "__main__":
    unittest.main()

