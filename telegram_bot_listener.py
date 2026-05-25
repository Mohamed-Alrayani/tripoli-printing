import os
import time
import requests
import threading
from datetime import datetime

import database as db

TELEGRAM_API = "https://api.telegram.org/bot{token}"
UPDATES_API = TELEGRAM_API + "/getUpdates"
SEND_DOC_API = TELEGRAM_API + "/sendDocument"
SEND_MSG_API = TELEGRAM_API + "/sendMessage"


class TelegramBotListener(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self._running = False
        self._last_update_id = 0

    def run(self):
        self._running = True
        while self._running:
            try:
                s = db.get_company_settings()
                token = s.get("telegram_bot_token", "")
                if not token:
                    time.sleep(10)
                    continue

                url = UPDATES_API.format(token=token)
                params = {"offset": self._last_update_id + 1, "timeout": 30}
                resp = requests.get(url, params=params, timeout=35)

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        for update in data.get("result", []):
                            self._last_update_id = update["update_id"]
                            self._handle_update(update, token, s)
            except requests.Timeout:
                continue
            except Exception:
                time.sleep(10)
                continue

    def _handle_update(self, update, token, settings):
        msg = update.get("message")
        if not msg:
            return
        chat_id = str(msg["chat"]["id"])
        text = (msg.get("text") or "").strip()

        if not text:
            return

        # معالجة /start 123 (من مسح الباركود)
        if text.startswith("/start ") and len(text) > 7:
            code = text[7:].strip()
            if code.isdigit() and len(code) == 3:
                text = code

        if text.isdigit() and len(text) == 3:
            self._process_code(text, chat_id, token, settings)
            return

    def _process_code(self, code, chat_id, token, settings=None):
        inv = db.find_invoice_by_secure_code(code)
        if not inv:
            print(f"[BOT-LAPTOP] Code {code} not found in local DB")
            msg_url = SEND_MSG_API.format(token=token)
            requests.post(
                msg_url,
                data={
                    "chat_id": chat_id,
                    "text": "عذراً، هذا الكود غير صحيح أو انتهت صلاحيته.\n"
                            "الرجاء التواصل مع الشركة للحصول على كود جديد."
                },
                timeout=10
            )
            return

        pdf_dir = "/home/mohamed/سطح المكتب/فواتير منظومة"
        os.makedirs(pdf_dir, exist_ok=True)
        from pdf_export import generate_invoice_pdf
        items = db.get_invoice_items(inv["id"])
        client = db.get_client_by_id(inv["client_id"])
        pdf_path = os.path.join(
            pdf_dir,
            f"فاتورة_{inv['invoice_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        try:
            invoice_data = {
                "number": inv["invoice_number"],
                "date": inv["date"],
                "total_before_discount": inv["total_before_discount"],
                "discount": inv["discount"],
                "total_after_discount": inv["total_after_discount"],
                "paid_amount": inv["paid_amount"],
                "remaining_amount": inv["remaining_amount"],
                "status": inv["status"],
            }
            generate_invoice_pdf(invoice_data, items, client, pdf_path, secure_code=code)
        except Exception:
            msg_url = SEND_MSG_API.format(token=token)
            requests.post(
                msg_url,
                data={
                    "chat_id": chat_id,
                    "text": "عذراً، حدث خطأ أثناء تجهيز الفاتورة. الرجاء المحاولة لاحقاً."
                },
                timeout=10
            )
            return

        doc_url = SEND_DOC_API.format(token=token)
        caption = (
            f"📄 فاتورة رقم: {inv['invoice_number']}\n"
            f"━━━━━━━━━━━━━━\n"
            f"تم التحقق من الكود بنجاح ✅\n"
            f"شكراً لتعاملك معنا 🙏"
        )
        try:
            with open(pdf_path, "rb") as f:
                files = {"document": (os.path.basename(pdf_path), f, "application/pdf")}
                data = {"chat_id": chat_id, "caption": caption}
                resp = requests.post(doc_url, files=files, data=data, timeout=60)

            if resp.status_code == 200 and resp.json().get("ok"):
                db.invalidate_secure_code(inv["id"])
                db.log_telegram_send(
                    inv["id"], inv["invoice_number"],
                    inv["client_id"], inv.get("client_name", ""),
                    chat_id, "success",
                    f"✅ تم إرسال الفاتورة عن طريق كود الأمان {code}"
                )
                # إعلام السحابة بحذف الكود (إذا كان موجود عندها)
                if settings:
                    self._notify_cloud_delete(code, settings)
        except Exception:
            pass

    def _notify_cloud_delete(self, code, settings):
        """يُعلم السيرفر السحابي بحذف الكود عشان ما يرسل الفاتورة مرتين."""
        cloud_url = (settings.get("cloud_server_url") or "").rstrip("/")
        cloud_api_key = settings.get("cloud_api_key") or ""
        if cloud_url and cloud_api_key:
            try:
                requests.post(
                    f"{cloud_url}/delete-code",
                    json={"code": code},
                    headers={"X-API-KEY": cloud_api_key},
                    timeout=10
                )
            except Exception:
                pass

    def stop(self):
        self._running = False
