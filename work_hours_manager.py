"""
Hodimlarning individual ish vaqtlarini boshqarish
"""
import json
import os
from datetime import datetime

WORK_HOURS_FILE = 'employee_work_hours.json'


def load_employee_work_hours():
    """Barcha hodimlarning ish vaqtlarini yuklash"""
    if not os.path.exists(WORK_HOURS_FILE):
        return {}
    
    try:
        with open(WORK_HOURS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ish vaqtlarini yuklashda xato: {e}")
        return {}


def save_employee_work_hours(work_hours_data):
    """Ish vaqtlarini faylga saqlash"""
    try:
        with open(WORK_HOURS_FILE, 'w', encoding='utf-8') as f:
            json.dump(work_hours_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Ish vaqtlarini saqlashda xato: {e}")
        return False


def set_employee_work_hours(user_id, work_start, work_end, username=None, full_name=None):
    """Hodim uchun ish vaqtini o'rnatish"""
    work_hours = load_employee_work_hours()
    
    work_hours[str(user_id)] = {
        'work_start': work_start,
        'work_end': work_end,
        'user_id': user_id,
        'username': username,
        'full_name': full_name,
        'updated_at': datetime.now().isoformat()
    }
    
    return save_employee_work_hours(work_hours)


def get_employee_work_hours(user_id):
    """Hodimning ish vaqtini olish"""
    work_hours = load_employee_work_hours()
    return work_hours.get(str(user_id))


def is_employee_work_hours(user_id, current_hour=None):
    """Hodim hozir ish vaqtida ekanligini tekshirish"""
    if current_hour is None:
        current_hour = datetime.now().hour
    
    work_hours = get_employee_work_hours(user_id)
    if not work_hours:
        return False
    
    return work_hours['work_start'] <= current_hour < work_hours['work_end']


def get_all_employee_work_hours():
    """Barcha hodimlarning ish vaqtlarini olish"""
    return load_employee_work_hours()


def delete_employee_work_hours(user_id):
    """Hodimning ish vaqtini o'chirish"""
    work_hours = load_employee_work_hours()
    
    if str(user_id) in work_hours:
        del work_hours[str(user_id)]
        return save_employee_work_hours(work_hours)
    
    return False
