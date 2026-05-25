import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            email TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            client_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            total_before_discount REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total_after_discount REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            remaining_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'قيد التصميم',
            attachment_path TEXT DEFAULT '',
            telegram_secure_code TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );

        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            service_type TEXT NOT NULL,
            length REAL DEFAULT 0,
            width REAL DEFAULT 0,
            area REAL DEFAULT 0,
            unit_price REAL DEFAULT 0,
            quantity INTEGER DEFAULT 1,
            installation_fee REAL DEFAULT 0,
            total REAL DEFAULT 0,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            default_price REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            unit TEXT NOT NULL DEFAULT 'متر',
            current_quantity REAL DEFAULT 0,
            min_quantity REAL DEFAULT 5,
            unit_price REAL DEFAULT 0,
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS material_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            invoice_id INTEGER,
            change_amount REAL NOT NULL,
            transaction_type TEXT NOT NULL CHECK(transaction_type IN ('add','remove','consume')),
            date TEXT NOT NULL,
            notes TEXT DEFAULT '',
            FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS telegram_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            invoice_number TEXT,
            client_id INTEGER,
            client_name TEXT,
            telegram_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            message TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    c.execute("PRAGMA table_info(invoices)")
    cols = [r[1] for r in c.fetchall()]
    if "attachment_path" not in cols:
        c.execute("ALTER TABLE invoices ADD COLUMN attachment_path TEXT DEFAULT ''")
    if "telegram_secure_code" not in cols:
        c.execute("ALTER TABLE invoices ADD COLUMN telegram_secure_code TEXT DEFAULT NULL")

    c.execute("PRAGMA table_info(clients)")
    client_cols = [r[1] for r in c.fetchall()]
    if "telegram_id" not in client_cols:
        c.execute("ALTER TABLE clients ADD COLUMN telegram_id TEXT DEFAULT ''")

    c.executescript("""
        CREATE TABLE IF NOT EXISTS company_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT DEFAULT 'شركتي',
            phone1 TEXT DEFAULT '',
            phone2 TEXT DEFAULT '',
            address TEXT DEFAULT '',
            currency TEXT DEFAULT 'د.ل',
            invoice_notes TEXT DEFAULT 'البضاعة التي تفصل لا ترد ولا تستبدل. نشكركم على حسن تعاملكم معكم.',
            telegram_bot_token TEXT DEFAULT '8658197731:AAEhum8PY1W0-6whvMH6mtH0gbXzNuXpTdI',
            telegram_admin_id TEXT DEFAULT '',
            telegram_bot_username TEXT DEFAULT 'Billlllllls_bot',
            cloud_server_url TEXT DEFAULT 'https://tripoli-printing.onrender.com',
            cloud_api_key TEXT DEFAULT ''
        );
    """)
    c.execute("PRAGMA table_info(company_settings)")
    settings_cols = [r[1] for r in c.fetchall()]
    if "telegram_bot_token" not in settings_cols:
        c.execute("ALTER TABLE company_settings ADD COLUMN telegram_bot_token TEXT DEFAULT ''")
    if "telegram_admin_id" not in settings_cols:
        c.execute("ALTER TABLE company_settings ADD COLUMN telegram_admin_id TEXT DEFAULT ''")
    if "cloud_server_url" not in settings_cols:
        c.execute("ALTER TABLE company_settings ADD COLUMN cloud_server_url TEXT DEFAULT 'https://tripoli-printing.onrender.com'")
    if "cloud_api_key" not in settings_cols:
        c.execute("ALTER TABLE company_settings ADD COLUMN cloud_api_key TEXT DEFAULT ''")
    if "telegram_bot_username" not in settings_cols:
        c.execute("ALTER TABLE company_settings ADD COLUMN telegram_bot_username TEXT DEFAULT 'Billlllllls_bot'")

    c.execute("SELECT COUNT(*) as cnt FROM company_settings")
    if c.fetchone()["cnt"] == 0:
        c.execute("INSERT INTO company_settings DEFAULT VALUES")
    else:
        c.execute("UPDATE company_settings SET telegram_bot_token = ? WHERE id = 1 AND (telegram_bot_token IS NULL OR telegram_bot_token = '')",
                  ("8658197731:AAEhum8PY1W0-6whvMH6mtH0gbXzNuXpTdI",))

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            full_name TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    c.execute("SELECT COUNT(*) as cnt FROM users")
    if c.fetchone()["cnt"] == 0:
        c.execute("INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                  ("admin", "admin123", "admin", "المدير"))

    conn.commit()
    conn.close()


def add_client(name, phone="", address="", email="", telegram_id=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO clients (name, phone, address, email, telegram_id) VALUES (?, ?, ?, ?, ?)",
              (name, phone, address, email, telegram_id))
    conn.commit()
    client_id = c.lastrowid
    conn.close()
    return client_id


def get_clients():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, phone, address, telegram_id FROM clients ORDER BY name")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_client_by_id(client_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, phone, address, telegram_id FROM clients WHERE id = ?", (client_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_next_invoice_number():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT MAX(invoice_number) as mx FROM invoices")
    row = c.fetchone()
    mx = row["mx"] if row and row["mx"] else ""
    conn.close()
    if mx and mx.startswith("INV-"):
        try:
            last_num = int(mx[4:])
            return f"INV-{last_num + 1:04d}"
        except ValueError:
            pass
    return "INV-0001"


def save_invoice(invoice_number, client_id, date, total_before_discount,
                 discount, total_after_discount, paid_amount, remaining_amount,
                 status, items):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO invoices
            (invoice_number, client_id, date, total_before_discount, discount,
             total_after_discount, paid_amount, remaining_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice_number, client_id, date, total_before_discount,
              discount, total_after_discount, paid_amount, remaining_amount, status))
        invoice_id = c.lastrowid
        for item in items:
            c.execute("""
                INSERT INTO invoice_items
                (invoice_id, service_type, length, width, area, unit_price,
                 quantity, installation_fee, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id, item["service_type"], item["length"], item["width"],
                item["area"], item["unit_price"], item["quantity"],
                item.get("installation_fee", 0), item["total"]
            ))
        conn.commit()
        return invoice_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_attachment(invoice_id, path):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE invoices SET attachment_path = ? WHERE id = ?", (path, invoice_id))
    conn.commit()
    conn.close()


def get_invoice_by_id(invoice_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT i.*, c.name as client_name, c.phone as client_phone,
                 c.address as client_address
                 FROM invoices i JOIN clients c ON i.client_id = c.id
                 WHERE i.id = ?""", (invoice_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_invoice_items(invoice_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def search_invoices(invoice_number="", client_name="", date_from="",
                    date_to="", status=""):
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT i.*, c.name as client_name
        FROM invoices i
        JOIN clients c ON i.client_id = c.id
        WHERE 1=1
    """
    params = []
    if invoice_number:
        query += " AND i.invoice_number LIKE ?"
        params.append(f"%{invoice_number}%")
    if client_name:
        query += " AND c.name LIKE ?"
        params.append(f"%{client_name}%")
    if date_from:
        query += " AND i.date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND i.date <= ?"
        params.append(date_to)
    if status:
        query += " AND i.status LIKE ?"
        params.append(f"%{status}%")
    query += " ORDER BY i.created_at DESC"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def delete_invoice(invoice_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()


def update_invoice(invoice_id, client_id, date, total_before_discount,
                   discount, total_after_discount, paid_amount, remaining_amount,
                   status, items):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE invoices SET client_id=?, date=?, total_before_discount=?,
                discount=?, total_after_discount=?, paid_amount=?,
                remaining_amount=?, status=?
            WHERE id=?
        """, (client_id, date, total_before_discount, discount,
              total_after_discount, paid_amount, remaining_amount, status, invoice_id))
        c.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        for item in items:
            c.execute("""
                INSERT INTO invoice_items
                (invoice_id, service_type, length, width, area, unit_price,
                 quantity, installation_fee, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id, item["service_type"], item["length"], item["width"],
                item["area"], item["unit_price"], item["quantity"],
                item["installation_fee"], item["total"]
            ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_all_invoices_summary():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT i.id, i.invoice_number, i.date, i.total_after_discount,
               i.paid_amount, i.remaining_amount, i.status,
               c.name as client_name, c.address as client_address
        FROM invoices i
        JOIN clients c ON i.client_id = c.id
        ORDER BY i.date DESC, i.id DESC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def add_material(name, unit="متر", quantity=0, min_qty=5, price=0, notes=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO materials (name, unit, current_quantity, min_quantity, unit_price, notes)
                 VALUES (?, ?, ?, ?, ?, ?)""", (name, unit, quantity, min_qty, price, notes))
    conn.commit()
    mid = c.lastrowid
    conn.close()
    return mid


def get_materials():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM materials ORDER BY name")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_material(material_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM materials WHERE id = ?", (material_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def update_material(material_id, name, unit, min_qty, price, notes):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE materials SET name=?, unit=?, min_quantity=?,
                 unit_price=?, notes=? WHERE id=?""",
              (name, unit, min_qty, price, notes, material_id))
    conn.commit()
    conn.close()


def delete_material(material_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()


def add_material_transaction(material_id, change_amount, trans_type,
                             date, invoice_id=None, notes=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO material_transactions
                 (material_id, invoice_id, change_amount, transaction_type, date, notes)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (material_id, invoice_id, change_amount, trans_type, date, notes))
    c.execute("UPDATE materials SET current_quantity = current_quantity + ? WHERE id = ?",
              (change_amount, material_id))
    conn.commit()
    conn.close()


def get_material_transactions(material_id=None, invoice_id=None):
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT mt.*, m.name as material_name, m.unit,
               i.invoice_number
        FROM material_transactions mt
        JOIN materials m ON mt.material_id = m.id
        LEFT JOIN invoices i ON mt.invoice_id = i.id
        WHERE 1=1
    """
    params = []
    if material_id:
        query += " AND mt.material_id = ?"
        params.append(material_id)
    if invoice_id:
        query += " AND mt.invoice_id = ?"
        params.append(invoice_id)
    query += " ORDER BY mt.date DESC, mt.id DESC"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_low_stock_materials():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM materials WHERE current_quantity <= min_quantity ORDER BY name")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_material_consumption_summary(invoice_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT mt.*, m.name as material_name, m.unit
                 FROM material_transactions mt
                 JOIN materials m ON mt.material_id = m.id
                 WHERE mt.invoice_id = ? AND mt.transaction_type = 'consume'
                 ORDER BY mt.id""", (invoice_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_services():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, default_price FROM services ORDER BY name")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def add_service(name, price=0):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO services (name, default_price) VALUES (?, ?)", (name, price))
        conn.commit()
        sid = c.lastrowid
        conn.close()
        return sid
    except Exception:
        conn.rollback()
        conn.close()
        return None


def delete_service(service_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM services WHERE id = ?", (service_id,))
    conn.commit()
    conn.close()


def get_company_settings():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM company_settings WHERE id = 1")
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {
        "company_name": "شركتي",
        "phone1": "", "phone2": "", "address": "",
        "currency": "د.ل",
        "invoice_notes": "البضاعة التي تفصل لا ترد ولا تستبدل.",
        "telegram_bot_token": "",
        "telegram_admin_id": "",
        "telegram_bot_username": "Billlllllls_bot",
        "cloud_server_url": "https://tripoli-printing.onrender.com",
        "cloud_api_key": ""
    }


def save_company_settings(company_name, phone1, phone2, address, currency, invoice_notes, telegram_bot_token="", telegram_admin_id="", cloud_server_url="", cloud_api_key="", telegram_bot_username=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE company_settings SET
            company_name=?, phone1=?, phone2=?, address=?,
            currency=?, invoice_notes=?, telegram_bot_token=?, telegram_admin_id=?,
            cloud_server_url=?, cloud_api_key=?, telegram_bot_username=?
        WHERE id=1
    """, (company_name, phone1, phone2, address, currency, invoice_notes, telegram_bot_token, telegram_admin_id, cloud_server_url, cloud_api_key, telegram_bot_username))
    conn.commit()
    conn.close()


def verify_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, full_name FROM users WHERE username=? AND password=?", (username, password))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, full_name, created_at FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_by_username(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def add_user(username, password, role, full_name):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                  (username, password, role, full_name))
        conn.commit()
        return True, "تمت الإضافة بنجاح"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_user(user_id, username, password, role, full_name):
    conn = get_connection()
    c = conn.cursor()
    try:
        if password:
            c.execute("UPDATE users SET username=?, password=?, role=?, full_name=? WHERE id=?",
                      (username, password, role, full_name, user_id))
        else:
            c.execute("UPDATE users SET username=?, role=?, full_name=? WHERE id=?",
                      (username, role, full_name, user_id))
        conn.commit()
        return True, "تم التحديث بنجاح"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def delete_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) as cnt FROM users WHERE role='admin'")
        admin_count = c.fetchone()["cnt"]
        c.execute("SELECT role FROM users WHERE id=?", (user_id,))
        user = c.fetchone()
        if user and user["role"] == "admin" and admin_count <= 1:
            return False, "لا يمكن حذف آخر مشرف"
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        return True, "تم الحذف بنجاح"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def change_user_password(user_id, current_password, new_password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    if not row or row["password"] != current_password:
        conn.close()
        return False, "كلمة المرور الحالية غير صحيحة"
    c.execute("UPDATE users SET password=? WHERE id=?", (new_password, user_id))
    conn.commit()
    conn.close()
    return True, "تم تغيير كلمة المرور بنجاح"


def log_telegram_send(invoice_id, invoice_number, client_id, client_name, telegram_id, status, message=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO telegram_log (invoice_id, invoice_number, client_id, client_name, telegram_id, status, message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (invoice_id, invoice_number, client_id, client_name, str(telegram_id), status, message))
    conn.commit()
    conn.close()


def get_telegram_logs(limit=50):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT tl.*, c.name as client_name
        FROM telegram_log tl
        LEFT JOIN clients c ON tl.client_id = c.id
        ORDER BY tl.created_at DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def save_secure_code(invoice_id, code):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE invoices SET telegram_secure_code = ? WHERE id = ?", (code, invoice_id))
    conn.commit()
    conn.close()


def find_invoice_by_secure_code(code):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT i.*, c.name as client_name, c.phone as client_phone,
               c.address as client_address, c.telegram_id as client_telegram_id
        FROM invoices i JOIN clients c ON i.client_id = c.id
        WHERE i.telegram_secure_code = ? AND i.telegram_secure_code IS NOT NULL
        LIMIT 1
    """, (code,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def invalidate_secure_code(invoice_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE invoices SET telegram_secure_code = NULL WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()
