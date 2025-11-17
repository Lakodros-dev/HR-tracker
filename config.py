import os
from dotenv import load_dotenv

load_dotenv()

# Statik sozlamalar (.env dan)
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
MINI_APP_URL = os.getenv('MINI_APP_URL', '')

# JSON bazadan sozlamalarni yuklash
from settings_manager import (
    get_office_location, get_office_area, is_area_mode,
    get_work_hours, get_lunch_hours, get_location_interval
)

# Dinamik sozlamalar (har safar yangi qiymat)
def get_office_config():
    """Ofis konfiguratsiyasini olish"""
    loc = get_office_location()
    return {
        'latitude': loc['latitude'],
        'longitude': loc['longitude'],
        'radius': loc['radius']
    }

def get_work_hours_config():
    """Ish vaqti konfiguratsiyasini olish"""
    return get_work_hours()

def get_lunch_hours_config():
    """Tushlik vaqti konfiguratsiyasini olish"""
    return get_lunch_hours()

def get_interval_config():
    """Interval konfiguratsiyasini olish"""
    return get_location_interval()

def get_area_points():
    """Hudud nuqtalarini olish"""
    area = get_office_area()
    return area['point1'], area['point2']

def is_area_mode_enabled():
    """Hudud rejimi faolmi?"""
    return is_area_mode()

def is_work_hours() -> bool:
    """Hozir ish vaqtimi?"""
    from datetime import datetime
    now = datetime.now()
    hour = now.hour
    work_hours = get_work_hours()
    return work_hours['start'] <= hour < work_hours['end']

def is_lunch_time() -> bool:
    """Hozir tushlik vaqtimi?"""
    from datetime import datetime
    now = datetime.now()
    hour = now.hour
    lunch_hours = get_lunch_hours()
    return lunch_hours['start'] <= hour < lunch_hours['end']

# Backward compatibility (eski kod uchun)
# Bu qiymatlar faqat bot ishga tushganda yuklanadi
_office_loc = get_office_location()
OFFICE_LATITUDE = _office_loc['latitude']
OFFICE_LONGITUDE = _office_loc['longitude']
ALLOWED_DISTANCE = _office_loc['radius']

_work_hours = get_work_hours()
WORK_START_HOUR = _work_hours['start']
WORK_END_HOUR = _work_hours['end']

_lunch_hours = get_lunch_hours()
LUNCH_START_HOUR = _lunch_hours['start']
LUNCH_END_HOUR = _lunch_hours['end']

_interval = get_location_interval()
LOCATION_INTERVAL_MINUTES = _interval['minutes']
LOCATION_GRACE_PERIOD_MINUTES = _interval['grace_period']

USE_AREA_MODE = is_area_mode()
