from geopy.distance import geodesic
from datetime import datetime
import config

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Ikki nuqta orasidagi masofani metrda hisoblash"""
    return geodesic((lat1, lon1), (lat2, lon2)).meters

def is_location_valid(lat: float, lon: float) -> tuple[bool, float]:
    """Lokatsiya ofis hududida ekanligini tekshirish"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Dinamik ravishda tekshirish
    use_area_mode = config.is_area_mode_enabled()
    logger.info(f"USE_AREA_MODE: {use_area_mode}")
    
    if use_area_mode:
        logger.info("To'rtburchak hudud rejimi ishlatilmoqda")
        return is_location_in_area(lat, lon)
    else:
        logger.info("Doira rejimi ishlatilmoqda")
        office_config = config.get_office_config()
        distance = calculate_distance(lat, lon, office_config['latitude'], office_config['longitude'])
        is_valid = distance <= office_config['radius']
        return is_valid, distance


def is_location_in_area(lat: float, lon: float) -> tuple[bool, float]:
    """Lokatsiya to'rtburchak hududda ekanligini tekshirish"""
    import logging
    logger = logging.getLogger(__name__)
    
    point1, point2 = config.get_area_points()
    
    # To'rtburchak chegaralarini hisoblash
    min_lat = min(point1['lat'], point2['lat'])
    max_lat = max(point1['lat'], point2['lat'])
    min_lng = min(point1['lng'], point2['lng'])
    max_lng = max(point1['lng'], point2['lng'])
    
    # Debug log
    logger.info(f"Lokatsiya tekshirilmoqda:")
    logger.info(f"  Hodim: lat={lat}, lng={lon}")
    logger.info(f"  Hudud: lat=[{min_lat}, {max_lat}], lng=[{min_lng}, {max_lng}]")
    logger.info(f"  Lat tekshirish: {min_lat} <= {lat} <= {max_lat} = {min_lat <= lat <= max_lat}")
    logger.info(f"  Lng tekshirish: {min_lng} <= {lon} <= {max_lng} = {min_lng <= lon <= max_lng}")
    
    # Lokatsiya hudud ichida ekanligini tekshirish
    is_valid = (min_lat <= lat <= max_lat) and (min_lng <= lon <= max_lng)
    
    logger.info(f"  Natija: {'✅ Ofis ichida' if is_valid else '❌ Ofis tashqarida'}")
    
    # Hudud markazigacha masofani hisoblash
    center_lat = (min_lat + max_lat) / 2
    center_lng = (min_lng + max_lng) / 2
    distance = calculate_distance(lat, lon, center_lat, center_lng)
    
    return is_valid, distance

def is_work_hours() -> bool:
    """Hozir ish vaqtimi?"""
    from datetime import datetime
    now = datetime.now()
    hour = now.hour
    work_hours = config.get_work_hours_config()
    return work_hours['start'] <= hour < work_hours['end']

def is_lunch_time() -> bool:
    """Hozir tushlik vaqtimi?"""
    now = datetime.now()
    hour = now.hour
    lunch_hours = config.get_lunch_hours_config()
    return lunch_hours['start'] <= hour < lunch_hours['end']

def format_time(iso_time: str) -> str:
    """Vaqtni chiroyli formatda ko'rsatish"""
    if not iso_time:
        return "Yo'q"
    dt = datetime.fromisoformat(iso_time)
    return dt.strftime("%H:%M:%S")

def format_date(iso_time: str) -> str:
    """Sanani chiroyli formatda ko'rsatish"""
    if not iso_time:
        return "Yo'q"
    dt = datetime.fromisoformat(iso_time)
    return dt.strftime("%d.%m.%Y %H:%M")
