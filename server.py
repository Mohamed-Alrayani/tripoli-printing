import os
import io
import json
import time
import logging
import threading
from flask import Flask, request, jsonify
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_KEY = os.environ.get("X_API_KEY", "")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://tripoli-printing.onrender.com")

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

DATA_DIR = "invoices_data"
INDEX_FILE = os.path.join(DATA_DIR, "index.json")
os.makedirs(DATA_DIR, exist_ok=True)

invoices = {}
_last_update_id = 0
_last_heartbeat = 0

TELEGRAM_API = "https://api.telegram.org/bot" + BOT_TOKEN
GET_UPDATES = TELEGRAM_API + "/getUpdates"
SEND_MSG = TELEGRAM_API + "/sendMessage"
SEND_DOC = TELEGRAM_API + "/sendDocument"
DELETE_WEBHOOK = TELEGRAM_API + "/deleteWebhook"


INVOICE_TTL_DAYS = 180  # 6 شهور قبل حذف الفواتير غير المستلمة


def _load_index():
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for code, info in data.items():
                    pdf_path = info.get("pdf_path", "")
                    if os.path.exists(pdf_path):
                        invoices[code] = info
                logging.info(f"Loaded {len(invoices)} invoices from disk")
        except Exception as e:
            logging.error(f"Failed to load index: {e}")


def _save_index():
    try:
        index = {}
        for code, info in invoices.items():
            index[code] = {
                "invoice_number": info["invoice_number"],
                "client_name": info["client_name"],
                "total": info["total"],
                "pdf_path": info.get("pdf_path", ""),
                "pdf_filename": info["pdf_filename"],
                "created_at": info.get("created_at", 0),
            }
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Failed to save index: {e}")


def _cleanup_expired():
    """يحذف الفواتير القديمة غير المستلمة من الذاكرة والقرص."""
    now = time.time()
    max_age = INVOICE_TTL_DAYS * 86400
    to_delete = []
    for code, info in list(invoices.items()):
        created = info.get("created_at", 0)
        if created > 0 and now - created > max_age:
            to_delete.append(code)
    for code in to_delete:
        inv = invoices.pop(code, None)
        if inv:
            pdf_path = inv.get("pdf_path", "")
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass
            logging.info(f"Expired invoice {inv.get('invoice_number', '?')} (code {code}) cleaned up")
    if to_delete:
        _save_index()


