"""
Oylik hisobot funksiyalari
"""
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


async def start_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Oylik hisobot jarayonini boshlash"""
    await update.message.reply_text(
        "📆 Oylik Hisobot\n\n"
        "Boshlanish sanasini kiriting:\n"
        "Format: YYYY-MM-DD\n\n"
        "Misol: 2025-01-01\n\n"
        "Bekor qilish: /cancel"
    )
    return 2  # WAITING_MONTHLY_START_DATE


async def receive_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Boshlanish sanasini qabul qilish"""
    text = update.message.text.strip()
    
    try:
        # Sanani tekshirish
        start_date = datetime.strptime(text, "%Y-%m-%d")
        context.user_data['monthly_start_date'] = text
        
        await update.message.reply_text(
            f"✅ Boshlanish: {text}\n\n"
            f"Tugash sanasini kiriting:\n"
            f"Format: YYYY-MM-DD\n\n"
            f"Misol: 2025-01-31\n\n"
            f"Bekor qilish: /cancel"
        )
        return 3  # WAITING_MONTHLY_END_DATE
    
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\n"
            "To'g'ri format: YYYY-MM-DD\n"
            "Misol: 2025-01-01\n\n"
            "Qaytadan kiriting yoki /cancel"
        )
        return 2  # WAITING_MONTHLY_START_DATE


async def receive_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugash sanasini qabul qilish"""
    text = update.message.text.strip()
    
    try:
        # Sanani tekshirish
        end_date = datetime.strptime(text, "%Y-%m-%d")
        start_date_str = context.user_data.get('monthly_start_date')
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        
        if end_date <= start_date:
            await update.message.reply_text(
                "❌ Tugash sanasi boshlanish sanasidan katta bo'lishi kerak!\n\n"
                "Qaytadan kiriting yoki /cancel"
            )
            return 3  # WAITING_MONTHLY_END_DATE
        
        context.user_data['monthly_end_date'] = text
        
        # Hodimlarni ko'rsatish (faqat tasdiqlangan, adminlar emas)
        from database import Database
        import config
        db = Database()
        all_employees = db.get_all_employees()
        
        # Faqat tasdiqlangan hodimlar va adminlar emas
        employees = [emp for emp in all_employees if db.is_approved(emp['user_id']) and not config.is_admin(emp['user_id'])]
        
        if not employees:
            await update.message.reply_text("❌ Tasdiqlangan hodimlar topilmadi!")
            context.user_data.clear()
            return -1  # ConversationHandler.END
        
        text_msg = f"📅 Davr: {start_date_str} - {text}\n\n"
        text_msg += "Hodimni tanlang:\n\n"
        
        keyboard = []
        for emp in employees:
            name = emp['name'] or emp['username'] or f"ID: {emp['user_id']}"
            text_msg += f"👤 {name}\n"
            keyboard.append([
                InlineKeyboardButton(name, callback_data=f"monthly_{emp['user_id']}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text_msg, reply_markup=reply_markup)
        
        return 4  # WAITING_MONTHLY_USER_SELECT
    
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\n"
            "To'g'ri format: YYYY-MM-DD\n"
            "Misol: 2025-01-31\n\n"
            "Qaytadan kiriting yoki /cancel"
        )
        return 3  # WAITING_MONTHLY_END_DATE


async def handle_monthly_user_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hodim tanlanganida hisobotni ko'rsatish"""
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split("_")[1])
    start_date = context.user_data.get('monthly_start_date')
    end_date = context.user_data.get('monthly_end_date')
    
    # Hisobotni olish
    from daily_work_calculator import get_monthly_report
    from database import Database
    from work_hours_manager import get_employee_work_hours
    
    db = Database()
    report_data = get_monthly_report(user_id, start_date, end_date)
    
    # Hodim ma'lumotlari
    employees = db.get_all_employees()
    user_info = next((emp for emp in employees if emp['user_id'] == user_id), None)
    user_name = user_info['name'] if user_info else f"ID: {user_id}"
    
    # Ish vaqti
    work_hours = get_employee_work_hours(user_id)
    work_hours_str = f"{work_hours['work_start']}:00 - {work_hours['work_end']}:00" if work_hours else "Belgilanmagan"
    
    # Hisobotni formatlash
    report = f"📊 Oylik Hisobot\n\n"
    report += f"👤 Hodim: {user_name}\n"
    report += f"📅 Davr: {start_date} - {end_date}\n"
    report += f"⏰ Ish vaqti: {work_hours_str}\n\n"
    
    report += f"📈 Jami ish kunlari: {report_data['total_days']} kun\n\n"
    
    report += f"✅ Jami ish soati: {report_data['total_work_hours']} soat\n"
    report += f"🟢 Ish joyida: {report_data['total_present_hours']} soat\n"
    report += f"❌ Ish joyida emas: {report_data['total_absent_hours']} soat\n"
    report += f"🎯 Samaradorlik: {report_data['efficiency_percent']}%\n\n"
    
    if report_data['daily_details']:
        report += "📋 Kunlik tafsilot:\n\n"
        for day in report_data['daily_details'][:10]:  # Faqat 10 kunni ko'rsatish
            date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
            report += f"{date_obj.strftime('%d.%m.%Y')}: {day['total_work_hours']} soat"
            if day['absent_hours'] > 0:
                report += f" (⚠️ {day['absent_hours']} soat yo'q)"
            report += "\n"
        
        if len(report_data['daily_details']) > 10:
            report += f"\n... va yana {len(report_data['daily_details']) - 10} kun"
    
    await query.edit_message_text(report)
    
    # Context ni tozalash
    context.user_data.clear()
    
    return -1  # ConversationHandler.END


async def cancel_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Oylik hisobotni bekor qilish"""
    keyboard = [
        [KeyboardButton("📊 Bugungi Hisobot"), KeyboardButton("👥 Kutish ro'yxati")],
        [KeyboardButton("🗑 Hodimni o'chirish"), KeyboardButton("🏢 Ofisni Belgilash")],
        [KeyboardButton("⏰ Ish Vaqtini Sozlash"), KeyboardButton("📅 Hisobot Oralig'i")],
        [KeyboardButton("📆 Oylik Hisobot"), KeyboardButton("📖 Qo'llanma")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "❌ Bekor qilindi",
        reply_markup=reply_markup
    )
    context.user_data.clear()
    return -1  # ConversationHandler.END
