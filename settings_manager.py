"""
JSON bazaga sozlamalarni saqlash va o'qish
"""
import json
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

SETTINGS_FILE = 'settings.json'
BACKEND_URL = os.getenv('BACKEND_URL', 'https://map-for-marking-domain-1.onrender.com')

# Cache uchun
_settings_cache = None
_cache_time = None
CACHE_DURATION = 30  # 30 soniya


def load_settings_from_backend():
    """Render serveridan sozlamalarni yuklash"""
    try:
        response = requests.get(f'{BACKEND_URL}/api/settings', timeout=5)
        if response.status_code == 200:
            settings = response.json()
            print(f"✅ Sozlamalar Render serveridan yuklandi")
            # Local faylga ham saqlash (backup)
            save_settings(settings)
            return settings
        else:
            print(f"⚠️ Backend dan sozlamalar olinmadi: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Backend ga ulanib bo'lmadi: {e}")
        return None


def load_settings():
    """Sozlamalarni yuklash (cache bilan)"""
    global _settings_cache, _cache_time
    
    # Cache tekshirish
    if _settings_cache and _cache_time:
        if datetime.now() - _cache_time < timedelta(seconds=CACHE_DURATION):
            return _settings_cache
    
    # Cache eski yoki yo'q - yangi ma'lumot olish
    backend_settings = load_settings_from_backend()
    if backend_settings:
        _settings_cache = backend_settings
        _cache_time = datetime.now()
        return backend_settings
    
    # Agar backend ishlamasa, local fayldan o'qish
    print("📁 Local settings.json dan o'qilmoqda...")
    if not os.path.exists(SETTINGS_FILE):
        return get_default_settings()
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            _settings_cache = settings
            _cache_time = datetime.now()
            return settings
    except Exception as e:
        print(f"Sozlamalarni yuklashda xato: {e}")
        return get_default_settings()


def clear_cache():
    """Cache ni tozalash (yangi ma'lumot olish uchun)"""
    global _settings_cache, _cache_time
    _settings_cache = None
    _cache_time = None
    print("🔄 Settings cache tozalandi")


def save_settings(settings):
    """Sozlamalarni saqlash"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Sozlamalarni saqlashda xato: {e}")
        return False


def get_default_settings():
    """Default sozlamalar"""
    return {
        "office_location": {
            "latitude": 41.2995,
            "longitude": 69.2401,
            "radius": 100
        },
        "office_area": {
            "point1": {"lat": 41.2995, "lng": 69.2401},
            "point2": {"lat": 41.3005, "lng": 69.2411}
        },
        "use_area_mode": False,
        "work_hours": {
            "start": 8,
            "end": 20
        },
        "lunch_hours": {
            "start": 12,
            "end": 13
        },
        "location_interval": {
            "minutes": 30,
            "grace_period": 5
        }
    }


def update_office_location(latitude, longitude, radius=100):
    """Ofis lokatsiyasini yangilash"""
    settings = load_settings()
    settings['office_location'] = {
        'latitude': latitude,
        'longitude': longitude,
        'radius': radius
    }
    settings['use_area_mode'] = False
    return save_settings(settings)


def update_office_area(point1, point2):
    """Ofis hududini yangilash"""
    settings = load_settings()
    settings['office_area'] = {
        'point1': point1,
        'point2': point2
    }
    settings['use_area_mode'] = True
    return save_settings(settings)


def update_work_hours(start, end):
    """Ish vaqtini yangilash"""
    settings = load_settings()
    settings['work_hours'] = {
        'start': start,
        'end': end
    }
    return save_settings(settings)


def update_lunch_hours(start, end):
    """Tushlik vaqtini yangilash"""
    settings = load_settings()
    settings['lunch_hours'] = {
        'start': start,
        'end': end
    }
    return save_settings(settings)


def update_location_interval(minutes, grace_period):
    """Lokatsiya oralig'ini yangilash"""
    settings = load_settings()
    settings['location_interval'] = {
        'minutes': minutes,
        'grace_period': grace_period
    }
    return save_settings(settings)


def get_office_location():
    """Ofis lokatsiyasini olish"""
    settings = load_settings()
    return settings.get('office_location', get_default_settings()['office_location'])


def get_office_area():
    """Ofis hududini olish"""
    settings = load_settings()
    return settings.get('office_area', get_default_settings()['office_area'])


def is_area_mode():
    """Hudud rejimi faolmi?"""
    settings = load_settings()
    return settings.get('use_area_mode', False)


def get_work_hours():
    """Ish vaqtini olish"""
    settings = load_settings()
    return settings.get('work_hours', get_default_settings()['work_hours'])


def get_lunch_hours():
    """Tushlik vaqtini olish"""
    settings = load_settings()
    return settings.get('lunch_hours', get_default_settings()['lunch_hours'])


def get_location_interval():
    """Lokatsiya oralig'ini olish"""
    settings = load_settings()
    return settings.get('location_interval', get_default_settings()['location_interval'])
