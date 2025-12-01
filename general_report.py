"""
Umumiy hisobot funksiyalari (Hodim -> Boshlanish sanasi -> Tugash sanasi)
"""
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
import config
from database import Database

logger = logging.getLogger(__name__)
db = Database()

# States
WAITING_REPORT_USER_SELECT = 30
WAITING_REPORT_START_DATE = 31
WAITING_REPORT_END_DATE = 32

async def start_general_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Umumiy hisobot jarayonini boshlash - Hodimni tanlash"""
    all_employees = db.get_all_employees()
    
    # Adminlarni chiqarib tashlash
    employees = [emp for emp in all_employees if not config.is_admin(emp['user_id'])]
    
    if not employees:
        await update.message.reply_text("❌ Hodimlar topilmadi!")
        return ConversationHandler.END
    
    text_msg = "📊 Hisobot\n\n"
    text_msg += "Qaysi hodim bo'yicha hisobot kerak? Tanlang:\n\n"
    
    keyboard = []
    for emp in employees:
        name = emp['name'] or emp['username'] or f"ID: {emp['user_id']}"
        keyboard.append([
            InlineKeyboardButton(f"👤 {name}", callback_data=f"report_user_{emp['user_id']}")
        ])
    
    text_msg += "\nBekor qilish: /cancel"
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text_msg, reply_markup=reply_markup)
    
    return WAITING_REPORT_USER_SELECT


async def handle_report_user_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hodim tanlanganda"""
    query = update.callback_query
    await query.answer()
    
    # data: report_user_{user_id}
    user_id = int(query.data.split("_")[2])
    context.user_data['report_user_id'] = user_id
    
    # Hodim ismini olish
    employees = db.get_all_employees()
    user_info = next((emp for emp in employees if emp['user_id'] == user_id), None)
    user_name = user_info['name'] if user_info else f"ID: {user_id}"
    context.user_data['report_user_name'] = user_name
    
    await query.edit_message_text(
        f"👤 Tanlangan hodim: {user_name}\n\n"
        f"Endi boshlanish sanasini kiriting:\n"
        f"Format: YYYY-MM-DD\n\n"
        f"Misol: 2025-11-01\n\n"
        f"Bekor qilish: /cancel"
    )
    
    return WAITING_REPORT_START_DATE


async def receive_report_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Boshlanish sanasini qabul qilish"""
    text = update.message.text.strip()
    
    try:
        # Sanani tekshirish
        start_date = datetime.strptime(text, "%Y-%m-%d")
        context.user_data['report_start_date'] = text
        
        user_name = context.user_data.get('report_user_name', 'Hodim')
        
        await update.message.reply_text(
            f"👤 Hodim: {user_name}\n"
            f"✅ Boshlanish: {text}\n\n"
            f"Endi tugash sanasini kiriting:\n"
            f"Format: YYYY-MM-DD\n\n"
            f"Misol: 2025-11-30\n\n"
            f"Bekor qilish: /cancel"
        )
        return WAITING_REPORT_END_DATE
    
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\n"
            "To'g'ri format: YYYY-MM-DD\n"
            "Misol: 2025-11-01\n\n"
            "Qaytadan kiriting yoki /cancel"
        )
        return WAITING_REPORT_START_DATE


async def receive_report_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugash sanasini qabul qilish va hisobotni chiqarish"""
    text = update.message.text.strip()
    
    try:
        # Sanani tekshirish
        end_date = datetime.strptime(text, "%Y-%m-%d")
        start_date_str = context.user_data.get('report_start_date')
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        
        if end_date < start_date:
            await update.message.reply_text(
                "❌ Tugash sanasi boshlanish sanasidan kichik bo'lishi mumkin emas!\n\n"
                "Qaytadan kiriting yoki /cancel"
            )
            return WAITING_REPORT_END_DATE
        
        user_id = context.user_data.get('report_user_id')
        user_name = context.user_data.get('report_user_name')
        
        # Hisobotni olish
        from daily_work_calculator import get_monthly_report
        from work_hours_manager import get_employee_work_hours
        
        # get_monthly_report aslida har qanday range uchun ishlaydi
        report_data = get_monthly_report(user_id, start_date_str, text)
        
        # Ish vaqti
        work_hours = get_employee_work_hours(user_id)
        work_hours_str = f"{work_hours['work_start']}:00 - {work_hours['work_end']}:00" if work_hours else "Belgilanmagan"
        
        # Hisobotni formatlash
        report = f"📊 Hisobot\n\n"
        report += f"👤 Hodim: {user_name}\n"
        report += f"📅 Davr: {start_date_str} - {text}\n"
        report += f"⏰ Ish vaqti: {work_hours_str}\n\n"
        
        report += f"📈 Jami ish kunlari: {report_data['total_days']} kun\n\n"
        
        report += f"✅ Jami ish soati: {report_data['total_work_hours']} soat\n"
        report += f"🟢 Ish joyida: {report_data['total_present_hours']} soat\n"
        report += f"❌ Ish joyida emas: {report_data['total_absent_hours']} soat\n"
        report += f"🎯 Samaradorlik: {report_data['efficiency_percent']}%\n\n"
        
        if report_data['daily_details']:
            report += "📋 Kunlik tafsilot:\n\n"
            # Agar juda ko'p bo'lsa, qisqartirish yoki fayl qilib tashlash kerak bo'lishi mumkin
            # Hozircha 15 kunni ko'rsatamiz
            for day in report_data['daily_details'][:15]:
                date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
                report += f"{date_obj.strftime('%d.%m.%Y')}: {day['total_work_hours']} soat"
                if day['absent_hours'] > 0:
                    report += f" (⚠️ {day['absent_hours']} soat yo'q)"
                report += "\n"
            
            if len(report_data['daily_details']) > 15:
                report += f"\n... va yana {len(report_data['daily_details']) - 15} kun"
        else:
            report += "Bu davrda ma'lumot yo'q."
        
        await update.message.reply_text(report)
        
        # Admin klaviaturasini qayta chiqarish (agar yo'qolgan bo'lsa)
        keyboard = [
            [KeyboardButton("📊 Hisobot"), KeyboardButton("👥 Kutish ro'yxati")],
            [KeyboardButton("🗑 Hodimni o'chirish"), KeyboardButton("🏢 Ofisni Belgilash")],
            [KeyboardButton("⏰ Ish Vaqtini Sozlash"), KeyboardButton("📅 Hisobot Oralig'i")],
            [KeyboardButton("📖 Qo'llanma")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("✅ Hisobot tayyor.", reply_markup=reply_markup)
        
        # Context ni tozalash
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format!\n\n"
            "To'g'ri format: YYYY-MM-DD\n"
            "Misol: 2025-11-30\n\n"
            "Qaytadan kiriting yoki /cancel"
        )
        return WAITING_REPORT_END_DATE


async def cancel_general_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hisobotni bekor qilish"""
    keyboard = [
        [KeyboardButton("📊 Hisobot"), KeyboardButton("👥 Kutish ro'yxati")],
        [KeyboardButton("🗑 Hodimni o'chirish"), KeyboardButton("🏢 Ofisni Belgilash")],
        [KeyboardButton("⏰ Ish Vaqtini Sozlash"), KeyboardButton("📅 Hisobot Oralig'i")],
        [KeyboardButton("📖 Qo'llanma")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "❌ Bekor qilindi",
        reply_markup=reply_markup
    )
    context.user_data.clear()
    return ConversationHandler.END
