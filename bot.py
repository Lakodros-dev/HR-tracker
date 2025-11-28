import logging
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from database import Database
from utils import is_location_valid, is_work_hours, is_lunch_time, format_time, format_date
from admin_settings import (
    set_work_hours, set_interval, show_work_time_setup, 
    show_report_interval_setup, handle_interval_callback
)
from mini_app_handler import handle_mini_app_data
from employee_management import (
    handle_start, show_pending_users, show_pending_users_text, 
    start_approval_with_hours, receive_approval_start_time, receive_approval_end_time, cancel_approval,
    reject_user,
    show_remove_employee_menu, show_remove_employee_menu_text, remove_employee,
    show_employees_for_work_hours, start_edit_work_hours, receive_edit_start_time, receive_edit_end_time, cancel_edit_hours
)
from work_time_tracker import send_end_of_day_stats

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database
db = Database()

# Scheduler
scheduler = AsyncIOScheduler()

# Conversation states
WAITING_WORK_HOURS = 1
WAITING_MONTHLY_START_DATE = 2
WAITING_MONTHLY_END_DATE = 3
WAITING_MONTHLY_USER_SELECT = 4
WAITING_APPROVE_START_TIME = 10
WAITING_APPROVE_END_TIME = 11
WAITING_EDIT_START_TIME = 20
WAITING_EDIT_END_TIME = 21


async def block_forwarded_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwarded (uzatilgan) xabarlarni bloklash"""
    if update.message and update.message.forward_date:
        await update.message.reply_text(
            "❌ Uzatilgan xabarlar taqiqlangan!\n\n"
            "Iltimos, xabarni to'g'ridan-to'g'ri yozing."
        )
        return
    # Agar forwarded emas bo'lsa, keyingi handlerga o'tkazish
    return


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lokatsiya qabul qilish"""
    user_id = update.effective_user.id
    
    # Hodim ekanligini tekshirish
    if not db.is_employee(user_id):
        await update.message.reply_text("❌ Siz ro'yxatdan o'tmagansiz!\n\n/start komandasi bilan ro'yxatdan o'ting.")
        return
    
    # Tasdiqlangan-tasdiqlanmaganini tekshirish
    if not db.is_approved(user_id):
        await update.message.reply_text("⏳ Sizning arizangiz hali tasdiqlanmagan.\n\nAdmin tasdiqlashini kuting.")
        return
    
    location = update.message.location
    lat = location.latitude
    lon = location.longitude
    now = datetime.now()
    
    # Ish vaqtida emasligini tekshirish
    if not config.is_work_hours():
        work_hours = config.get_work_hours_config()
        await update.message.reply_text(
            f"⏰ Hozirda sizning ish vaqtingiz tugagan.\n\n"
            f"Ish vaqti: {work_hours['start']}:00 - {work_hours['end']}:00\n"
            f"Hozirgi vaqt: {now.strftime('%H:%M')}"
        )
        return
    
    # Lokatsiyani tekshirish
    is_valid, distance = is_location_valid(lat, lon)
    
    # Bazaga yozish
    db.log_location(user_id, lat, lon, distance, is_valid)
    
    # Kunlik ish soatlarini yangilash
    from daily_work_calculator import update_daily_work_hours_for_user
    try:
        update_daily_work_hours_for_user(user_id)
    except Exception as e:
        logger.error(f"Kunlik ish soatlarini yangilashda xato: {e}")
    
    # Bugungi birinchi lokatsiyami?
    today_locations = db.get_today_report(user_id)
    if len(today_locations) == 1:  # Birinchi lokatsiya
        from work_time_tracker import check_first_location_of_day
        await check_first_location_of_day(user_id, now, context)
    
    if is_valid:
        db.update_attendance_status(user_id, True, now.isoformat())
        await update.message.reply_text(
            f"✅ Lokatsiya qabul qilindi!\n"
            f"📏 Masofa: {distance:.1f} metr\n"
            f"⏰ Vaqt: {now.strftime('%H:%M:%S')}\n"
            f"📊 Bugungi lokatsiyalar: {len(today_locations)}"
        )
    else:
        db.update_attendance_status(user_id, False)
        await update.message.reply_text(
            f"❌ Siz ofis hududida emassiz!\n"
            f"📏 Masofa: {distance:.1f} metr\n"
            f"⚠️ Iltimos, ofis hududiga kiring."
        )


