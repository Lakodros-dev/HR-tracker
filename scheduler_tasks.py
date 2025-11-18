"""
Avtomatik vazifalar - lokatsiya so'rash, holat tekshirish
"""
import logging
from datetime import datetime, time
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from database import Database
import config

logger = logging.getLogger(__name__)
db = Database()


async def request_morning_location(context: ContextTypes.DEFAULT_TYPE):
    """Ertalab barcha hodimlardan lokatsiya so'rash"""
    logger.info("🌅 Ertalab lokatsiya so'rovi boshlandi")
    
    employees = db.get_all_employees()
    work_hours = config.get_work_hours_config()
    
    for employee in employees:
        user_id = employee['user_id']
        name = employee.get('name', 'Hodim')
        
        # Adminni o'tkazib yuborish
        if user_id == config.ADMIN_ID:
            continue
        
        # Faqat tasdiqlangan hodimlar uchun
        if not db.is_approved(user_id):
            continue
        
        try:
            # Lokatsiya tugmasi
            keyboard = [[KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            message = (
                f"🌅 Xayrli tong, {name}!\n\n"
                f"⏰ Ish vaqti boshlandi ({work_hours['start']}:00)\n"
                f"📍 Iltimos, lokatsiyangizni yuboring.\n\n"
                f"Lokatsiya yuborish uchun pastdagi tugmani bosing."
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=reply_markup
            )
            
            logger.info(f"✅ Lokatsiya so'rovi yuborildi: {name} ({user_id})")
            
        except Exception as e:
            logger.error(f"❌ Xatolik ({user_id}): {e}")


async def check_missing_locations(context: ContextTypes.DEFAULT_TYPE):
    """Lokatsiya yubormaganlarni tekshirish"""
    logger.info("🔍 Lokatsiya yubormaganlar tekshirilmoqda")
    
    employees = db.get_all_employees()
    today = datetime.now().date()
    work_hours = config.get_work_hours_config()
    grace_period = config.get_interval_config()['grace_period']
    
    for employee in employees:
        user_id = employee['user_id']
        name = employee.get('name', 'Hodim')
        
        # Adminni o'tkazib yuborish
        if user_id == config.ADMIN_ID:
            continue
        
        # Faqat tasdiqlangan hodimlar uchun
        if not db.is_approved(user_id):
            continue
        
        # Bugun lokatsiya yuborgan-yubormaganini tekshirish
        last_location = db.get_last_location(user_id)
        
        if not last_location:
            # Hech qachon lokatsiya yubormagan
            logger.warning(f"⚠️ {name} hech qachon lokatsiya yubormagan")
            continue
        
        last_time = datetime.fromisoformat(last_location['timestamp'])
        
        # Bugun lokatsiya yuborgan-yubormaganini tekshirish
        if last_time.date() < today:
            # Bugun lokatsiya yubormagan
            try:
                message = (
                    f"⚠️ Ogohlantirish!\n\n"
                    f"Siz bugun hali lokatsiya yubormagansiz.\n"
                    f"Ish vaqti: {work_hours['start']}:00 - {work_hours['end']}:00\n"
                    f"Grace period: {grace_period} daqiqa\n\n"
                    f"📍 Iltimos, lokatsiyangizni yuboring."
                )
                
                keyboard = [[KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)]]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    reply_markup=reply_markup
                )
                
                logger.info(f"⚠️ Ogohlantirish yuborildi: {name} ({user_id})")
                
            except Exception as e:
                logger.error(f"❌ Xatolik ({user_id}): {e}")


async def send_lunch_notification(context: ContextTypes.DEFAULT_TYPE):
    """Tushlik vaqti haqida xabar"""
    logger.info("🍽 Tushlik vaqti xabari yuborilmoqda")
    
    employees = db.get_all_employees()
    lunch_hours = config.get_lunch_hours_config()
    
    for employee in employees:
        user_id = employee['user_id']
        name = employee.get('name', 'Hodim')
        
        # Adminni o'tkazib yuborish
        if user_id == config.ADMIN_ID:
            continue
        
        # Faqat tasdiqlangan hodimlar uchun
        if not db.is_approved(user_id):
            continue
        
        try:
            message = (
                f"🍽 Tushlik vaqti, {name}!\n\n"
                f"⏰ {lunch_hours['start']}:00 - {lunch_hours['end']}:00\n\n"
                f"Yaxshi ishtaha! 😊"
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message
            )
            
            logger.info(f"✅ Tushlik xabari yuborildi: {name} ({user_id})")
            
        except Exception as e:
            logger.error(f"❌ Xatolik ({user_id}): {e}")


