"""
Admin sozlamalari uchun funksiyalar
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config


async def set_work_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ish vaqtini o'rnatish"""
    if not config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bu komanda faqat admin uchun!")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\n"
            "To'g'ri format: /set_work_hours BOSH_SOAT TUG_SOAT\n"
            "Masalan: /set_work_hours 8 18"
        )
        return
    
    try:
        start_hour = int(context.args[0])
        end_hour = int(context.args[1])
        
        if not (0 <= start_hour <= 23) or not (0 <= end_hour <= 23):
            await update.message.reply_text("❌ Soat 0-23 orasida bo'lishi kerak!")
            return
        
        if start_hour >= end_hour:
            await update.message.reply_text("❌ Boshlanish vaqti tugash vaqtidan kichik bo'lishi kerak!")
            return
        
        # ENV faylini yangilash
        update_work_time_env_file(start_hour, end_hour)
        
        await update.message.reply_text(
            f"✅ Ish vaqti o'rnatildi!\n\n"
            f"🌅 Boshlanish: {start_hour}:00\n"
            f"🌆 Tugash: {end_hour}:00\n\n"
            f"⚠️ O'zgarishlar keyingi restart'da kuchga kiradi"
        )
        
    except ValueError:
        await update.message.reply_text("❌ Soatlar noto'g'ri kiritilgan!")


async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hisobot oralig'ini o'rnatish"""
    if not config.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bu komanda faqat admin uchun!")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\n"
            "To'g'ri format: /set_interval DAQIQA GRACE_PERIOD\n"
            "Masalan: /set_interval 30 5"
        )
        return
    
    try:
        interval = int(context.args[0])
        grace = int(context.args[1])
        
        if not (5 <= interval <= 120):
            await update.message.reply_text("❌ Oraliq 5-120 daqiqa orasida bo'lishi kerak!")
            return
        
        if not (1 <= grace <= 30):
            await update.message.reply_text("❌ Grace period 1-30 daqiqa orasida bo'lishi kerak!")
            return
        
        # ENV faylini yangilash
        update_interval_env_file(interval, grace)
        
        await update.message.reply_text(
            f"✅ Hisobot oralig'i o'rnatildi!\n\n"
            f"⏱ Oraliq: {interval} daqiqa\n"
            f"⏳ Grace period: {grace} daqiqa\n\n"
            f"⚠️ O'zgarishlar keyingi restart'da kuchga kiradi"
        )
        
    except ValueError:
        await update.message.reply_text("❌ Raqamlar noto'g'ri kiritilgan!")


def update_work_time_env_file(start_hour, end_hour):
    """Ish vaqti JSON bazaga yangilash"""
    from settings_manager import update_work_hours
    return update_work_hours(start_hour, end_hour)


def update_interval_env_file(interval, grace):
    """Interval JSON bazaga yangilash"""
    from settings_manager import update_location_interval
    return update_location_interval(interval, grace)


async def show_work_time_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ish vaqtini sozlash menyusi"""
    current_start = config.WORK_START_HOUR
    current_end = config.WORK_END_HOUR
    current_lunch_start = config.LUNCH_START_HOUR
    current_lunch_end = config.LUNCH_END_HOUR
    
    await update.message.reply_text(
        f"⏰ Hozirgi ish vaqti sozlamalari:\n\n"
        f"🌅 Ish boshlanishi: {current_start}:00\n"
        f"🌆 Ish tugashi: {current_end}:00\n"
        f"🍽 Tushlik: {current_lunch_start}:00 - {current_lunch_end}:00\n\n"
        f"O'zgartirish uchun komandalar:\n"
        f"/set_work_hours {current_start} {current_end}\n"
        f"Masalan: /set_work_hours 9 17"
    )


async def show_report_interval_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hisobot oralig'ini sozlash menyusi"""
    current_interval = config.LOCATION_INTERVAL_MINUTES
    current_grace = config.LOCATION_GRACE_PERIOD_MINUTES
    
    keyboard = [
        [InlineKeyboardButton("⏱ 15 daqiqa", callback_data="set_interval_15")],
        [InlineKeyboardButton("⏱ 30 daqiqa", callback_data="set_interval_30")],
        [InlineKeyboardButton("⏱ 45 daqiqa", callback_data="set_interval_45")],
        [InlineKeyboardButton("⏱ 60 daqiqa", callback_data="set_interval_60")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📅 Hozirgi hisobot sozlamalari:\n\n"
        f"⏱ Lokatsiya oralig'i: {current_interval} daqiqa\n"
        f"⏳ Grace period: {current_grace} daqiqa\n\n"
        f"Yangi oraliqni tanlang yoki komanda:\n"
        f"/set_interval {current_interval} {current_grace}",
        reply_markup=reply_markup
    )


async def handle_interval_callback(query, context, data):
    """Interval callback'larini qayta ishlash"""
    intervals = {
        "set_interval_15": 15,
        "set_interval_30": 30,
        "set_interval_45": 45,
        "set_interval_60": 60
    }
    
    if data in intervals:
        interval = intervals[data]
        grace = 5  # Default grace period
        
        # ENV faylini yangilash
        update_interval_env_file(interval, grace)
        
        await query.edit_message_text(
            f"✅ Hisobot oralig'i o'rnatildi!\n\n"
            f"⏱ Yangi oraliq: {interval} daqiqa\n"
            f"⏳ Grace period: {grace} daqiqa\n\n"
            f"⚠️ O'zgarishlar keyingi restart'da kuchga kiradi"
        )