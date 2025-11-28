"""
Kunlik ish soatlarini hisoblash va tracking
"""
from datetime import datetime, timedelta
from database import Database
from work_hours_manager import get_employee_work_hours

db = Database()


def calculate_time_difference_hours(start_time_str, end_time_str):
    """Ikki vaqt orasidagi farqni soatlarda hisoblash"""
    try:
        start = datetime.fromisoformat(start_time_str)
        end = datetime.fromisoformat(end_time_str)
        diff = end - start
        return diff.total_seconds() / 3600  # Soatlarga aylantirish
    except:
        return 0


def calculate_daily_work_hours(user_id, date_str=None):
    """
    Kunlik ish soatlarini hisoblash
    
    Logika:
    1. Birinchi lokatsiya = Ishga kelgan vaqt
    2. Oxirgi lokatsiya = Ketgan vaqt
    3. Har bir lokatsiya orasidagi interval tekshiriladi
    4. Agar interval > belgilangan vaqt + grace period, u vaqt "ish joyida emas" hisoblanadi
    5. Jami ish soati = (Ketgan - Kelgan) - (Ish joyida bo'lmagan vaqt)
    """
    if date_str is None:
        date_str = datetime.now().date().isoformat()
    
    # Kunlik lokatsiyalarni olish
    logs = db.get_today_report(user_id) if date_str == datetime.now().date().isoformat() else get_date_locations(user_id, date_str)
    
    if not logs or len(logs) == 0:
        # Lokatsiya yo'q - 0 soat
        db.save_daily_work_hours(
            user_id=user_id,
            date=date_str,
            total_work_hours=0,
            present_hours=0,
            absent_hours=0,
            total_locations=0,
            valid_locations=0
        )
        return {
            'total_work_hours': 0,
            'present_hours': 0,
            'absent_hours': 0,
            'work_start_time': None,
            'work_end_time': None
        }
    
    # Birinchi va oxirgi lokatsiya
    first_location = logs[0]
    last_location = logs[-1]
    
    work_start_time = first_location['timestamp']
    work_end_time = last_location['timestamp']
    
    # Jami vaqt (kelgan - ketgan)
    total_time_hours = calculate_time_difference_hours(work_start_time, work_end_time)
    
    # Lokatsiya oralig'idagi bo'shliqlarni hisoblash
    from settings_manager import get_location_interval
    interval_config = get_location_interval()
    expected_interval_minutes = interval_config['minutes']
    grace_period_minutes = interval_config['grace_period']
    max_allowed_gap_minutes = expected_interval_minutes + grace_period_minutes
    
    absent_hours = 0
    
    # Har bir lokatsiya orasidagi vaqtni tekshirish
    for i in range(len(logs) - 1):
        current_log = logs[i]
        next_log = logs[i + 1]
        
        current_time = datetime.fromisoformat(current_log['timestamp'])
        next_time = datetime.fromisoformat(next_log['timestamp'])
        
        gap_minutes = (next_time - current_time).total_seconds() / 60
        
        # Agar gap > max_allowed_gap, bu vaqt "ish joyida emas"
        if gap_minutes > max_allowed_gap_minutes:
            # Gap dan max_allowed_gap ni ayiramiz (chunki max_allowed_gap normal hisoblanadi)
            absent_minutes = gap_minutes - max_allowed_gap_minutes
            absent_hours += absent_minutes / 60
    
    # Ish joyida bo'lgan vaqt
    present_hours = total_time_hours - absent_hours
    
    # Valid lokatsiyalar soni
    valid_locations = sum(1 for log in logs if log['is_valid'])
    
    # Bazaga saqlash
    db.save_daily_work_hours(
        user_id=user_id,
        date=date_str,
        work_start_time=work_start_time,
        work_end_time=work_end_time,
        total_work_hours=round(total_time_hours, 2),
        present_hours=round(present_hours, 2),
        absent_hours=round(absent_hours, 2),
        total_locations=len(logs),
        valid_locations=valid_locations
    )
    
    return {
        'total_work_hours': round(total_time_hours, 2),
        'present_hours': round(present_hours, 2),
        'absent_hours': round(absent_hours, 2),
        'work_start_time': work_start_time,
        'work_end_time': work_end_time,
        'total_locations': len(logs),
        'valid_locations': valid_locations
    }


def get_date_locations(user_id, date_str):
    """Berilgan sanadagi lokatsiyalarni olish"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT latitude, longitude, distance, is_valid, timestamp
        FROM location_logs 
        WHERE user_id = ? AND DATE(timestamp) = ?
        ORDER BY timestamp
    ''', (user_id, date_str))
    results = cursor.fetchall()
    conn.close()
    
    return [{
        'latitude': r[0],
        'longitude': r[1],
        'distance': r[2],
        'is_valid': bool(r[3]),
        'timestamp': r[4]
    } for r in results]


def update_daily_work_hours_for_user(user_id):
    """Foydalanuvchi uchun bugungi ish soatlarini yangilash"""
    today = datetime.now().date().isoformat()
    return calculate_daily_work_hours(user_id, today)


def get_monthly_report(user_id, start_date_str, end_date_str):
    """
    Oylik hisobot olish
    
    Args:
        user_id: Foydalanuvchi ID
        start_date_str: Boshlanish sanasi (YYYY-MM-DD)
        end_date_str: Tugash sanasi (YYYY-MM-DD)
    
    Returns:
        dict: Oylik hisobot ma'lumotlari
    """
    # Sana oralig'idagi ma'lumotlarni olish
    daily_records = db.get_work_hours_range(user_id, start_date_str, end_date_str)
    
    if not daily_records:
        return {
            'user_id': user_id,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'total_days': 0,
            'total_work_hours': 0,
            'total_present_hours': 0,
            'total_absent_hours': 0,
            'efficiency_percent': 0,
            'daily_details': []
        }
    
    # Jami hisoblar
    total_work_hours = sum(r['total_work_hours'] for r in daily_records)
    total_present_hours = sum(r['present_hours'] for r in daily_records)
    total_absent_hours = sum(r['absent_hours'] for r in daily_records)
    
    return {
        'user_id': user_id,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'total_days': len(daily_records),
        'total_work_hours': round(total_work_hours, 2),
        'total_present_hours': round(total_present_hours, 2),
        'total_absent_hours': round(total_absent_hours, 2),
        'efficiency_percent': round((total_present_hours / total_work_hours * 100) if total_work_hours > 0 else 0, 1),
        'daily_details': daily_records
    }