async def my_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hodimning kunlik hisoboti"""
    user_id = update.effective_user.id
    
    if not db.is_employee(user_id):
        await update.message.reply_text("❌ Siz ro'yxatdan o'tmagansiz!\n\n/start komandasi bilan ro'yxatdan o'ting.")
        return
    
    if not db.is_approved(user_id):
        await update.message.reply_text("⏳ Sizning arizangiz hali tasdiqlanmagan.\n\nAdmin tasdiqlashini kuting.")
        return
    
    status = db.get_attendance_status(user_id)
    logs = db.get_today_report(user_id)
    
    no_data = "Yo'q"
    report = f"📊 Bugungi hisobotingiz\n\n"
    report += f"Holat: {'✅ Ish joyida' if status and status['is_present'] else '❌ Ish joyida emas'}\n"
    report += f"Kelgan vaqt: {format_time(status['check_in_time']) if status else no_data}\n"
    report += f"Ketgan vaqt: {format_time(status['check_out_time']) if status else no_data}\n"
    report += f"Ogohlantirishlar: {status['warnings_count'] if status else 0}\n\n"
    
    if logs:
        valid_count = sum(1 for log in logs if log['is_valid'])
        report += f"📍 Lokatsiya yozuvlari: {len(logs)} ta\n"
        report += f"✅ To'g'ri: {valid_count} ta\n"
        report += f"❌ Noto'g'ri: {len(logs) - valid_count} ta\n\n"
        
        # Barcha lokatsiyalar
        report += "🗺 Barcha lokatsiyalar:\n\n"
        for i, log in enumerate(logs, 1):
            status_icon = "✅" if log['is_valid'] else "❌"
            report += f"{i}. {status_icon} {format_time(log['timestamp'])}\n"
            report += f"   📍 Lat: {log['latitude']:.6f}\n"
            report += f"   📍 Lng: {log['longitude']:.6f}\n"
            report += f"   📏 Masofa: {log['distance']:.1f}m\n\n"
    else:
        report += "📍 Bugun lokatsiya yuborilmagan"
    
    await update.message.reply_text(report)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi - yangi tizim bilan"""
    await handle_start(update, context)


