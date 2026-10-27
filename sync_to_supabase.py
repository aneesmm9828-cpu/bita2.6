"""
Supabase Data Sync Script
==========================
Ye script aapke collected training dataset ko Supabase ke 'training_data' table
me upload/save karti hai.
"""

import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_KEY")
    or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
    or ""
).strip()


# Sample dataset pairs jo browser me chat se collect huye hain
INITIAL_TRAINING_PAIRS = [
    {
        "instruction": "Apna parichay do aur batao tum kya kar sakte ho?",
        "output": "Namaste! Main Bita AI hoon, ek AI assistant jo aapke sawalon ke jawab deta hai aur naye AI models ko train karne ke liye training dataset tayar karta hai.",
        "tag": "Introduction"
    },
    {
        "instruction": "Python me list aur tuple me kya antar hai?",
        "output": "Python me List mutable hoti hai (isko badla ja sakta hai, e.g. [1, 2, 3]), jabki Tuple immutable hota hai (isko badla nahi ja sakta, e.g. (1, 2, 3)). List slow hoti hai, Tuple fast hota hai.",
        "tag": "Coding"
    },
    {
        "instruction": "AI model me weights kya hote hain?",
        "output": "Weights AI model ke mathematical parameters hote hain jo har input ki importance decide karte hain. Model training ke dauran inhi weights ko adjust kiya jata hai taaki model accurate predictions de sake.",
        "tag": "MachineLearning"
    }
]


def sync_data():
    print("=" * 60)
    print("☁️ Supabase Data Sync Pipeline")
    print("=" * 60)

    if not SUPABASE_KEY or "your-" in SUPABASE_KEY:
        print("\n❌ Error: Supabase API Key set nahi hai!")
        print("Kripya '.env' file me apni Supabase anon ya secret key paste karein:\n")
        print("SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\n")
        print("API Key lene ka link: https://supabase.com/dashboard/project/ifhybprohsejtkiofhyh/settings/api")
        return

    try:
        from supabase import create_client, Client

        print(f"Connecting to: {SUPABASE_URL}")
        client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase Connected!")

        print(f"\nUploading {len(INITIAL_TRAINING_PAIRS)} training pairs to 'training_data' table...")
        response = client.table("training_data").insert(INITIAL_TRAINING_PAIRS).execute()

        print(f"🎉 SUCCESS! Data Supabase database me successfully save ho gaya!")
        print(f"Inserted rows: {len(response.data)}")

    except Exception as e:
        print(f"\n❌ Error aaya: {e}")
        print("\n💡 Agar table nahi mili (relation does not exist), to pehle Supabase me 'setup.sql' run karein:")
        print("   Link: https://supabase.com/dashboard/project/ifhybprohsejtkiofhyh/sql/new\n")


if __name__ == "__main__":
    sync_data()
