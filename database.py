"""
Database definitions for User Management.
Using SQLite for persistence.

Copyright © CTDOTEAM - Đỗ Thành #1110
This module is provided AS-IS without warranties.
Use only for authorized testing purposes.
The author is NOT responsible for misuse, legal consequences, or damages.
"""

import sqlite3
import time
from datetime import datetime, timedelta

DB_NAME = "bot_users.db"

def init_db():
    """Initialize database tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        vip_expiry TEXT,
        daily_limit INTEGER DEFAULT 0,
        usage_today INTEGER DEFAULT 0,
        last_reset_date TEXT,
        user_role TEXT DEFAULT 'none'
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('public_mode', 'off')")
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN user_role TEXT DEFAULT 'none'")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.cursor = self.conn.cursor()
        init_db()
    
    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return self.cursor.fetchone()
    
    def add_user(self, user_id):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            # Default limit is 0 (Inactive)
            self.cursor.execute(
                "INSERT INTO users (user_id, daily_limit, usage_today, last_reset_date) VALUES (?, ?, ?, ?)",
                (user_id, 0, 0, today)
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass
            
    def activate_user(self, user_id):
        """Activate a user as Free (limit 50)."""
        if not self.get_user(user_id):
            self.add_user(user_id)
            
        self.cursor.execute(
            "UPDATE users SET daily_limit=50, vip_expiry=NULL, user_role='free' WHERE user_id=?",
            (user_id,)
        )
        self.conn.commit()
    
    def set_vip(self, user_id, days):
        """Set user as VIP (200/day, no delay)."""
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.get_user(user_id):
            self.add_user(user_id)
            
        self.cursor.execute(
            "UPDATE users SET vip_expiry=?, daily_limit=200, user_role='vip' WHERE user_id=?",
            (expiry, user_id)
        )
        self.conn.commit()
        return expiry
    
    def set_premium(self, user_id, days):
        """Set user as Premium (2000/day, no delay)."""
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.get_user(user_id):
            self.add_user(user_id)
            
        self.cursor.execute(
            "UPDATE users SET vip_expiry=?, daily_limit=2000, user_role='premium' WHERE user_id=?",
            (expiry, user_id)
        )
        self.conn.commit()
        return expiry
    
    def get_all_user_ids(self):
        """Get all user IDs for notification."""
        self.cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_public_mode(self):
        """Get current public mode status."""
        self.cursor.execute("SELECT value FROM settings WHERE key='public_mode'")
        result = self.cursor.fetchone()
        return result[0] == 'on' if result else False
    
    def set_public_mode(self, enabled: bool):
        """Set public mode on/off."""
        value = 'on' if enabled else 'off'
        self.cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('public_mode', ?)",
            (value,)
        )
        self.conn.commit()
        return enabled

    def check_limit(self, user_id, is_admin=False):
        if is_admin:
            return True, "admin"
            
        user = self.get_user(user_id)
        is_new_user = False
        
        if not user:
            self.add_user(user_id)
            user = self.get_user(user_id)
            is_new_user = True
        
        vip_expiry = user[1]
        limit = user[2]
        usage = user[3]
        last_reset = user[4]
        user_role = user[5] if len(user) > 5 else "none"
        
        has_active_subscription = False
        if vip_expiry:
            expiry_date = datetime.strptime(vip_expiry, "%Y-%m-%d %H:%M:%S")
            if expiry_date > datetime.now():
                has_active_subscription = True
            else:
                self.cursor.execute(
                    "UPDATE users SET vip_expiry=NULL, daily_limit=0, user_role='none' WHERE user_id=?", 
                    (user_id,)
                )
                self.conn.commit()
                limit = 0
                user_role = "none"
        
        has_valid_access = False
        
        if user_role == "free" and limit > 0:
            has_valid_access = True
        elif user_role in ["vip", "premium"] and has_active_subscription:
            has_valid_access = True
        
        if not has_valid_access:
            if self.get_public_mode():
                limit = 50
                today = datetime.now().strftime("%Y-%m-%d")
                if last_reset != today:
                    self.cursor.execute(
                        "UPDATE users SET usage_today=0, last_reset_date=? WHERE user_id=?",
                        (today, user_id)
                    )
                    self.conn.commit()
                    usage = 0
                
                if usage >= limit:
                    return False, "limit_reached"
                return True, "public_free"
            else:
                return False, "inactive"
        
        today = datetime.now().strftime("%Y-%m-%d")
        if last_reset != today:
            self.cursor.execute(
                "UPDATE users SET usage_today=0, last_reset_date=? WHERE user_id=?",
                (today, user_id)
            )
            self.conn.commit()
            usage = 0
            
        if usage >= limit:
            return False, "limit_reached"
        
        if user_role == "premium":
            return True, "premium"
        elif user_role == "vip":
            return True, "vip"
        else:
            return True, "free"
        
    def increment_usage(self, user_id):
        self.cursor.execute("UPDATE users SET usage_today = usage_today + 1 WHERE user_id=?", (user_id,))
        self.conn.commit()
    
    def get_remaining_limit(self, user_id, is_admin=False):
        """Get remaining checks for today.
        
        Returns: (remaining, daily_limit, status)
        - admin: (999999, 999999, "admin")
        - premium: (remaining, 2000, "premium")
        - vip: (remaining, 200, "vip")
        - free: (remaining, 50, "free")
        - public_free: (remaining, 50, "public_free")
        - inactive: (0, 0, "inactive")
        """
        if is_admin:
            return 999999, 999999, "admin"
        
        can_check, status = self.check_limit(user_id)
        
        if status == "inactive":
            return 0, 0, "inactive"
        
        user = self.get_user(user_id)
        if not user:
            return 0, 0, "inactive"
        
        usage = user[3]
        
        # Determine limit based on status
        if status == "premium":
            limit = 2000
        elif status == "vip":
            limit = 200
        else:  # free or public_free
            limit = 50
        
        remaining = max(0, limit - usage)
        return remaining, limit, status

# Singleton
db = Database()
