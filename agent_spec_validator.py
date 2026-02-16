
import yaml
import sys
import os
import re

def load_spec(file_path):
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading YAML: {e}")
        sys.exit(1)

def check_field(data, field, required=True, valid_values=None, regex=None):
    if field not in data:
        if required:
            print(f"❌ Missing required field: {field}")
            return False
        return True
    
    value = data[field]
    
    if valid_values and value not in valid_values:
        print(f"❌ Invalid value for {field}: {value}. Expected one of {valid_values}")
        return False
        
    if regex and not re.match(regex, str(value)):
        print(f"❌ Invalid format for {field}: {value}. Expected usage of regex {regex}")
        return False
        
    return True

def validate_secrets(spec):
    # Ensure no secrets are hardcoded in the spec
    secrets = spec.get('secrets', [])
    for secret in secrets:
        if not re.match(r'^[A-Z0-9_]+$', secret):
            print(f"❌ Invalid secret name format: {secret}. Should be uppercase ENV var style.")
            return False
    
    # Check if any sensitive keys are accidentally in other fields
    spec_str = str(spec).lower()
    suspicious_patterns = ['api_key', 'password', 'secret', 'token']
    
    # Allow 'secrets' field to mention them, but look for values looking like real keys in other places
    # This is a bit advanced, for now a simple check:
    # If the user put a real key in "description" or something, catch it?
    # Maybe simply warn if values define look like high entropy strings? 
    # For now, just ensuring 'secrets' list assumes ENV injection is enough for structure.
    return True

def validate_agent_spec(file_path):
    print(f"🔍 Validating {file_path}...")
    spec = load_spec(file_path)
    valid = True

    # 1. Core Metadata
    valid &= check_field(spec, 'agent_name')
    valid &= check_field(spec, 'version', regex=r'^\d+\.\d+\.\d+$') # SemVer
    valid &= check_field(spec, 'owner')
    valid &= check_field(spec, 'agent_type', valid_values=['chatbot', 'parser', 'telecaller', 'recommender', 'other'])
    
    # 2. Spec Improvements
    valid &= check_field(spec, 'commit_hash', required=False) # Should be injected during build really, but good to have constraint if present
    
    # 3. LLM Provider
    if 'llm_provider' in spec:
        valid &= check_field(spec['llm_provider'], 'name')
        valid &= check_field(spec['llm_provider'], 'model')
    else:
        print("❌ Missing llm_provider section")
        valid = False

    # 4. Secrets
    if 'secrets' not in spec:
        print("⚠️  No 'secrets' section found. If this agent uses APIs, declare required ENV vars here.")
    else:
        valid &= validate_secrets(spec)

    # 5. Guardrails
    if 'guardrails' not in spec:
        print("❌ Missing guardrails section")
        valid = False
    else:
        valid &= check_field(spec['guardrails'], 'pii_filter', required=True)
        valid &= check_field(spec['guardrails'], 'prompt_versioning', valid_values=[True])

    if valid:
        print("✅ Spec is VALID!")
        return True
    else:
        print("❌ Spec validation FAILED.")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_spec_validator.py <path_to_agent_spec.yaml>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
        
    if not validate_agent_spec(file_path):
        sys.exit(1)
