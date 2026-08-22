import os
import json
import joblib
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, "model.pkl")
response_path = os.path.join(base_dir, "response_data.json")

print(f"Loading {model_path}...")
model = joblib.load(model_path)
print(f"Loaded model with {len(model.classes_)} classes.")

with open(response_path, "r", encoding="utf-8") as f:
    responses = json.load(f)

test_queries = [
    ("Can I hire CakePHP developers from Opti Matrix?", "cakephp_hiring_support", True),
    ("I need a CakePHP developer for my project. Can you help?", "cakephp_hiring_support", True),
    ("Where is your head office located?", "contact_location_head_office", True),
    ("What is the capital of France?", None, False),
    ("Who founded Opti Matrix?", "company_founded", True),
    ("How can I contact sales?", "contact_sales", True),
    ("Show me your portfolio", "portfolio_general", True),
    ("What services do you provide?", "services", True),
    ("Tell me about iOS application development", "iphone_app_general", True),
    ("Random gibberish xyz123 hello unknown?", None, False),
    ("can you give some software demo , you have built", "portfolio_general", True),
    ("can you give some software names that you have built", "portfolio_general", True)
]

CONFIDENCE_THRESHOLD = 0.15

print("\n" + "=" * 80)
print(f"{'QUERY':<50} | {'PREDICTED INTENT':<30} | {'CONF':<6} | {'MATCH'}")
print("=" * 80)

for q, exp_intent, exp_match in test_queries:
    probs = model.predict_proba([q])[0]
    max_idx = int(np.argmax(probs))
    conf = float(probs[max_idx])
    pred_intent = str(model.classes_[max_idx])
    
    is_matched = conf >= CONFIDENCE_THRESHOLD
    final_intent = pred_intent if is_matched else "FALLBACK (None)"
    answer = responses.get(pred_intent, ["No response found"])[0] if is_matched else "Fallback message returned"
    
    print(f"{q:<50} | {final_intent:<30} | {conf:.3f}  | {is_matched}")

print("=" * 80)