async def send_end_of_day_notification(context: ContextTypes.DEFAULT_TYPE):
    """Ish kuni tugashi - statistika bilan"""
    from work_time_tracker import send_end_of_day_stats
    await send_end_of_day_stats(context)


async def periodic_location_request(context: ContextTypes.DEFAULT_TYPE):
    """Davriy lokatsiya so'rash (ish vaqtida)"""
    logger.info("🔄 Davriy lokatsiya so'rovi")
    
    # Ish vaqtimi?
    if not config.is_work_hours():
        logger.info("⏰ Ish vaqti emas, o'tkazib yuborildi")
        return
    
    # Tushlik vaqtimi?
    if config.is_lunch_time():
        logger.info("🍽 Tushlik vaqti, o'tkazib yuborildi")
        return
    
    employees = db.get_all_employees()
    interval_config = config.get_interval_config()
    
    for employee in employees:
        user_id = employee['user_id']
        name = employee.get('name', 'Hodim')
        
        # Adminni o'tkazib yuborish
        if user_id == config.ADMIN_ID:
            continue
        
        # Faqat tasdiqlangan hodimlar uchun
        if not db.is_approved(user_id):
            continue
        
        try:
            keyboard = [[KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            message = (
                f"📍 Lokatsiya so'rovi\n\n"
                f"Iltimos, hozirgi lokatsiyangizni yuboring.\n"
                f"(Har {interval_config['minutes']} daqiqada)"
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=reply_markup
            )
            
            logger.info(f"✅ Davriy so'rov yuborildi: {name} ({user_id})")
            
        except Exception as e:
            logger.error(f"❌ Xatolik ({user_id}): {e}")


def setup_scheduler(application):
    """Scheduler ni sozlash"""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    
    scheduler = AsyncIOScheduler()
    
    # Sozlamalarni olish
    work_hours = config.get_work_hours_config()
    lunch_hours = config.get_lunch_hours_config()
    interval_config = config.get_interval_config()
    
    # 1. Ertalab lokatsiya so'rash (ish boshlanishida)
    scheduler.add_job(
        request_morning_location,
        CronTrigger(hour=work_hours['start'], minute=0),
        args=[application],
        id='morning_location',
        name='Ertalab lokatsiya so\'rovi',
        replace_existing=True
    )
    logger.info(f"✅ Ertalab lokatsiya so'rovi: {work_hours['start']}:00")
    
    # 2. Lokatsiya yubormaganlarni tekshirish (ish boshlanishidan 15 daqiqa keyin)
    grace_period = interval_config['grace_period']
    scheduler.add_job(
        check_missing_locations,
        CronTrigger(hour=work_hours['start'], minute=grace_period),
        args=[application],
        id='check_missing',
        name='Lokatsiya yubormaganlarni tekshirish',
        replace_existing=True
    )
    logger.info(f"✅ Tekshirish: {work_hours['start']}:{grace_period:02d}")
    
    # 3. Tushlik vaqti xabari
    scheduler.add_job(
        send_lunch_notification,
        CronTrigger(hour=lunch_hours['start'], minute=0),
        args=[application],
        id='lunch_notification',
        name='Tushlik vaqti xabari',
        replace_existing=True
    )
    logger.info(f"✅ Tushlik xabari: {lunch_hours['start']}:00")
    
    # 4. Ish kuni tugashi xabari
    scheduler.add_job(
        send_end_of_day_notification,
        CronTrigger(hour=work_hours['end'], minute=0),
        args=[application],
        id='end_of_day',
        name='Ish kuni tugashi xabari',
        replace_existing=True
    )
    logger.info(f"✅ Ish kuni tugashi: {work_hours['end']}:00")
    
    # 5. Davriy lokatsiya so'rash (har X daqiqada)
    scheduler.add_job(
        periodic_location_request,
        'interval',
        minutes=interval_config['minutes'],
        args=[application],
        id='periodic_location',
        name='Davriy lokatsiya so\'rovi',
        replace_existing=True
    )
    logger.info(f"✅ Davriy so'rov: har {interval_config['minutes']} daqiqada")
    
    scheduler.start()
    logger.info("🚀 Scheduler ishga tushdi!")
    
    return scheduler