async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin tugmalarini qayta ishlash"""
    if not config.is_admin(update.effective_user.id):
        return
    
    text = update.message.text
    
    if text == "📊 Bugungi Hisobot":
        await show_daily_report_menu(update, context)
    elif text == "👥 Kutish ro'yxati":
        await show_pending_users_text(update, context)
    elif text == "🗑 Hodimni o'chirish":
        await show_remove_employee_menu_text(update, context)
    elif text == "🏢 Ofisni Belgilash":
        await show_office_setup(update, context)
    elif text == "⏰ Ish Vaqtini Sozlash":
        await show_employees_for_work_hours(update, context)
    elif text == "📅 Hisobot Oralig'i":
        await show_report_interval_setup(update, context)


# ==================== ISH VAQTINI SOZLASH (CONVERSATION) ====================

async def start_work_hours_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ish vaqtini sozlashni boshlash"""
    from settings_manager import get_work_hours
    current = get_work_hours()
    
    await update.message.reply_text(
        f"⏰ Ish vaqtini sozlash\n\n"
        f"Hozirgi vaqt: {current['start']}:00 - {current['end']}:00\n\n"
        f"Yangi ish vaqtini yuboring:\n"
        f"Format: <boshlanish> <tugash>\n\n"
        f"Misol: 9 18\n"
        f"(9:00 dan 18:00 gacha)\n\n"
        f"Bekor qilish uchun /cancel yuboring",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_WORK_HOURS


async def receive_work_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ish vaqtini qabul qilish"""
    text = update.message.text.strip()
    
    try:
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text(
                "❌ Noto'g'ri format!\n\n"
                "To'g'ri format: <boshlanish> <tugash>\n"
                "Misol: 9 18"
            )
            return WAITING_WORK_HOURS
        
        start_hour = int(parts[0])
        end_hour = int(parts[1])
        
        if not (0 <= start_hour < 24 and 0 <= end_hour < 24):
            await update.message.reply_text(
                "❌ Vaqt 0-23 oralig'ida bo'lishi kerak!\n\n"
                "Qaytadan kiriting yoki /cancel"
            )
            return WAITING_WORK_HOURS
        
        if start_hour >= end_hour:
            await update.message.reply_text(
                "❌ Boshlanish vaqti tugash vaqtidan kichik bo'lishi kerak!\n\n"
                "Qaytadan kiriting yoki /cancel"
            )
            return WAITING_WORK_HOURS
        
        # Saqlash
        from settings_manager import update_work_hours
        if update_work_hours(start_hour, end_hour):
            # Admin klaviaturasini qaytarish
            keyboard = [
                [KeyboardButton("📊 Bugungi Hisobot"), KeyboardButton("👥 Kutish ro'yxati")],
                [KeyboardButton("🗑 Hodimni o'chirish"), KeyboardButton("🏢 Ofisni Belgilash")],
                [KeyboardButton("⏰ Ish Vaqtini Sozlash"), KeyboardButton("📅 Hisobot Oralig'i")],
                [KeyboardButton("📖 Qo'llanma")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"✅ Ish vaqti o'rnatildi!\n\n"
                f"🕐 Boshlanish: {start_hour}:00\n"
                f"🕐 Tugash: {end_hour}:00\n\n"
                f"⚠️ Botni qayta ishga tushiring: /start",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text("❌ Sozlamalarni saqlashda xato!")
            return ConversationHandler.END
            
    except ValueError:
        await update.message.reply_text(
            "❌ Faqat raqam kiriting!\n\n"
            "Misol: 9 18\n\n"
            "Bekor qilish: /cancel"
        )
        return WAITING_WORK_HOURS


async def cancel_work_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ish vaqtini sozlashni bekor qilish"""
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
    return ConversationHandler.END


async def handle_office_location_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ofis lokatsiyasini qo'lda belgilash - /set_office lat lng radius"""
    if not config.is_admin(update.effective_user.id):
        return
    
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ Noto'g'ri format!\n\n"
                "To'g'ri format:\n"
                "/set_office <latitude> <longitude> [radius]\n\n"
                "Misol:\n"
                "/set_office 41.2995 69.2401 100"
            )
            return
        
        latitude = float(args[0])
        longitude = float(args[1])
        radius = int(args[2]) if len(args) > 2 else 100
        
        from settings_manager import update_office_location
        if update_office_location(latitude, longitude, radius):
            await update.message.reply_text(
                "✅ Ofis muvaffaqiyatli o'rnatildi!\n\n"
                "🎯 Hodimlar endi belgilangan hudud ichida lokatsiya yuborishlari kerak."
            )
            
            # Lokatsiyani xaritada ko'rsatish
            await update.message.reply_location(latitude=latitude, longitude=longitude)
        else:
            await update.message.reply_text("❌ Sozlamalarni saqlashda xato!")
    except ValueError:
        await update.message.reply_text("❌ Koordinatalar raqam bo'lishi kerak!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xato: {str(e)}")


