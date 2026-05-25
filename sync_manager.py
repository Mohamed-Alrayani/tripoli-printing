import os
import json
import time
import logging
import requests

SYNC_FILE = "sync_queue.json"


def _load():
    if os.path.exists(SYNC_FILE):
        try:
            with open(SYNC_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save(items):
    with open(SYNC_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def enqueue(action, pdf_path=None, secure_code="", invoice_number="", client_name="", total="0"):
    """يضيف عملية لقائمة الانتظار."""
    items = _load()
    for item in items:
        if item.get("action") == action and item.get("invoice_number") == invoice_number:
            item["secure_code"] = secure_code
            item["client_name"] = client_name
            item["total"] = str(total)
            item["pdf_path"] = pdf_path
            item["retries"] = 0
            _save(items)
            return
    items.append({
        "action": action,
        "pdf_path": pdf_path,
        "secure_code": secure_code,
        "invoice_number": invoice_number,
        "client_name": client_name,
        "total": str(total),
        "retries": 0,
        "created_at": time.time(),
    })
    _save(items)


def enqueue_delete(invoice_number):
    """يضيف عملية حذف فاتورة."""
    items = _load()
    # نشيل أي عمليات save/edit معلقة لنفس الفاتورة
    items = [i for i in items if not (i.get("invoice_number") == invoice_number and i.get("action") in ("save", "edit"))]
    items.append({
        "action": "delete",
        "pdf_path": "",
        "secure_code": "",
        "invoice_number": invoice_number,
        "client_name": "",
        "total": "0",
        "retries": 0,
        "created_at": time.time(),
    })
    _save(items)


def process_queue():
    """يعالج كل العمليات المعلقة في قائمة الانتظار."""
    from database import get_company_settings
    settings = get_company_settings()
    cloud_url = (settings.get("cloud_server_url") or "").rstrip("/")
    cloud_api_key = settings.get("cloud_api_key") or ""
    if not cloud_url or not cloud_api_key:
        return

    items = _load()
    if not items:
        return

    remaining = []
    for item in items:
        action = item.get("action", "")
        invoice_number = item.get("invoice_number", "")
        secure_code = item.get("secure_code", "")
        client_name = item.get("client_name", "")
        total = item.get("total", "0")
        pdf_path = item.get("pdf_path", "")

        if action == "delete":
            try:
                resp = requests.post(
                    f"{cloud_url}/delete-invoice",
                    json={"invoice_number": invoice_number},
                    headers={"X-API-KEY": cloud_api_key},
                    timeout=15
                )
                if resp.status_code == 200:
                    logging.info(f"Synced delete: {invoice_number}")
                    continue
                else:
                    logging.warning(f"Sync delete failed: {resp.status_code}")
            except Exception as e:
                logging.warning(f"Sync delete error: {e}")
            remaining.append(item)
            continue

        if action in ("save", "edit"):
            if not pdf_path or not os.path.exists(pdf_path):
                logging.warning(f"Sync {action}: PDF not found for {invoice_number}")
                # نجرب تاني مرة وحدة، لو لسه مفيهوش نرمي
                item["retries"] = item.get("retries", 0) + 1
                if item["retries"] < 3:
                    remaining.append(item)
                continue
            try:
                with open(pdf_path, "rb") as f:
                    files = {"pdf": (os.path.basename(pdf_path), f, "application/pdf")}
                    data = {
                        "secure_code": secure_code,
                        "invoice_number": invoice_number,
                        "client_name": client_name,
                        "total": str(total),
                    }
                    resp = requests.post(
                        f"{cloud_url}/add-invoice",
                        files=files, data=data,
                        headers={"X-API-KEY": cloud_api_key},
                        timeout=30
                    )
                    if resp.status_code == 200:
                        logging.info(f"Synced {action}: {invoice_number} (code {secure_code})")
                        print(f"✅ Synced {action}: {invoice_number} (code {secure_code}) to cloud")
                        continue
                    else:
                        logging.warning(f"Sync {action} failed: {resp.status_code}")
            except Exception as e:
                logging.warning(f"Sync {action} error: {e}")

        item["retries"] = item.get("retries", 0) + 1
        if item["retries"] < 10:
            remaining.append(item)

    _save(remaining)


def pending_count():
    """عدد العمليات المعلقة في قائمة الانتظار."""
    return len(_load())
