import os
import sys

# Ensure backend is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import supabase_client

def test_vault():
    try:
        # Try to read from vault
        res = supabase_client.table("vault.decrypted_secrets").select("*").execute()
        print("Vault access via PostgREST:", res)
    except Exception as e:
        print("Error accessing Vault via PostgREST:", e)

if __name__ == "__main__":
    test_vault()
