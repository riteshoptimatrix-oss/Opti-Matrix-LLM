import json
import joblib
import os
import glob
import re
import string
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return text.strip()

def augment_patterns(pattern: str, intent: str = "") -> list:
    """
    Generate synthetic in-domain paraphrases and prefix variations
    to enrich intent coverage and boost generalization.
    """
    variations = {pattern}
    p_lower = pattern.lower().strip()
    
    # Question prefix variations
    prefixes = [
        "can you tell me ",
        "please tell me ",
        "i want to know ",
        "do you have info on ",
        "what about ",
        "how about ",
        "information about ",
        "details for "
    ]
    
    # Remove question marks and common interrogative starters for keyword pattern matching
    stripped = re.sub(r'^(what is|what are|do you provide|do you offer|can i get|can we get|how to|tell me about)\s+', '', p_lower, flags=re.IGNORECASE)
    stripped = stripped.rstrip('?.! ')
    
    if len(stripped) > 3 and stripped != p_lower:
        variations.add(stripped)
        for pref in prefixes[:3]:
            variations.add(pref + stripped)
            
    # Inject synthetic context-augmented patterns for hiring intents
    if "hire" in intent.lower() or "hiring" in intent.lower():
        # Try to extract technology name from intent (e.g. 'hire_php_developer' -> 'php', 'angular_hiring' -> 'angular')
        parts = intent.lower().replace("_", " ").split()
        tech_keywords = [w for w in parts if w not in ["hire", "hiring", "developer", "developers", "fulltime", "dedicated", "support", "opti", "matrix"]]
        tech = tech_keywords[0] if tech_keywords else "web"
        
        # Add the exact augmented patterns the user might produce
        variations.add(f"{tech} developer role i need to hire one")
        variations.add(f"{tech} developer i need to hire one")
        variations.add(f"{tech} i need hire")
        variations.add(f"{tech} i need to hire one")
        variations.add(f"i need hire {tech}")
        variations.add(f"i need to hire one {tech}")
            
    return list(variations)

def main():
    print("=" * 60)
    print("1. Loading datasets from JSON_Data and Greetings...")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    patterns_by_intent = defaultdict(list)
    responses_by_intent = defaultdict(list)
    
    search_path = os.path.join(base_dir, "**", "*.json")
    all_json_files = glob.glob(search_path, recursive=True)
    
    valid_json_files = [
        f for f in all_json_files 
        if "venv" not in f 
        and "__pycache__" not in f 
        and "node_modules" not in f 
        and os.path.basename(f) != "response_data.json"
        and ("JSON_Data" in f or "Greetings" in f)
    ]

    for filepath in valid_json_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                if not isinstance(file_data, list):
                    continue
                for item in file_data:
                    intent = item.get("intent")
                    patterns = item.get("patterns", [])
                    responses = item.get("responses", [])
                    if intent:
                        intent = intent.strip()
                        for p in patterns:
                            if isinstance(p, str) and p.strip():
                                patterns_by_intent[intent].append(p.strip())
                        for r in responses:
                            if isinstance(r, str) and r.strip():
                                responses_by_intent[intent].append(r.strip())
        except Exception as e:
            print(f"Error loading {filepath}: {e}")

    total_intents = len(patterns_by_intent)
    print(f"Found {len(valid_json_files)} JSON dataset files.")
    print(f"Total unique intents: {total_intents}")

    # Export response_data.json
    response_export_path = os.path.join(base_dir, "response_data.json")
    with open(response_export_path, "w", encoding="utf-8") as f:
        json.dump(responses_by_intent, f, indent=2, ensure_ascii=False)
    print(f"Response mapping saved to {response_export_path}")

    # Build Augmented Dataset
    augmented_data = []
    seen = set()
    for intent, patterns in patterns_by_intent.items():
        for p in patterns:
            for variant in augment_patterns(p, intent):
                variant_clean = clean_text(variant)
                key = (variant_clean.lower(), intent)
                if key not in seen and len(variant_clean) > 1:
                    seen.add(key)
                    augmented_data.append((variant_clean, intent))

    print(f"Total augmented pattern-intent pairs: {len(augmented_data)}")

    # Split for benchmark evaluation
    import random
    random.seed(42)

    by_intent_grouped = defaultdict(list)
    for p, i in augmented_data:
        by_intent_grouped[i].append(p)

    train_pairs = []
    test_pairs = []
    for intent, pats in by_intent_grouped.items():
        if len(pats) == 1:
            train_pairs.append((pats[0], intent))
        else:
            pats_shuffled = list(pats)
            random.shuffle(pats_shuffled)
            n_test = max(1, int(len(pats_shuffled) * 0.15))
            test_pairs.extend([(p, intent) for p in pats_shuffled[:n_test]])
            train_pairs.extend([(p, intent) for p in pats_shuffled[n_test:]])

    X_train = [p[0] for p in train_pairs]
    y_train = [p[1] for p in train_pairs]
    X_test = [p[0] for p in test_pairs]
    y_test = [p[1] for p in test_pairs]

    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples:  {len(X_test)}")

    print("\n" + "=" * 60)
    print("2. Training High-Capacity TF-IDF + Logistic Regression Model...")
    print("=" * 60)

    eval_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=8000,
            sublinear_tf=True,
            token_pattern=r'(?u)\b\w+\b'
        )),
        ('clf', LogisticRegression(
            C=30.0,
            max_iter=500,
            solver='lbfgs',
            random_state=42
        ))
    ])

    eval_pipeline.fit(X_train, y_train)

    print("\n" + "=" * 60)
    print("3. Model Evaluation on Held-Out Test Patterns")
    print("=" * 60)

    y_pred = eval_pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)

    print(f"Accuracy:        {accuracy * 100:.2f}%")
    print(f"Weighted Prec:   {precision * 100:.2f}%")
    print(f"Weighted Recall: {recall * 100:.2f}%")
    print(f"Weighted F1:     {f1 * 100:.2f}%")

    print("\n" + "=" * 60)
    print("4. Fitting final production pipeline on 100% of augmented data & saving model.pkl...")
    print("=" * 60)

    production_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=8000,
            sublinear_tf=True,
            token_pattern=r'(?u)\b\w+\b'
        )),
        ('clf', LogisticRegression(
            C=30.0,
            max_iter=500,
            solver='lbfgs',
            random_state=42
        ))
    ])

    X_all = [p[0] for p in augmented_data]
    y_all = [p[1] for p in augmented_data]
    production_pipeline.fit(X_all, y_all)

    model_path = os.path.join(base_dir, "model.pkl")
    joblib.dump(production_pipeline, model_path)
    print(f"Model successfully saved to: {model_path}")
    print(f"Pipeline classes count: {len(production_pipeline.classes_)} (Expected: {total_intents})")
    print("=" * 60)

if __name__ == "__main__":
    main()
