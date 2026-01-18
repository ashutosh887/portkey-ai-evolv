from dotenv import load_dotenv
import os
import sys

# Load env variables
load_dotenv()

print("-" * 30)
print("Diagnostics:")
print("-" * 30)

# Check API Key
key = os.getenv("PORTKEY_API_KEY")
if key:
    print(f"✅ PORTKEY_API_KEY found: {key[:5]}******")
else:
    print("❌ PORTKEY_API_KEY NOT found in environment")

# Check Library
try:
    import portkey_ai
    print("✅ portkey-ai package is INSTALLED")
    print(f"   Version: {getattr(portkey_ai, '__version__', 'unknown')}")
except ImportError:
    print("❌ portkey-ai package is MISSING")
    print("   Please run: pip install portkey-ai")

print("-" * 30)