async def handle_office_area_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ofis hududini qo'lda belgilash - /set_area lat1 lng1 lat2 lng2"""
    logger.info(f"/set_area komandasi qabul qilindi. User ID: {update.effective_user.id}, Admin IDs: {config.ADMIN_IDS}")
    
    if not config.is_admin(update.effective_user.id):
        logger.warning(f"Admin emas! User ID: {update.effective_user.id}")
        return
    
    try:
        args = context.args
        if len(args) < 4:
            await update.message.reply_text(
                "❌ Noto'g'ri format!\n\n"
                "To'g'ri format:\n"
                "/set_area <lat1> <lng1> <lat2> <lng2>\n\n"
                "Misol:\n"
                "/set_area 41.2995 69.2401 41.3005 69.2411"
            )
            return
        
        point1 = {'lat': float(args[0]), 'lng': float(args[1])}
        point2 = {'lat': float(args[2]), 'lng': float(args[3])}
        
        # Debug log
        logger.info(f"Ofis hududi belgilanmoqda:")
        logger.info(f"  Point1: lat={point1['lat']}, lng={point1['lng']}")
        logger.info(f"  Point2: lat={point2['lat']}, lng={point2['lng']}")
        
        from settings_manager import update_office_area
        if update_office_area(point1, point2):
            # Maydonni hisoblash
            import math
            R = 6371000
            lat1 = point1['lat'] * math.pi / 180
            lat2 = point2['lat'] * math.pi / 180
            lng1 = point1['lng'] * math.pi / 180
            lng2 = point2['lng'] * math.pi / 180
            
            dlat = abs(lat2 - lat1)
            dlng = abs(lng2 - lng1)
            
            lat_distance = dlat * R
            lng_distance = dlng * R * math.cos((lat1 + lat2) / 2)
            area = lat_distance * lng_distance
            
            await update.message.reply_text(
                "✅ Ofis muvaffaqiyatli o'rnatildi!\n\n"
                "🎯 Hodimlar endi belgilangan hudud ichida lokatsiya yuborishlari kerak."
            )
            
            # Markazni xaritada ko'rsatish
            center_lat = (point1['lat'] + point2['lat']) / 2
            center_lng = (point1['lng'] + point2['lng']) / 2
            await update.message.reply_location(latitude=center_lat, longitude=center_lng)
        else:
            await update.message.reply_text("❌ Sozlamalarni saqlashda xato!")
    except ValueError:
        await update.message.reply_text("❌ Koordinatalar raqam bo'lishi kerak!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xato: {str(e)}")


