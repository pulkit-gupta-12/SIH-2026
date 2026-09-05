import os
import django
import sys
from dotenv import load_dotenv

load_dotenv()

# Setup django environment
sys.path.append(r"c:\Users\kanishk doosaj\OneDrive\Desktop\New folder\SIH-2026\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.rules_engine.semantic.providers import get_llm_provider, OpenRouterProvider
import json

def test_openrouter():
    provider = get_llm_provider()
    
    print(f"Provider class: {type(provider).__name__}")
    if isinstance(provider, OpenRouterProvider):
        print(f"Model configured: {provider.model}")
        print(f"API Key configured: {'Yes' if provider.is_available() else 'No'}")
        print(f"API Key value: {provider.api_key[:10]}...")

    if not provider or not provider.is_available():
        print("Provider not available. Please check the API key in .env.")
        return

    print("Testing semantic evaluation with OpenRouter (minimax-m3:free)...")
    
    # Dummy rule data
    rule_id = "rule_test_123"
    section_ref = "Sec 3(1)(a)"
    statutory_requirement = "The package must clearly declare the maximum retail price (MRP) in INR."
    candidate_text = "Maximum Retail Price: Rs. 150.00 (incl. of all taxes)"
    field_name = "MRP"
    
    result = provider.evaluate_semantic_rule(
        rule_id=rule_id,
        section_ref=section_ref,
        statutory_requirement=statutory_requirement,
        candidate_text=candidate_text,
        field_name=field_name
    )
    
    print("Result from OpenRouter:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_openrouter()
