import os
import io
import json
import logging
from flask import Flask, request, jsonify
import telebot
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_KEY = os.environ.get("X_API_KEY", "")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

invoices = {}

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

    invoices[secure_code] = {
        "invoice_number": invoice_number,
        "client_name": client_name,
        "total": total,
        "pdf_bytes": pdf_bytes,
        "pdf_filename": pdf_file.filename or f"فاتورة_{invoice_number}.pdf",
    }

    logging.info(f"Invoice {invoice_number} stored with code {secure_code}")
    return jsonify({"success": True, "message": "تم تخزين الفاتورة في السحابة"}), 200


@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.reply_to(
        message,
        "مرحباً بك في بوت الفواتير 🤖\n\n"
        "للاستلام فاتورتك، يرجى إرسال رمز التحقق المكون من 3 أرقام\n"
        "الذي استلمته من الشركة.",
    )


@bot.message_handler(func=lambda m: m.text and m.text.isdigit() and len(m.text) == 3)
def handle_code(message):
    code = message.text
    chat_id = message.chat.id
    inv = invoices.pop(code, None)

    if not inv:
        bot.reply_to(
            message,
            "عذراً، هذا الكود غير صحيح أو انتهت صلاحيته.\n"
            "الرجاء التواصل مع الشركة للحصول على كود جديد.",
        )
        return

    caption = (
        f"📄 فاتورة رقم: {inv['invoice_number']}\n"
        f"━━━━━━━━━━━━━━\n"
        f"تم التحقق من الكود بنجاح ✅\n"
        f"شكراً لتعاملك معنا 🙏"
    )

    try:
        bot.send_document(
            chat_id,
            (inv["pdf_filename"], io.BytesIO(inv["pdf_bytes"]), "application/pdf"),
            caption=caption,
        )
        logging.info(f"Invoice {inv['invoice_number']} sent, code {code} deleted")
    except Exception as e:
        logging.error(f"Failed to send document: {e}")
        bot.send_message(
            chat_id,
            "عذراً، حدث خطأ أثناء تجهيز الفاتورة. الرجاء المحاولة لاحقاً.",
        )


@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.json:
        update = telebot.types.Update.de_json(json.dumps(request.json))
        bot.process_new_updates([update])
    return "OK", 200


def set_webhook():
    if not BOT_TOKEN or not RENDER_URL:
        logging.warning("BOT_TOKEN or RENDER_EXTERNAL_URL not set, skipping webhook")
        return
    webhook_url = f"{RENDER_URL}/webhook/{BOT_TOKEN}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    resp = requests.post(url, json={"url": webhook_url})
    if resp.status_code == 200 and resp.json().get("ok"):
        logging.info(f"Webhook set to {webhook_url}")
    else:
        logging.error(f"Webhook failed: {resp.text}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