def send_message(chat_id, text):
    try:
        requests.post(SEND_MSG, json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        logging.error(f"send_message failed: {e}")


def send_document(chat_id, pdf_path, filename, caption):
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        files = {"document": (filename, io.BytesIO(pdf_bytes), "application/pdf")}
        data = {"chat_id": chat_id, "caption": caption}
        requests.post(SEND_DOC, files=files, data=data, timeout=60)
    except Exception as e:
        logging.error(f"send_document failed: {e}")


def process_update(update):
    global _last_heartbeat
    # إذا الابتوب شغال (heartbeat < 60 ثانية)، نتخطى المعالجة عشان ما يتعارض
    if time.time() - _last_heartbeat < 60:
        return

    msg = update.get("message")
    if not msg:
        return
    chat_id = msg["chat"]["id"]
    text = (msg.get("text") or "").strip()
    if not text:
        return

    if text == "/start":
        send_message(
            chat_id,
            "مرحباً بك في بوت الفواتير 🤖\n\n"
            "للاستلام فاتورتك، يرجى إرسال رمز التحقق المكون من 3 أرقام\n"
            "الذي استلمته من الشركة.",
        )
        return

    # معالجة /start 123 (من مسح الباركود)
    if text.startswith("/start ") and len(text) > 7:
        code = text[7:].strip()
        if code.isdigit() and len(code) == 3:
            text = code
        else:
            return

    if text.isdigit() and len(text) == 3:
        code = text
        inv = invoices.pop(code, None)

        if not inv:
            send_message(
                chat_id,
                "عذراً، هذا الكود غير صحيح أو انتهت صلاحيته.\n"
                "الرجاء التواصل مع الشركة للحصول على كود جديد.",
            )
            return

        pdf_path = inv.get("pdf_path", "")
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass
        _save_index()

        caption = (
            f"📄 فاتورة رقم: {inv['invoice_number']}\n"
            f"━━━━━━━━━━━━━━\n"
            f"تم التحقق من الكود بنجاح ✅\n"
            f"شكراً لتعاملك معنا 🙏"
        )
        send_document(chat_id, pdf_path, inv["pdf_filename"], caption)
        logging.info(f"Invoice {inv['invoice_number']} sent via cloud, code {code} deleted")


def poll_bot():
    global _last_update_id
    # نحاول نمسح أي webhook عشان polling يشتغل
    # إذا ما انمسحش، webhook route راح يتولى المعالجة
    try:
        requests.post(DELETE_WEBHOOK, timeout=10)
    except Exception:
        pass
    time.sleep(1)

    while True:
        try:
            params = {"offset": _last_update_id + 1, "timeout": 30}
            resp = requests.get(GET_UPDATES, params=params, timeout=35)
            if resp.status_code == 409:
                # webhook لسه مضبوط → polling ما يشتغلش، نتخطى والـ webhook يتولى
                time.sleep(10)
                continue
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        _last_update_id = update["update_id"]
                        process_update(update)
        except requests.Timeout:
            continue
        except Exception as e:
            logging.error(f"Poll error: {e}")
            time.sleep(10)


# -------------------- Flask Routes --------------------

@app.route("/webhook", methods=["POST"])
def webhook():
    """معالجة التحديثات الواردة من Webhook تليجرام (كاحتياطي إلى جانب polling)."""
    update = request.get_json(silent=True) or {}
    if update:
        process_update(update)
    return "", 200


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    global _last_heartbeat
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    _last_heartbeat = time.time()
    return jsonify({"ok": True}), 200


@app.route("/delete-code", methods=["POST"])
def delete_code():
    """يحذف كود من السحابة لما الابتوب يعالجه أولاً (اختياري)."""
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()
    if code and code in invoices:
        inv = invoices.pop(code)
        pdf_path = inv.get("pdf_path", "")
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass
        _save_index()
        logging.info(f"Code {code} deleted from cloud by desktop notification")
        return jsonify({"ok": True, "note": "deleted"}), 200
    return jsonify({"ok": True, "note": "not_found"}), 200


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "invoices_count": len(invoices)}), 200


@app.route("/add-invoice", methods=["POST"])
def add_invoice():
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    secure_code = request.form.get("secure_code", "").strip()
    invoice_number = request.form.get("invoice_number", "").strip()
    client_name = request.form.get("client_name", "").strip()
    total = request.form.get("total", "0")

    if not secure_code or len(secure_code) != 3 or not secure_code.isdigit():
        return jsonify({"error": "Invalid secure code (must be 3 digits)"}), 400

    pdf_file = request.files.get("pdf")
    if not pdf_file:
        return jsonify({"error": "PDF file is required"}), 400

    pdf_bytes = pdf_file.read()
    pdf_filename = pdf_file.filename or f"فاتورة_{invoice_number}.pdf"
    pdf_path = os.path.join(DATA_DIR, f"{secure_code}_{invoice_number}.pdf")

    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    invoices[secure_code] = {
        "invoice_number": invoice_number,
        "client_name": client_name,
        "total": total,
        "pdf_filename": pdf_filename,
        "pdf_path": pdf_path,
        "created_at": time.time(),
    }

    _save_index()
    logging.info(f"Invoice {invoice_number} stored in cloud")
    return jsonify({"success": True, "message": "تم تخزين الفاتورة في السحابة"}), 200


# -------------------- تشغيل البولينج والتنظيف في خلفية --------------------
def cleanup_loop():
    while True:
        time.sleep(3600)  # كل ساعة
        _cleanup_expired()


_load_index()
threading.Thread(target=poll_bot, daemon=True).start()
threading.Thread(target=cleanup_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
