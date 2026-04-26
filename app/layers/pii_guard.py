import json
import re
import os
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Configure Presidio
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
provider = NlpEngineProvider(nlp_configuration=configuration)
analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())
anonymizer = AnonymizerEngine()

# Load Corporate Vault
VAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "corporate_vault.json")

def load_vault():
    try:
        with open(VAULT_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def scrub_pii(text: str) -> str:
    vault = load_vault()
    redacted_text = text
    
    # 1. Custom Vault Redaction (Exact Keywords & Patterns)
    if vault:
        # Redact Employees & Projects (Word Boundary Case Insensitive)
        keywords = vault.get("employees", []) + vault.get("projects", [])
        for kw in keywords:
            pattern = re.compile(rf'\b{re.escape(kw)}\b', re.IGNORECASE)
            redacted_text = pattern.sub("[REDACTED]", redacted_text)
            
        # Redact Infrastructure Patterns (IPs, Buckets, etc.)
        infra = vault.get("infrastructure", {})
        patterns = infra.get("ip_patterns", []) + vault.get("secrets", {}).get("api_key_patterns", [])
        
        # Add a generic high-entropy string detector to catch unknown keys (hex/base64 style)
        # Matches strings of 20+ chars that look like keys/tokens
        generic_secret_pattern = r'\b[A-Za-z0-9+/]{20,}\b'
        patterns.append(generic_secret_pattern)

        for p in patterns:
            # Added flags=re.IGNORECASE implicitly via the pattern list if needed, 
            # but for generic secrets we want case sensitive as well.
            redacted_text = re.sub(p, "[REDACTED]", redacted_text)
            
        # server names
        for srv in infra.get("server_names", []):
            redacted_text = re.sub(rf'\b{re.escape(srv)}\b', "[REDACTED]", redacted_text)

    # 2. Presidio NLP Redaction (General PII like Emails/Phones)
    results = analyzer.analyze(
        text=redacted_text, 
        entities=["EMAIL_ADDRESS", "PHONE_NUMBER"], 
        language='en',
        score_threshold=0.3
    )
    
    anonymized_result = anonymizer.anonymize(
        text=redacted_text,
        analyzer_results=results,
        operators={
            "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})
        }
    )
    
    return anonymized_result.text