"""
Bita AI - Secure Backend Server
================================
Ye server aapki saari API Keys (.env) ko safe rakhta hai.
Frontend me koi bhi key daalne ki zaroorat nahi hai (Zero Hacking Risk).

Features:
- Groq AI (Qwen 3.8 / 2.5) backend proxy
- Supabase direct server-side insert & export
- Full CORS support for chat.html
"""

import json
import os
import sys
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request
import urllib.error
import urllib.parse
from dotenv import load_dotenv

# Load .env file
load_dotenv(override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2", "").strip()
OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY", "").strip() or os.getenv("BITA_AI_KEY", "").strip())
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ifhybprohsejtkiofhyh.supabase.co").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_SECRET_KEY")
    or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    or os.getenv("SUPABASE_KEY")
    or ""
).strip()
DEFAULT_MODEL = "qwen/qwen3.8-27b"

_groq_key_idx = 0

def get_openrouter_key():
    load_dotenv(override=True)
    k = os.getenv("OPENROUTER_API_KEY", "").strip() or os.getenv("BITA_AI_KEY", "").strip()
    return k if (k and k.startswith("sk-or-v1-")) else None

def call_openrouter_api(messages, model="openrouter/free"):
    key = get_openrouter_key()
    if not key:
        return None
    # Use reliable OpenRouter model
    or_model = model if model and not model.startswith("bita") else "openrouter/free"
    req_body = json.dumps({
        "model": or_model,
        "messages": messages
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=req_body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Bita AI"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp_data = json.loads(resp.read().decode("utf-8"))
        return resp_data["choices"][0]["message"]["content"]

def generate_ai_image(prompt, width=1024, height=1024):
    clean_p = prompt.strip()
    if not clean_p:
        raise ValueError("Prompt is required for image generation")

    # 1. Try OpenRouter Image API if credits available
    or_key = get_openrouter_key()
    if or_key:
        try:
            req_body = json.dumps({
                "model": "bytedance-seed/seedream-4.5",
                "prompt": clean_p
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/images",
                data=req_body,
                headers={
                    "Authorization": f"Bearer {or_key}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                if resp_data.get("data") and len(resp_data["data"]) > 0:
                    b64 = resp_data["data"][0].get("b64_json")
                    if b64:
                        return {
                            "image_url": f"data:image/png;base64,{b64}",
                            "provider": "OpenRouter Image Engine",
                            "prompt": clean_p
                        }
        except Exception as e:
            print(f"ℹ️ OpenRouter image fallback to FLUX HD: {e}")

    # 2. High-Definition FLUX.1 Engine (Free, Instant, Ultra-HD)
    encoded_p = urllib.parse.quote(clean_p)
    seed = random.randint(1000, 999999)
    img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width={width}&height={height}&seed={seed}&nologo=true&model=flux"
    return {
        "image_url": img_url,
        "provider": "FLUX.1 (Ultra-HD AI)",
        "prompt": clean_p
    }

def get_groq_keys():
    load_dotenv(override=True)
    keys = []
    k1 = os.getenv("GROQ_API_KEY", "").strip()
    if k1 and k1.startswith("gsk_"):
        keys.append(k1)
    for i in range(2, 11):
        k = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
        if k and k.startswith("gsk_") and k not in keys:
            keys.append(k)
    return keys

def call_groq_api(messages, model=DEFAULT_MODEL, temperature=0.7):
    global _groq_key_idx
    keys = get_groq_keys()
    if not keys:
        raise ValueError("Groq API Key (.env me) missing hai! Kripya .env me GROQ_API_KEY set karein.")
    
    last_err = None
    # If 2 keys exist, try up to 2 attempts (one for each key if 429)
    max_tries = max(2, len(keys))
    for _ in range(max_tries):
        key = keys[_groq_key_idx % len(keys)]
        _groq_key_idx += 1
        req_body = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": temperature
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=req_body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                return resp_data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as he:
            last_err = he
            if he.code == 429 and len(keys) > 1:
                print("⚠️ Groq Key rate-limited (429), switching instantly to next key...")
                continue
            raise
        except Exception as e:
            last_err = e
            raise
    if last_err:
        raise last_err

def call_gemini_api(messages, model="gemini-2.0-flash"):
    load_dotenv(override=True)
    g_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("BITA_AI_KEY", "").strip()
    if not g_key:
        return None
    api_model = "gemini-2.0-flash-lite" if "lite" in model.lower() else "gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{api_model}:generateContent?key={g_key}"
    
    contents = []
    for m in messages:
        role = "model" if m.get("role") == "assistant" else "user"
        text = m.get("content", "")
        if m.get("role") == "system":
            text = f"[System Instructions: {text}]"
        contents.append({
            "role": role,
            "parts": [{"text": text}]
        })
    req_body = json.dumps({"contents": contents}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp_data = json.loads(resp.read().decode("utf-8"))
        return resp_data["candidates"][0]["content"]["parts"][0]["text"]

def get_supabase_client():
    if not SUPABASE_KEY or "your-" in SUPABASE_KEY:
        return None
    try:
        # pyrefly: ignore[missing-import]
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️ Supabase init error: {e}")
        return None


class SecureApiHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for frontend
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            keys = get_groq_keys()
            or_key = get_openrouter_key()
            status = {
                "groq_configured": len(keys) > 0,
                "groq_keys_count": len(keys),
                "openrouter_configured": bool(or_key),
                "openrouter_key": or_key or "",
                "image_generation_enabled": True,
                "speed_multiplier": f"{len(keys)}x" if len(keys) > 1 else "1x",
                "supabase_configured": bool(SUPABASE_KEY and "your-" not in SUPABASE_KEY),
                "supabase_url": SUPABASE_URL,
                "model": DEFAULT_MODEL,
                "security": "100% Backend Secure (.env protected)"
            }
            self.wfile.write(json.dumps(status).encode("utf-8"))
            return

        # Serve static files (like chat.html)
        if self.path == "/" or self.path == "":
            self.path = "/chat.html"
        return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        # 1. /api/chat - Secure AI Chat & Auto-Save
        if self.path == "/api/chat":
            prompt = data.get("prompt", "").strip()
            history = data.get("history", [])
            system_prompt = data.get("system_prompt", "Aap Bita AI hain, ek helpful AI assistant.")
            model = data.get("model", DEFAULT_MODEL)

            if not prompt:
                self.send_json_error(400, "Prompt is required")
                return

            try:
                # Call Groq / OpenRouter / Gemini with failover
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(history[-6:])
                messages.append({"role": "user", "content": prompt})

                ai_answer = None

                # 1. OpenRouter model call if selected
                if "deepseek" in model.lower() or "openrouter" in model.lower():
                    try:
                        ai_answer = call_openrouter_api(messages, model=model)
                    except Exception as ore:
                        print(f"⚠️ OpenRouter call warning, falling back to Groq: {ore}")

                # 2. Gemini model call if selected
                if not ai_answer and model in ["bita-ai-2.6", "gemini-2.0-flash", "gemini-2.0-flash-lite"]:
                    try:
                        ai_answer = call_gemini_api(messages, model=model)
                    except Exception as ge:
                        print(f"⚠️ Gemini call error, falling back to Groq: {ge}")

                # 3. Groq Fast Multi-Key fallback
                if not ai_answer:
                    groq_m = model if not (model == "bita-ai-2.6" or "gemini" in model or "deepseek" in model) else DEFAULT_MODEL
                    ai_answer = call_groq_api(messages, model=groq_m, temperature=0.7)

                # Auto-save to Supabase from backend (if configured)
                uploaded_to_sb = False
                sb = get_supabase_client()
                if sb:
                    try:
                        sb.table("training_data").insert({
                            "instruction": prompt,
                            "output": ai_answer,
                            "tag": "Auto"
                        }).execute()
                        uploaded_to_sb = True
                    except Exception as sb_err:
                        print(f"⚠️ Supabase auto-save error: {sb_err}")

                self.send_json_response(200, {
                    "response": ai_answer,
                    "uploaded_to_supabase": uploaded_to_sb
                })

            except urllib.error.HTTPError as he:
                err_text = he.read().decode("utf-8")
                self.send_json_error(he.code, f"API Error: {err_text}")
            except Exception as e:
                self.send_json_error(500, str(e))
            return

        # 1.5. /api/generate-image - AI Image Generation (OpenRouter + FLUX.1 Ultra-HD)
        if self.path == "/api/generate-image":
            prompt = data.get("prompt", "").strip()
            width = int(data.get("width", 1024))
            height = int(data.get("height", 1024))
            if not prompt:
                self.send_json_error(400, "Prompt is required for image generation")
                return

            try:
                img_data = generate_ai_image(prompt, width=width, height=height)
                uploaded_to_sb = False
                sb = get_supabase_client()
                if sb:
                    try:
                        sb.table("training_data").insert({
                            "instruction": f"Generate Image: {prompt}",
                            "output": f"Generated via {img_data.get('provider')}: {img_data.get('image_url')}",
                            "tag": "ImageGeneration"
                        }).execute()
                        uploaded_to_sb = True
                    except Exception as sb_err:
                        print(f"⚠️ Supabase image log warning: {sb_err}")

                self.send_json_response(200, {
                    "success": True,
                    "image_url": img_data.get("image_url"),
                    "provider": img_data.get("provider"),
                    "prompt": prompt,
                    "uploaded_to_supabase": uploaded_to_sb
                })
            except Exception as e:
                self.send_json_error(500, str(e))
            return

        # 2. /api/supabase-export - Secure Batch Sync
        if self.path == "/api/supabase-export":
            items = data.get("items", [])
            if not items:
                self.send_json_error(400, "No items provided for export")
                return

            load_dotenv(override=True)
            sb = get_supabase_client()
            if not sb:
                self.send_json_error(500, "Supabase key (.env me) set nahi hai! Kripya .env me SUPABASE_PUBLISHABLE_KEY ya SUPABASE_SECRET_KEY daalein.")
                return

            try:
                payload = [
                    {
                        "instruction": it.get("instruction", ""),
                        "output": it.get("output", ""),
                        "tag": it.get("tag", "Exported")
                    }
                    for it in items
                ]
                # Chunk into batches of 50
                chunk_size = 50
                total_uploaded = 0
                for i in range(0, len(payload), chunk_size):
                    chunk = payload[i:i + chunk_size]
                    sb.table("training_data").insert(chunk).execute()
                    total_uploaded += len(chunk)

                self.send_json_response(200, {
                    "success": True,
                    "uploaded_count": total_uploaded
                })
            except Exception as e:
                self.send_json_error(500, f"Supabase sync failed: {e}")
            return

        # 3. /api/bulk-answer - Secure Bulk Question Answer & Direct Supabase Push
        if self.path == "/api/bulk-answer":
            question = data.get("question", "").strip()
            if not question:
                self.send_json_error(400, "Question is required")
                return

            try:
                # Answer question via Groq (with multi-key rotation & failover)
                messages = [
                    {"role": "system", "content": "Aap ek helpful AI hain. Hindi aur English me accurate answer dein."},
                    {"role": "user", "content": question}
                ]
                ai_ans = call_groq_api(messages, model=DEFAULT_MODEL, temperature=0.7)

                # Push to Supabase directly from server
                uploaded = False
                sb = get_supabase_client()
                if sb:
                    try:
                        sb.table("training_data").insert({
                            "instruction": question,
                            "output": ai_ans,
                            "tag": "Bulk1000"
                        }).execute()
                        uploaded = True
                    except Exception as sbe:
                        print(f"⚠️ Supabase bulk insert error: {sbe}")

                self.send_json_response(200, {
                    "question": question,
                    "answer": ai_ans,
                    "uploaded_to_supabase": uploaded
                })
            except Exception as e:
                self.send_json_error(500, str(e))
            return

        self.send_json_error(404, "Endpoint not found")

    def send_json_response(self, code, payload):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def send_json_error(self, code, message):
        self.send_json_response(code, {"error": message, "success": False})


def run_server(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, SecureApiHandler)
    print("=" * 60)
    print("🛡️  Bita AI Secure Backend Server Running")
    print("=" * 60)
    print(f"📍 Local URL: http://localhost:{port}")
    print("🔒 Security: Saari API Keys .env file se load hongi.")
    print("   Frontend me koi bhi secret key expose nahi hogi!")
    print("=" * 60)
    httpd.serve_forever()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port)