def main():
    """Botni ishga tushirish"""
    if not config.BOT_TOKEN:
        print("❌ BOT_TOKEN topilmadi! .env faylini to'ldiring.")
        return
    
    # Application yaratish
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Test komandasi
    async def test_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Web App test"""
        if not config.is_admin(update.effective_user.id):
            return
        
        keyboard = [[InlineKeyboardButton("🗺 Test Mini App", web_app=WebAppInfo(url=config.MINI_APP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🧪 Mini App Test:\n\n"
            f"URL: {config.MINI_APP_URL}\n\n"
            "Tugmani bosing va ma'lumot yuboring.\n"
            "Console'da loglarni ko'ring.",
            reply_markup=reply_markup
        )
    
    # Sozlamalarni yangilash komandasi
    async def refresh_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sozlamalarni yangilash (admin uchun)"""
        if not config.is_admin(update.effective_user.id):
            return
        
        from settings_manager import clear_cache, load_settings
        clear_cache()
        settings = load_settings()
        
        await update.message.reply_text(
            f"🔄 Sozlamalar yangilandi!\n\n"
            f"📍 Ofis rejimi: {'Hudud' if settings.get('use_area_mode') else 'Doira'}\n"
            f"⏰ Ish vaqti: {settings['work_hours']['start']}:00 - {settings['work_hours']['end']}:00\n"
            f"🍽 Tushlik: {settings['lunch_hours']['start']}:00 - {settings['lunch_hours']['end']}:00"
        )
    
    # Handlerlar
    # Forwarded xabarlarni bloklash (eng birinchi tekshiruv)
    application.add_handler(MessageHandler(filters.FORWARDED, block_forwarded_messages))
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test_webapp", test_webapp))
    application.add_handler(CommandHandler("refresh", refresh_settings))
    application.add_handler(CommandHandler("set_work_hours", set_work_hours))
    application.add_handler(CommandHandler("set_interval", set_interval))
    application.add_handler(CommandHandler("set_office", handle_office_location_command))
    application.add_handler(CommandHandler("set_area", handle_office_area_command))
    
    # Video handler (file_id olish uchun)
    async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Video yuborilganda file_id ni qaytarish"""
        if config.is_admin(update.effective_user.id):
            video = update.message.video
            file_id = video.file_id
            await update.message.reply_text(
                f"📹 Video qabul qilindi!\n\n"
                f"File ID:\n`{file_id}`\n\n"
                f"Bu ID ni qo'llanma uchun ishlatishingiz mumkin.",
                parse_mode='Markdown'
            )
    
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    # Lokatsiya va hisobot
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(CommandHandler("report", my_report))
    application.add_handler(MessageHandler(filters.Regex("📊 Mening hisobotim"), my_report))
    
    # Qo'llanma (admin va hodimlar uchun)
    application.add_handler(MessageHandler(filters.Regex("📖 Qo'llanma"), show_guide))
    
    # Ish vaqtini sozlash (Conversation) - Individual
    edit_work_hours_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_work_hours, pattern="^edit_hours_")],
        states={
            WAITING_EDIT_START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_start_time)],
            WAITING_EDIT_END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_end_time)]
        },
        fallbacks=[CommandHandler("cancel", cancel_edit_hours)]
    )
    application.add_handler(edit_work_hours_conv)
    
    # Oylik hisobot (Conversation)
    from monthly_report import (
        start_monthly_report, receive_start_date, receive_end_date,
        handle_monthly_user_select, cancel_monthly_report
    )
    
    monthly_report_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📆 Oylik Hisobot$"), start_monthly_report)],
        states={
            WAITING_MONTHLY_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_start_date)],
            WAITING_MONTHLY_END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_end_date)],
            WAITING_MONTHLY_USER_SELECT: [CallbackQueryHandler(handle_monthly_user_select, pattern="^monthly_")]
        },
        fallbacks=[CommandHandler("cancel", cancel_monthly_report)]
    )
    application.add_handler(monthly_report_conv)
    
    # Tasdiqlash (Conversation) - ish vaqti bilan
    approval_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_approval_with_hours, pattern="^approve_")],
        states={
            WAITING_APPROVE_START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_approval_start_time)],
            WAITING_APPROVE_END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_approval_end_time)]
        },
        fallbacks=[CommandHandler("cancel", cancel_approval)]
    )
    application.add_handler(approval_conv)
    
    # Callback query handler (AFTER ConversationHandlers so they can intercept first)
    async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        # Hodimlarni boshqarish
        if query.data == "pending_users":
            await show_pending_users(update, context)
        elif query.data.startswith("reject_"):
            user_id = int(query.data.split("_")[1])
            await reject_user(update, context, user_id)
        elif query.data == "remove_employee":
            await show_remove_employee_menu(update, context)
        elif query.data.startswith("remove_"):
            user_id = int(query.data.split("_")[1])
            await remove_employee(update, context, user_id)
        elif query.data.startswith("set_interval_"):
            await handle_interval_callback(query, context, query.data)
        elif query.data == "manual_office_menu":
            await query.edit_message_text(
                "📝 Qo'lda ofis belgilash:\n\n"
                "Komandalar:\n"
                "/set_office lat lng radius - Nuqta\n"
                "/set_area lat1 lng1 lat2 lng2 - Hudud\n\n"
                "Masalan:\n"
                "/set_office 41.2995 69.2401 100"
            )
        elif query.data == "admin_status":
            # Hodimlar holati
            employees = db.get_all_active_employees()
            employees = [emp for emp in employees if not config.is_admin(emp[0])]
            
            if not employees:
                await query.edit_message_text("📊 Hozircha hodimlar yo'q")
                return
            
            present = []
            absent = []
            
            for user_id, username, full_name in employees:
                status = db.get_attendance_status(user_id)
                name = full_name or username or f"ID: {user_id}"
                if status and status['is_present']:
                    present.append(f"✅ {name}")
                else:
                    absent.append(f"❌ {name}")
            
            report = f"👥 Hodimlar Holati ({datetime.now().strftime('%H:%M')})\n\n"
            
            if present:
                report += "🟢 Ish joyida:\n" + "\n".join(present) + "\n\n"
            
            if absent:
                report += "🔴 Ish joyida emas:\n" + "\n".join(absent)
            
            await query.edit_message_text(report)
        
        elif query.data == "general_report":
            # Umumiy hisobot
            employees = db.get_all_active_employees()
            employees = [emp for emp in employees if not config.is_admin(emp[0])]
            
            if not employees:
                await query.edit_message_text("📊 Hozircha hodimlar yo'q")
                return
            
            report = "📈 Umumiy bugungi hisobot\n\n"
            
            present_count = 0
            total_locations = 0
            
            for user_id, username, full_name in employees:
                name = full_name or username or f"ID: {user_id}"
                status = db.get_attendance_status(user_id)
                logs = db.get_today_report(user_id)
                
                if status and status['is_present']:
                    present_count += 1
                
                total_locations += len(logs)
                
                report += f"👤 {name}\n"
                report += f"   Holat: {'✅' if status and status['is_present'] else '❌'}\n"
                report += f"   Lokatsiyalar: {len(logs)} ta\n"
                report += f"   Ogohlantirishlar: {status['warnings_count'] if status else 0}\n\n"
            
            summary = f"📊 Xulosa:\n"
            summary += f"👥 Jami hodimlar: {len(employees)}\n"
            summary += f"✅ Ish joyida: {present_count}\n"
            summary += f"❌ Ish joyida emas: {len(employees) - present_count}\n"
            summary += f"📍 Jami lokatsiyalar: {total_locations}\n\n"
            
            await query.edit_message_text(summary + report)
        
        elif query.data.startswith("user_report_"):
            # Individual hodim hisoboti
            user_id = int(query.data.split("_")[2])
            
            employees = db.get_all_active_employees()
            user_info = None
            
            for uid, username, full_name in employees:
                if uid == user_id:
                    user_info = (uid, username, full_name)
                    break
            
            if not user_info:
                await query.edit_message_text("❌ Hodim topilmadi!")
                return
            
            _, username, full_name = user_info
            name = full_name or username or f"ID: {user_id}"
            
            status = db.get_attendance_status(user_id)
            logs = db.get_today_report(user_id)
            
            report = f"👤 {name} - Batafsil hisobot\n\n"
            
            # Asosiy ma'lumotlar
            no_data = "Yo'q"
            report += f"📊 Bugungi holat:\n"
            report += f"   Hozir: {'✅ Ish joyida' if status and status['is_present'] else '❌ Ish joyida emas'}\n"
            report += f"   Kelgan: {format_time(status['check_in_time']) if status else no_data}\n"
            report += f"   Ketgan: {format_time(status['check_out_time']) if status else no_data}\n"
            report += f"   Ogohlantirishlar: {status['warnings_count'] if status else 0}\n\n"
            
            # Lokatsiya ma'lumotlari
            if logs:
                valid_count = sum(1 for log in logs if log['is_valid'])
                report += f"📍 Lokatsiya yozuvlari ({len(logs)} ta):\n"
                report += f"   ✅ To'g'ri: {valid_count} ta\n"
                report += f"   ❌ Noto'g'ri: {len(logs) - valid_count} ta\n\n"
                
                # Barcha lokatsiyalar
                report += "🗺 Barcha lokatsiyalar:\n\n"
                for i, log in enumerate(logs, 1):
                    status_icon = "✅" if log['is_valid'] else "❌"
                    report += f"{i}. {status_icon} {format_time(log['timestamp'])}\n"
                    report += f"   📍 Lat: {log['latitude']:.6f}\n"
                    report += f"   📍 Lng: {log['longitude']:.6f}\n"
                    report += f"   📏 Masofa: {log['distance']:.1f}m\n\n"
                
                # Oxirgi lokatsiyani xarita sifatida yuborish
                try:
                    await context.bot.send_location(
                        chat_id=query.message.chat_id,
                        latitude=last_log['latitude'],
                        longitude=last_log['longitude']
                    )
                except Exception as e:
                    report += f"\n❌ Xarita yuborishda xato"
            else:
                report += "📍 Bugun lokatsiya yuborilmagan\n"
            
            await query.edit_message_text(report)
        elif query.data == "view_on_map":
            # Ofis hududini xaritada ko'rsatish
            from settings_manager import get_office_area, is_area_mode
            
            if is_area_mode():
                area = get_office_area()
                point1 = area['point1']
                point2 = area['point2']
                
                # Markazni hisoblash
                center_lat = (point1['lat'] + point2['lat']) / 2
                center_lng = (point1['lng'] + point2['lng']) / 2
                
                # Lokatsiyani yuborish
                await context.bot.send_location(
                    chat_id=query.message.chat_id,
                    latitude=center_lat,
                    longitude=center_lng
                )
                
                await query.edit_message_text(
                    f"🗺 Ofis hududi markazi:\n\n"
                    f"📍 Lat: {center_lat:.6f}\n"
                    f"📍 Lng: {center_lng:.6f}"
                )
            else:
                from settings_manager import get_office_location
                loc = get_office_location()
                
                await context.bot.send_location(
                    chat_id=query.message.chat_id,
                    latitude=loc['latitude'],
                    longitude=loc['longitude']
                )
                
                await query.edit_message_text(
                    f"🗺 Ofis joyi:\n\n"
                    f"📍 Lat: {loc['latitude']:.6f}\n"
                    f"📍 Lng: {loc['longitude']:.6f}\n"
                    f"🔵 Radius: {loc['radius']} metr"
                )
    
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    
    
    # Admin tugmalar (boshqa tugmalar)
    application.add_handler(MessageHandler(
        filters.Regex("📊 Bugungi Hisobot|👥 Kutish ro'yxati|🗑 Hodimni o'chirish|🏢 Ofisni Belgilash|⏰ Ish Vaqtini Sozlash|📅 Hisobot Oralig'i"), 
        handle_admin_buttons
    ))
    
    # Web App handler
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_mini_app_data))
    
    
    # Scheduler ni sozlash
    from scheduler_tasks import setup_scheduler
    scheduler = setup_scheduler(application)
    
    # Botni ishga tushirish
    print("🤖 Bot ishga tushdi!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def show_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Qo'llanma videosini yuborish (admin va hodimlar uchun)"""
    user_id = update.effective_user.id
    
    # Admin uchun qo'llanma
    if config.is_admin(user_id):
        ADMIN_GUIDE_VIDEO_FILE_ID = "BAACAgIAAxkBAAOqaRvw7txl2sjRZMCwWrnYrkmdPHYAAliCAAI9leFILEYNB-_S3142BA"
        try:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=ADMIN_GUIDE_VIDEO_FILE_ID,
                caption="📖 Admin uchun qo'llanma\n\n"
                        "Ushbu videoda botning barcha admin funksiyalari va sozlamalari tushuntirilgan."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Qo'llanma videosini yuborishda xato:\n{str(e)}\n\n"
                "Iltimos, keyinroq qayta urinib ko'ring."
            )
    # Hodim uchun qo'llanma
    else:
        EMPLOYEE_GUIDE_VIDEO_FILE_ID = "BAACAgIAAxkBAAPGaRv7jAABYC9OC8RpARCItuSM-B6QAAKmggACPZXhSO9lh0JnEDVaNgQ"
        try:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=EMPLOYEE_GUIDE_VIDEO_FILE_ID,
                caption="📖 Hodim uchun qo'llanma\n\n"
                        "Ushbu videoda botdan qanday foydalanish ko'rsatilgan."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Qo'llanma videosini yuborishda xato:\n{str(e)}\n\n"
                "Iltimos, keyinroq qayta urinib ko'ring."
            )


