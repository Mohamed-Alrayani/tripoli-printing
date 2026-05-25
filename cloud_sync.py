import os
import json
import time
import logging
import requests

PENDING_FILE = "pending_uploads.json"


def _load_pending():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_pending(items):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_pending(pdf_path, secure_code, client_name, total, invoice_number):
    items = _load_pending()
    # نتجنب التكرار
    for item in items:
        if item.get("secure_code") == secure_code and item.get("invoice_number") == invoice_number:
            return
    items.append({
        "pdf_path": pdf_path,
        "secure_code": secure_code,
        "client_name": client_name,
        "total": str(total),
        "invoice_number": invoice_number,
        "created_at": time.time(),
    })
    _save_pending(items)


def retry_pending_uploads():
    from database import get_company_settings
    settings = get_company_settings()
    cloud_url = (settings.get("cloud_server_url") or "").rstrip("/")
    cloud_api_key = settings.get("cloud_api_key") or ""
    if not cloud_url or not cloud_api_key:
        return

    items = _load_pending()
    if not items:
        return

    remaining = []
    for item in items:
        pdf_path = item.get("pdf_path", "")
        secure_code = item.get("secure_code", "")
        if not pdf_path or not os.path.exists(pdf_path) or not secure_code:
            continue
        try:
            with open(pdf_path, "rb") as f:
                files = {"pdf": (os.path.basename(pdf_path), f, "application/pdf")}
                data = {
                    "secure_code": secure_code,
                    "invoice_number": item.get("invoice_number", ""),
                    "client_name": item.get("client_name", ""),
                    "total": item.get("total", "0"),
                }
                resp = requests.post(
                    f"{cloud_url}/add-invoice",
                    files=files, data=data,
                    headers={"X-API-KEY": cloud_api_key},
                    timeout=30
                )
            if resp.status_code == 200:
                logging.info(f"Pending upload completed for {item.get('invoice_number')}")
                continue
            else:
                logging.warning(f"Pending retry failed: {resp.status_code}")
        except Exception as e:
            logging.warning(f"Pending retry error: {e}")
        remaining.append(item)

    _save_pending(remaining)
