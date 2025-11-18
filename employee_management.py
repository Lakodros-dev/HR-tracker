"""
Hodimlarni boshqarish - ro'yxatdan o'tish, tasdiqlash, o'chirish
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import Database
import config

logger = logging.getLogger(__name__)
db = Database()


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi - ro'yxatdan o'tish"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "Noma'lum"
    full_name = user.full_name or username
    
    # Admin uchun
    if config.is_admin(user_id):
        from telegram import KeyboardButton, ReplyKeyboardMarkup
        
        # Admin klaviaturasi
        keyboard = [
            [KeyboardButton("📊 Bugungi Hisobot"), KeyboardButton("👥 Kutish ro'yxati")],
            [KeyboardButton("🗑 Hodimni o'chirish"), KeyboardButton("🏢 Ofisni Belgilash")],
            [KeyboardButton("⏰ Ish Vaqtini Sozlash"), KeyboardButton("📅 Hisobot Oralig'i")],
            [KeyboardButton("📖 Qo'llanma")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"👋 Xush kelibsiz, Admin!\n\n"
            f"🎛 Admin paneli:\n"
            f"📊 Bugungi Hisobot - Hodimlar hisoboti\n"
            f"👥 Kutish ro'yxati - Yangi foydalanuvchilar\n"
            f"🗑 Hodimni o'chirish - Hodimni tizimdan o'chirish\n"
            f"🏢 Ofisni Belgilash - Koordinatalar\n"
            f"⏰ Ish Vaqtini Sozlash - Vaqt belgilash\n"
            f"📅 Hisobot Oralig'i - Interval sozlash\n"
            f"📖 Qo'llanma - Bot ishlatish bo'yicha video",
            reply_markup=reply_markup
        )
        return
    
    # Hodim allaqachon ro'yxatdan o'tgan
    if db.is_employee(user_id):
        if db.is_approved(user_id):
            from telegram import KeyboardButton, ReplyKeyboardMarkup
            
            # Hodim klaviaturasi
            keyboard = [
                [KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)],
                [KeyboardButton("📊 Mening hisobotim")],
                [KeyboardButton("📖 Qo'llanma")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"👋 Xush kelibsiz, {full_name}!\n\n"
                f"Siz allaqachon tizimda ro'yxatdan o'tgansiz.\n\n"
                f"📍 Lokatsiya yuborish\n"
                f"📊 Mening hisobotim\n"
                f"📖 Qo'llanma - Bot ishlatish bo'yicha video",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                f"⏳ Sizning arizangiz ko'rib chiqilmoqda.\n\n"
                f"Admin tasdiqlashini kuting."
            )
        return
    
    # Yangi hodim - ro'yxatdan o'tish
    db.add_employee(user_id, username, full_name)
    
    # Adminni xabardor qilish
    # Barcha adminlarga xabar yuborish
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🆕 Yangi foydalanuvchi!\n\n"
                     f"👤 Ism: {full_name}\n"
                     f"🆔 Username: @{username}\n"
                     f"🔢 ID: {user_id}\n\n"
                     f"Tasdiqlash uchun /pending komandasi",
            )
        except Exception as e:
            logger.error(f"Admin {admin_id} ga xabar yuborishda xato: {e}")
    
    await update.message.reply_text(
        f"✅ Ro'yxatdan o'tdingiz!\n\n"
        f"👤 Ism: {full_name}\n"
        f"🆔 Username: @{username}\n\n"
        f"⏳ Admin tasdiqlashini kuting.\n"
        f"Tasdiqlangandan keyin lokatsiya yuborishingiz mumkin bo'ladi."
    )


async def show_pending_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kutish ro'yxatidagi foydalanuvchilarni ko'rsatish (callback)"""
    query = update.callback_query
    await query.answer()
    
    pending = db.get_pending_users()
    
    if not pending:
        await query.edit_message_text("✅ Kutish ro'yxati bo'sh")
        return
    
    text = "👥 Kutish ro'yxati:\n\n"
    keyboard = []
    
    for user in pending:
        text += f"👤 {user['name']}\n"
        text += f"🆔 @{user['username']} (ID: {user['user_id']})\n"
        text += f"📅 {user['created_at']}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(f"✅ {user['name']}", callback_data=f"approve_{user['user_id']}"),
            InlineKeyboardButton(f"❌ Rad etish", callback_data=f"reject_{user['user_id']}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)


async def show_pending_users_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kutish ro'yxatidagi foydalanuvchilarni ko'rsatish (text)"""
    pending = db.get_pending_users()
    
    if not pending:
        await update.message.reply_text("✅ Kutish ro'yxati bo'sh")
        return
    
    text = "👥 Kutish ro'yxati:\n\n"
    keyboard = []
    
    for user in pending:
        text += f"👤 {user['name']}\n"
        text += f"🆔 @{user['username']} (ID: {user['user_id']})\n"
        text += f"📅 {user['created_at']}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(f"✅ {user['name']}", callback_data=f"approve_{user['user_id']}"),
            InlineKeyboardButton(f"❌ Rad etish", callback_data=f"reject_{user['user_id']}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Foydalanuvchini tasdiqlash"""
    query = update.callback_query
    await query.answer("✅ Tasdiqlandi!")
    
    db.approve_user(user_id)
    
    # Foydalanuvchiga xabar va klaviatura
    try:
        from telegram import KeyboardButton, ReplyKeyboardMarkup
        
        keyboard = [
            [KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)],
            [KeyboardButton("📊 Mening hisobotim")],
            [KeyboardButton("📖 Qo'llanma")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 Tabriklaymiz!\n\n"
                 "Sizning arizangiz tasdiqlandi.\n"
                 "Endi lokatsiya yuborishingiz mumkin.\n\n"
                 "📍 Lokatsiya yuborish\n"
                 "📊 Mening hisobotim\n"
                 "📖 Qo'llanma - Bot ishlatish bo'yicha video",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Foydalanuvchiga xabar yuborishda xato: {e}")
    
    # Yangilangan ro'yxatni ko'rsatish
    await show_pending_users(update, context)


async def reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Foydalanuvchini rad etish"""
    query = update.callback_query
    await query.answer("❌ Rad etildi!")
    
    db.reject_user(user_id)
    
    # Foydalanuvchiga xabar
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Arizangiz rad etildi.\n\n"
                 "Agar bu xato bo'lsa, admin bilan bog'laning."
        )
    except Exception as e:
        logger.error(f"Foydalanuvchiga xabar yuborishda xato: {e}")
    
    # Yangilangan ro'yxatni ko'rsatish
    await show_pending_users(update, context)


async def show_remove_employee_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hodimni o'chirish menyusi (callback)"""
    query = update.callback_query
    await query.answer()
    
    employees = db.get_all_employees()
    
    if not employees:
        await query.edit_message_text("📊 Hodimlar yo'q")
        return
    
    text = "🗑 Hodimni o'chirish:\n\n"
    keyboard = []
    
    for emp in employees:
        text += f"👤 {emp['name']} (@{emp['username']})\n"
        keyboard.append([
            InlineKeyboardButton(f"🗑 {emp['name']}", callback_data=f"remove_{emp['user_id']}")
        ])
    
    keyboard.append([InlineKeyboardButton("« Orqaga", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)


async def show_remove_employee_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hodimni o'chirish menyusi (text)"""
    employees = db.get_all_employees()
    
    if not employees:
        await update.message.reply_text("📊 Hodimlar yo'q")
        return
    
    text = "🗑 Hodimni o'chirish:\n\n"
    keyboard = []
    
    for emp in employees:
        text += f"👤 {emp['name']} (@{emp['username']})\n"
        keyboard.append([
            InlineKeyboardButton(f"🗑 {emp['name']}", callback_data=f"remove_{emp['user_id']}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def remove_employee(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Hodimni o'chirish"""
    query = update.callback_query
    await query.answer("🗑 O'chirildi!")
    
    db.remove_employee(user_id)
    
    # Hodimga xabar
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Siz tizimdan o'chirildingiz.\n\n"
                 "Agar bu xato bo'lsa, admin bilan bog'laning."
        )
    except Exception as e:
        logger.error(f"Hodimga xabar yuborishda xato: {e}")
    
    await query.edit_message_text(
        f"✅ Hodim o'chirildi!\n\n"
        f"ID: {user_id}"
    )