async def show_office_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ofis sozlash menyusi"""
    keyboard = []
    
    # Agar mini app URL mavjud bo'lsa
    if config.MINI_APP_URL:
        keyboard.append([InlineKeyboardButton("🗺 Mini App Orqali", web_app=WebAppInfo(url=config.MINI_APP_URL))])
    
    keyboard.append([InlineKeyboardButton("📝 Qo'lda Kiritish", callback_data="manual_office_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏢 Ofis joyini qanday belgilashni xohlaysiz?",
        reply_markup=reply_markup
    )


async def show_daily_report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bugungi hisobot menyusi"""
    employees = db.get_all_employees()
    
    # Admin'ni ro'yxatdan chiqarish
    employees = [emp for emp in employees if not config.is_admin(emp['user_id'])]
    
    if not employees:
        await update.message.reply_text("📊 Hozircha hodimlar yo'q")
        return
    
    # Bugungi hisobotlar bormi tekshirish
    has_reports = False
    for emp in employees:
        logs = db.get_today_report(emp['user_id'])
        if logs:
            has_reports = True
            break
    
    if not has_reports:
        await update.message.reply_text("📊 Bugun hali hisobotlar yo'q\n\nHodimlar lokatsiya yuborishlari kutilmoqda.")
        return
    
    # Inline keyboard yaratish
    keyboard = []
    keyboard.append([InlineKeyboardButton("📈 Umumiy Hisobot", callback_data="general_report")])
    
    # Hodimlar ro'yxati (faqat hisoboti borlar)
    for emp in employees:
        logs = db.get_today_report(emp['user_id'])
        if logs:
            name = emp['name'] or emp['username'] or f"ID: {emp['user_id']}"
            keyboard.append([InlineKeyboardButton(f"👤 {name} ({len(logs)} ta)", callback_data=f"user_report_{emp['user_id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📊 Bugungi hisobot\n\n"
        "Umumiy hisobot yoki hodimni tanlang:",
        reply_markup=reply_markup
    )


async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hodimlar holati"""
    employees = db.get_all_active_employees()
    
    # Admin'ni ro'yxatdan chiqarish
    employees = [emp for emp in employees if not config.is_admin(emp[0])]
    
    if not employees:
        await update.message.reply_text("📊 Hozircha hodimlar yo'q")
        return
    
    present = []
    absent = []
    
    for user_id, username, full_name in employees:
        status = db.get_attendance_status(user_id)
        name = full_name or username or f"ID: {user_id}"
        if status and status['is_present']:
            present.append(f"✅ {name}")
        else:
            absent.append(f"❌ {name}")
    
    report = f"👥 Hodimlar Holati ({datetime.now().strftime('%H:%M')})\n\n"
    
    if present:
        report += "🟢 Ish joyida:\n" + "\n".join(present) + "\n\n"
    
    if absent:
        report += "🔴 Ish joyida emas:\n" + "\n".join(absent)
    
    await update.message.reply_text(report)


async def start_live_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Live map - Barcha hodimlarning real-time lokatsiyalari"""
    employees = db.get_all_active_employees()
    
    # Admin'ni ro'yxatdan chiqarish
    employees = [emp for emp in employees if not config.is_admin(emp[0])]
    
    if not employees:
        await update.message.reply_text("📍 Hozircha hodimlar yo'q")
        return
    
    await update.message.reply_text("🗺 Hodimlar Live Map yangilanmoqda...")
    
    active_locations = 0
    no_location = []
    
    for user_id, username, full_name in employees:
        name = full_name or username or f"ID: {user_id}"
        status = db.get_attendance_status(user_id)
        logs = db.get_today_report(user_id)
        
        # Oxirgi lokatsiyani topish
        if logs:
            last_log = logs[-1]  # Oxirgi yozuv
            
            lat = last_log['latitude']
            lng = last_log['longitude']
            distance = last_log['distance']
            timestamp = last_log['timestamp']
            
            status_icon = "✅" if status and status['is_present'] else "❌"
            
            # Har bir hodim uchun alohida live location yuborish
            try:
                location_msg = await context.bot.send_location(
                    chat_id=update.effective_chat.id,
                    latitude=lat,
                    longitude=lng,
                    live_period=900  # 15 daqiqa live - harakatlanganda yangilanadi
                )
                
                # Lokatsiya haqida ma'lumot
                info_text = (
                    f"{status_icon} {name}\n"
                    f"📏 Ofisdan: {distance:.1f}m\n"
                    f"⏰ Oxirgi: {format_date(timestamp)}\n"
                    f"{'🟢 Ofis hududida' if last_log['is_valid'] else '🔴 Ofis tashqarisida'}"
                )
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=info_text,
                    reply_to_message_id=location_msg.message_id
                )
                
                active_locations += 1
                
            except Exception as e:
                await update.message.reply_text(f"❌ {name}: Lokatsiya yuborishda xato")
        else:
            no_location.append(name)
    
    # Xulosa
    summary = f"✅ Live Map Tayyor!\n\n"
    summary += f"📍 {active_locations} ta LIVE lokatsiya yuborildi\n"
    summary += f"🔄 15 daqiqa davomida harakatlanganda yangilanadi\n\n"
    
    if no_location:
        summary += f"⚠️ Lokatsiya yo'q:\n"
        for name in no_location:
            summary += f"   • {name}\n"
    
    await update.message.reply_text(summary)


if __name__ == '__main__':
    main()
