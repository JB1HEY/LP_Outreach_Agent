"""
Verification script for LP Outreach Agent (Post-Reorganization)
Tests configuration loading and API connectivity
"""
import sys
import os
from src.config import load_config
import google.generativeai as genai

def test_config():
    print("Testing configuration loading...")
    try:
        search_config, criteria = load_config()
        if search_config.gemini_api_key:
            print(f"✓ API Key found in env: {search_config.gemini_api_key[:5]}...")
            return True
        else:
            print("✗ API Key missing from config")
            return False
    except Exception as e:
        print(f"✗ Config load failed: {e}")
        return False

def test_api_connectivity():
    print("\nTesting Gemini API connectivity...")
    try:
        search_config, _ = load_config()
        genai.configure(api_key=search_config.gemini_api_key)
        
        # Using Gemini 2.0 Flash as determined earlier
        model_name = 'gemini-2.0-flash'
        print(f"Connecting to {model_name}...")
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, are you online?")
        
        if response.text:
            print(f"✓ API Connected! Response: {response.text.strip()[:30]}...")
            return True
        else:
            print("✗ API returned empty response")
            return False
            
    except Exception as e:
        if "429" in str(e):
            print("⚠ API Connected but Rate Limited (429). Key is valid.")
            return True
        print(f"✗ API Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("SYSTEM VERIFICATION")
    print("="*60)
    
    config_ok = test_config()
    api_ok = test_api_connectivity()
    
    print("\n" + "="*60)
    if config_ok and api_ok:
        print("VERIFICATION SUCCESSFUL! ✅")
        print("You can now run: python main.py")
    else:
        print("VERIFICATION FAILED ❌")
    print("="*60)
