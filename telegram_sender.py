import os
import requests
from PyQt5.QtCore import QThread, pyqtSignal

import database as db

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendDocument"
TELEGRAM_MSG_API = "https://api.telegram.org/bot{token}/sendMessage"


CHAT_NOT_FOUND_MSG = (
    "فشل إرسال الفاتورة: يجب على العميل الدخول للبوت (@Billllllllls_bot) "
    "والضغط على زر 'ابدأ' أولاً، أو تأكد من صحة الـ Telegram ID."
)


def _friendly_error(err_text):
    if not err_text:
        return "خطأ غير معروف من Telegram"
    err_lower = err_text.lower()
    if "chat not found" in err_lower:
        return CHAT_NOT_FOUND_MSG
    if "bot was blocked" in err_lower:
        return "فشل الإرسال: قام العميل بحظر البوت. الرجاء إعلامه بإلغاء حظر البوت (@Billllllllls_bot)."
    if "user is deactivated" in err_lower:
        return "فشل الإرسال: حساب Telegram الخاص بالعميل غير نشط (ملغي)."
    if "too many requests" in err_lower:
        return "فشل الإرسال: تم تجاوز عدد الطلبات المسموح بها. حاول مرة أخرى لاحقاً."
    return f"فشل إرسال الفاتورة:\n{err_text}"


def _send_to_one(url, pdf_path, pdf_filename, chat_id, caption):
    with open(pdf_path, "rb") as f:
        files = {"document": (pdf_filename, f, "application/pdf")}
        data = {"chat_id": chat_id, "caption": caption}
        return requests.post(url, files=files, data=data, timeout=60)


class TelegramSender(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, pdf_path, invoice_id, invoice_number, client_id, client_name, telegram_id, total=0, admin_id="", secure_code=""):
        super().__init__()
        self.pdf_path = pdf_path
        self.invoice_id = invoice_id
        self.invoice_number = invoice_number
        self.client_id = client_id
        self.client_name = client_name
        self.telegram_id = telegram_id
        self.total = total
        self.admin_id = str(admin_id).strip()
        self.secure_code = secure_code

    def run(self):
        try:
            s = db.get_company_settings()
            token = s.get("telegram_bot_token", "")
            if not token:
                self.finished.emit(False, CHAT_NOT_FOUND_MSG)
                return

            if not os.path.exists(self.pdf_path):
                self.finished.emit(False, "ملف PDF غير موجود")
                return

            url = TELEGRAM_API.format(token=token)
            pdf_filename = os.path.basename(self.pdf_path)

            client_caption = (
                f"📄 فاتورة جديدة\n"
                f"━━━━━━━━━━━━━━\n"
                f"رقم الفاتورة: {self.invoice_number}\n"
                f"العميل: {self.client_name}\n"
                f"الإجمالي: {self.total:.2f} د.ل\n"
                f"━━━━━━━━━━━━━━\n"
                f"شكراً لتعاملك معنا 🙏"
            )

            admin_caption = (
                f"📄 فاتورة جديدة - إشعار للمسؤول\n"
                f"━━━━━━━━━━━━━━\n"
                f"رقم الفاتورة: {self.invoice_number}\n"
                f"العميل: {self.client_name}\n"
                f"الإجمالي: {self.total:.2f} د.ل\n"
                f"━━━━━━━━━━━━━━"
            )

            recipients = [(self.telegram_id, self.client_name, self.client_id, client_caption)]

            if self.admin_id and self.admin_id != self.telegram_id:
                recipients.append((self.admin_id, "المسؤول", None, admin_caption))

            any_success = False
            last_error = ""

            for chat_id, label, cid, caption in recipients:
                try:
                    resp = _send_to_one(url, self.pdf_path, pdf_filename, chat_id, caption)

                    if resp.status_code == 200:
                        result = resp.json()
                        if result.get("ok"):
                            db.log_telegram_send(
                                self.invoice_id, self.invoice_number,
                                cid if cid else self.client_id,
                                label, chat_id, "success",
                                f"✅ تم الإرسال إلى {label}"
                            )
                            any_success = True

                            if self.secure_code and label == "المسؤول":
                                self._send_code_to_admin(chat_id)
                            continue

                    err = resp.json().get("description", f"HTTP {resp.status_code}")
                    friendly = _friendly_error(err)
                    db.log_telegram_send(
                        self.invoice_id, self.invoice_number,
                        cid if cid else self.client_id,
                        label, chat_id, "failed",
                        f"❌ {friendly}"
                    )
                    last_error = friendly

                except Exception as e:
                    friendly = _friendly_error(str(e))
                    db.log_telegram_send(
                        self.invoice_id, self.invoice_number,
                        cid if cid else self.client_id,
                        label, chat_id, "failed",
                        f"❌ {friendly}"
                    )
                    last_error = friendly

            if any_success:
                self.finished.emit(True, "تم إرسال الفاتورة عبر Telegram")
            else:
                self.finished.emit(False, last_error)

        except Exception as e:
            self.finished.emit(False, _friendly_error(str(e)))

    def _send_code_to_admin(self, admin_chat_id):
        try:
            s = db.get_company_settings()
            token = s.get("telegram_bot_token", "")
            if not token or not self.secure_code:
                return
            msg_url = TELEGRAM_MSG_API.format(token=token)
            code_msg = (
                f"🔐 كود استلام الفاتورة: {self.secure_code}\n"
                f"━━━━━━━━━━━━━━\n"
                f"العميل: {self.client_name}\n"
                f"رقم الفاتورة: {self.invoice_number}\n"
                f"الإجمالي: {self.total:.2f} د.ل\n"
                f"━━━━━━━━━━━━━━\n"
                f"⚠️ يجب على العميل إرسال هذا الكود للبوت لاستلام الفاتورة.\n"
                f"هذا الكود صالح للاستخدام مرة واحدة فقط."
            )
            requests.post(msg_url, data={"chat_id": admin_chat_id, "text": code_msg}, timeout=10)
        except Exception:
            pass
