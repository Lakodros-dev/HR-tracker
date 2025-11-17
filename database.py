import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple

class Database:
    def __init__(self, db_name='attendance.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Hodimlar jadvali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_active INTEGER DEFAULT 1,
                is_approved INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Lokatsiya yozuvlari
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS location_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                latitude REAL,
                longitude REAL,
                distance REAL,
                is_valid INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES employees (user_id)
            )
        ''')
        
        # Davomat holati
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_status (
                user_id INTEGER PRIMARY KEY,
                is_present INTEGER DEFAULT 0,
                last_location_time TEXT,
                check_in_time TEXT,
                check_out_time TEXT,
                warnings_count INTEGER DEFAULT 0,
                late_minutes INTEGER DEFAULT 0,
                work_minutes INTEGER DEFAULT 0,
                absent_minutes INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES employees (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    
    def add_employee(self, user_id: int, username: str, full_name: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO employees (user_id, username, full_name)
            VALUES (?, ?, ?)
        ''', (user_id, username, full_name))
        
        cursor.execute('''
            INSERT OR IGNORE INTO attendance_status (user_id)
            VALUES (?)
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def is_employee(self, user_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_active FROM employees WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None and result[0] == 1
    
    def log_location(self, user_id: int, lat: float, lon: float, distance: float, is_valid: bool):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO location_logs (user_id, latitude, longitude, distance, is_valid)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, lat, lon, distance, 1 if is_valid else 0))
        conn.commit()
        conn.close()
    
    def update_attendance_status(self, user_id: int, is_present: bool, location_time: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if is_present:
            cursor.execute('''
                UPDATE attendance_status 
                SET is_present = 1, last_location_time = ?, warnings_count = 0
                WHERE user_id = ?
            ''', (location_time or now, user_id))
        else:
            cursor.execute('''
                UPDATE attendance_status 
                SET is_present = 0
                WHERE user_id = ?
            ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def set_check_in(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE attendance_status 
            SET check_in_time = ?, is_present = 1, warnings_count = 0
            WHERE user_id = ?
        ''', (now, user_id))
        conn.commit()
        conn.close()
    
    def set_check_out(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE attendance_status 
            SET check_out_time = ?, is_present = 0
            WHERE user_id = ?
        ''', (now, user_id))
        conn.commit()
        conn.close()
    
    def get_attendance_status(self, user_id: int) -> Optional[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT is_present, last_location_time, check_in_time, check_out_time, warnings_count
            FROM attendance_status WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'is_present': bool(result[0]),
                'last_location_time': result[1],
                'check_in_time': result[2],
                'check_out_time': result[3],
                'warnings_count': result[4]
            }
        return None
    
    def increment_warning(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE attendance_status 
            SET warnings_count = warnings_count + 1
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        conn.close()
    
    def get_all_active_employees(self) -> List[Tuple[int, str, str]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, full_name 
            FROM employees WHERE is_active = 1
        ''')
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_today_report(self, user_id: int) -> List[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT latitude, longitude, distance, is_valid, timestamp
            FROM location_logs 
            WHERE user_id = ? AND DATE(timestamp) = ?
            ORDER BY timestamp
        ''', (user_id, today))
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'latitude': r[0],
            'longitude': r[1],
            'distance': r[2],
            'is_valid': bool(r[3]),
            'timestamp': r[4]
        } for r in results]
    
    def get_all_employees(self) -> List[dict]:
        """Barcha faol hodimlarni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, full_name 
            FROM employees WHERE is_active = 1
        ''')
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'user_id': r[0],
            'username': r[1],
            'name': r[2]
        } for r in results]
    
    def get_last_location(self, user_id: int) -> Optional[dict]:
        """Oxirgi lokatsiyani olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT latitude, longitude, distance, is_valid, timestamp
            FROM location_logs 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'latitude': result[0],
                'longitude': result[1],
                'distance': result[2],
                'is_valid': bool(result[3]),
                'timestamp': result[4]
            }
        return None
    
    def get_daily_report(self, user_id: int, date) -> Optional[dict]:
        """Kunlik hisobotni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        date_str = date.isoformat() if hasattr(date, 'isoformat') else str(date)
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) as in_office,
                SUM(CASE WHEN is_valid = 0 THEN 1 ELSE 0 END) as out_office
            FROM location_logs 
            WHERE user_id = ? AND DATE(timestamp) = ?
        ''', (user_id, date_str))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] > 0:
            return {
                'total_locations': result[0],
                'in_office_count': result[1],
                'out_office_count': result[2]
            }
        return None
    
    def delete_all_users_except_admin(self, admin_id: int):
        """Admindan tashqari barcha foydalanuvchilarni o'chirish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Lokatsiya loglarini o'chirish
        cursor.execute('DELETE FROM location_logs WHERE user_id != ?', (admin_id,))
        
        # Davomat holatini o'chirish
        cursor.execute('DELETE FROM attendance_status WHERE user_id != ?', (admin_id,))
        
        # Hodimlarni o'chirish
        cursor.execute('DELETE FROM employees WHERE user_id != ?', (admin_id,))
        
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        return deleted
    
    def get_pending_users(self) -> List[dict]:
        """Tasdiqlanmagan foydalanuvchilarni olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, full_name, created_at
            FROM employees 
            WHERE is_approved = 0 AND is_active = 1
        ''')
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'user_id': r[0],
            'username': r[1],
            'name': r[2],
            'created_at': r[3]
        } for r in results]
    
    def approve_user(self, user_id: int):
        """Foydalanuvchini tasdiqlash"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE employees 
            SET is_approved = 1
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        conn.close()
    
    def reject_user(self, user_id: int):
        """Foydalanuvchini rad etish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM location_logs WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM attendance_status WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM employees WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def remove_employee(self, user_id: int):
        """Hodimni tizimdan o'chirish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE employees SET is_active = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def is_approved(self, user_id: int) -> bool:
        """Foydalanuvchi tasdiqlangan-tasdiqlanmaganini tekshirish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_approved FROM employees WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None and result[0] == 1
    
    def update_work_stats(self, user_id: int, late_minutes: int = 0, work_minutes: int = 0, absent_minutes: int = 0):
        """Ish statistikasini yangilash"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE attendance_status 
            SET late_minutes = ?, work_minutes = ?, absent_minutes = ?
            WHERE user_id = ?
        ''', (late_minutes, work_minutes, absent_minutes, user_id))
        conn.commit()
        conn.close()
    
    def get_work_stats(self, user_id: int) -> Optional[dict]:
        """Ish statistikasini olish"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT late_minutes, work_minutes, absent_minutes
            FROM attendance_status WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'late_minutes': result[0] or 0,
                'work_minutes': result[1] or 0,
                'absent_minutes': result[2] or 0
            }
        return None
