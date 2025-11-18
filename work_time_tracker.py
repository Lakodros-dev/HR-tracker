"""
Ish vaqti kuzatuvi - kechikish, ish vaqti, yo'qlik
"""
import logging
from datetime import datetime, time, timedelta
from telegram.ext import ContextTypes

from database import Database
import config

logger = logging.getLogger(__name__)
db = Database()


def calculate_late_minutes(check_in_time: datetime, work_start_hour: int) -> int:
    """Kechikish daqiqalarini hisoblash"""
    work_start = check_in_time.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
    
    if check_in_time > work_start:
        late = (check_in_time - work_start).total_seconds() / 60
        return int(late)
    return 0


def calculate_work_minutes(locations: list, work_hours: dict, lunch_hours: dict) -> tuple:
    """Ish vaqti va yo'qlik daqiqalarini hisoblash"""
    if not locations:
        return 0, 0
    
    work_minutes = 0
    absent_minutes = 0
    
    # Ish vaqti davomiyligi (daqiqalarda)
    total_work_minutes = (work_hours['end'] - work_hours['start']) * 60
    lunch_duration = (lunch_hours['end'] - lunch_hours['start']) * 60
    expected_work_minutes = total_work_minutes - lunch_duration
    
    # Har bir lokatsiya orasidagi vaqtni hisoblash
    for i in range(len(locations) - 1):
        current = datetime.fromisoformat(locations[i]['timestamp'])
        next_loc = datetime.fromisoformat(locations[i+1]['timestamp'])
        
        # Vaqt farqi (daqiqalarda)
        diff_minutes = (next_loc - current).total_seconds() / 60
        
        # Agar lokatsiya ofisda bo'lsa
        if locations[i]['is_valid']:
            work_minutes += diff_minutes
        else:
            absent_minutes += diff_minutes
    
    return int(work_minutes), int(absent_minutes)


async def send_end_of_day_stats(context: ContextTypes.DEFAULT_TYPE):
    """Ish kuni oxirida statistika yuborish"""
    logger.info("📊 Ish kuni statistikasi yuborilmoqda")
    
    employees = db.get_all_employees()
    work_hours = config.get_work_hours_config()
    lunch_hours = config.get_lunch_hours_config()
    
    for employee in employees:
        user_id = employee['user_id']
        name = employee.get('name', 'Hodim')
        
        # Adminni o'tkazib yuborish
        if config.is_admin(user_id):
            continue
        
        # Faqat tasdiqlangan hodimlar uchun
        if not db.is_approved(user_id):
            continue
        
        try:
            # Bugungi lokatsiyalarni olish
            today_locations = db.get_today_report(user_id)
            
            if not today_locations:
                # Lokatsiya yuborilmagan
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🌆 Ish kuni tugadi, {name}!\n\n"
                         f"⚠️ Bugun lokatsiya yuborilmagan.\n"
                         f"❌ Yo'qlik: {(work_hours['end'] - work_hours['start']) * 60} daqiqa\n\n"
                         f"Xayr! Ertaga ko'rishguncha! 👋"
                )
                continue
            
            # Birinchi lokatsiya - kechikish
            first_location = today_locations[0]
            first_time = datetime.fromisoformat(first_location['timestamp'])
            late_minutes = calculate_late_minutes(first_time, work_hours['start'])
            
            # Ish vaqti va yo'qlik
            work_minutes, absent_minutes = calculate_work_minutes(
                today_locations, work_hours, lunch_hours
            )
            
            # Statistikani saqlash
            db.update_work_stats(user_id, late_minutes, work_minutes, absent_minutes)
            
            # Xabar tayyorlash
            message = f"🌆 Ish kuni tugadi, {name}!\n\n"
            message += f"📊 Bugungi natijalar:\n\n"
            
            if late_minutes > 0:
                message += f"⏰ Kechikish: {late_minutes} daqiqa\n"
            else:
                message += f"✅ Kechikish yo'q\n"
            
            message += f"💼 Ish vaqti: {work_minutes} daqiqa ({work_minutes // 60} soat {work_minutes % 60} daqiqa)\n"
            
            if absent_minutes > 0:
                message += f"❌ Yo'qlik: {absent_minutes} daqiqa\n"
            
            message += f"\n📍 Lokatsiyalar: {len(today_locations)} ta\n"
            message += f"✅ Ofisda: {sum(1 for loc in today_locations if loc['is_valid'])} ta\n"
            message += f"❌ Tashqarida: {sum(1 for loc in today_locations if not loc['is_valid'])} ta\n\n"
            message += f"Xayr! Ertaga ko'rishguncha! 👋"
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message
            )
            
            logger.info(f"✅ Statistika yuborildi: {name} ({user_id})")
            
        except Exception as e:
            logger.error(f"❌ Xatolik ({user_id}): {e}")


async def check_location_during_work(update, context):
    """Ish vaqtida lokatsiya yuborilganda tekshirish"""
    user_id = update.effective_user.id
    
    # Ish vaqtimi?
    if not config.is_work_hours():
        await update.message.reply_text(
            "⏰ Hozirda sizning ish vaqtingiz tugagan.\n\n"
            "Ish vaqti: {}-{}\n"
            "Hozirgi vaqt: {}".format(
                config.get_work_hours_config()['start'],
                config.get_work_hours_config()['end'],
                datetime.now().strftime("%H:%M")
            )
        )
        return False
    
    return True


async def check_first_location_of_day(user_id: int, location_time: datetime, context: ContextTypes.DEFAULT_TYPE):
    """Kunning birinchi lokatsiyasi - kechikishni tekshirish"""
    work_hours = config.get_work_hours_config()
    late_minutes = calculate_late_minutes(location_time, work_hours['start'])
    
    if late_minutes > 0:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"⏰ Kechikish!\n\n"
                     f"Siz {late_minutes} daqiqa kechikdingiz.\n"
                     f"Ish boshlanish vaqti: {work_hours['start']}:00\n"
                     f"Sizning vaqtingiz: {location_time.strftime('%H:%M')}"
            )
        except Exception as e:
            logger.error(f"Kechikish xabarini yuborishda xato: {e}")
    else:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Vaqtida keldingiz!\n\n"
                     f"Yaxshi ish kuni! 💼"
            )
        except Exception as e:
            logger.error(f"Xabar yuborishda xato: {e}")
