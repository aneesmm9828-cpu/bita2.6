"""
Supabase Python Client & Chat Backend Example
==============================================
Ye script Supabase database se connect karti hai aur 'messages' table me
data insert aur read karne me madad karti hai.
"""

import os
import sys
from dotenv import load_dotenv
# pyrefly: ignore[missing-import]
from supabase import create_client, Client

# .env file se URL aur Key load karein
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_KEY")
    or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
    or ""
).strip()


def get_supabase_client() -> Client:
    """Supabase client initialize karta hai."""
    placeholders = ["your-project-url", "your-project-id", "your-publishable-key", "your-anon-public-key-here"]
    is_placeholder = any(p in SUPABASE_URL for p in placeholders) or any(p in SUPABASE_KEY for p in placeholders)
    if not SUPABASE_URL or not SUPABASE_KEY or is_placeholder:
        print("\n❌ Error: .env file me asali credentials nahi hain!")
        print(f"Current SUPABASE_URL = '{SUPABASE_URL}'")
        print(f"Current SUPABASE_KEY = '{SUPABASE_KEY}'")
        print("\nKripya '.env' file me apna actual Supabase Project URL (e.g. https://xxxxxx.supabase.co) aur Key paste karke Save (Ctrl+S) karein.\n")
        sys.exit(1)

    try:
        client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client
    except Exception as e:
        print(f"❌ Supabase client initialization error: {e}")
        sys.exit(1)


def send_message(username: str, content: str):
    """'messages' table me naya message bhejta hai."""
    client = get_supabase_client()
    try:
        response = (
            client.table("messages")
            .insert({"username": username, "content": content})
            .execute()
        )
        print(f"✅ Message bhej diya gaya: [{username}]: {content}")
        return response.data
    except Exception as e:
        print(f"❌ Message send karne me error aaya: {e}")
        return None


def get_messages(limit: int = 10):
    """'messages' table se aakhiri messages fetch karta hai."""
    client = get_supabase_client()
    try:
        response = (
            client.table("messages")
            .select("*")
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        messages = response.data
        print(f"\n--- Supabase Chat Messages (Total: {len(messages)}) ---")
        for msg in messages:
            sender = msg.get("username", "Unknown")
            body = msg.get("content", "")
            time = msg.get("created_at", "")[:19]
            print(f"[{time}] {sender}: {body}")
        print("--------------------------------------------------\n")
        return messages
    except Exception as e:
        print(f"❌ Messages fetch karne me error aaya: {e}")
        return []


if __name__ == "__main__":
    print("=" * 55)
    print("🚀 Supabase Python Client Test")
    print("=" * 55)

    if not SUPABASE_URL or not SUPABASE_KEY or "your-project-id" in SUPABASE_URL:
        print("\n⚠️ .env file me credentials update karein:")
        print("1. .env file kholein.")
        print("2. SUPABASE_URL aur SUPABASE_KEY paste karein.")
        print("3. Phir ye script run karein: python supabase_client.py\n")
    else:
        print(f"URL: {SUPABASE_URL}")
        print("Connecting to Supabase...")
        client = get_supabase_client()
        print("✅ Supabase Connected successfully!")

        # Example: Fetch recent messages
        get_messages()

        # Uncomment to send a test message:
        # send_message("Anees", "Hello from Python script!")
