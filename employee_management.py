"""
Hodimlarni boshqarish - ro'yxatdan o'tish, tasdiqlash, o'chirish
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from database import Database
import config
from work_hours_manager import set_employee_work_hours, load_employee_work_hours

logger = logging.getLogger(__name__)
db = Database()

# Conversation states
WAITING_APPROVE_START_TIME = 10
WAITING_APPROVE_END_TIME = 11

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi - ro'yxatdan o'tish"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "Noma'lum"
    full_name = user.full_name or username
    
    # Admin uchun
    if config.is_admin(user_id):
        # Admin klaviaturasi
        keyboard = [
            [KeyboardButton("📊 Hisobot"), KeyboardButton("👥 Kutish ro'yxati")],
            [KeyboardButton("🗑 Hodimni o'chirish"), KeyboardButton("🏢 Ofisni Belgilash")],
            [KeyboardButton("⏰ Ish Vaqtini Sozlash"), KeyboardButton("📅 Hisobot Oralig'i")],
            [KeyboardButton("📖 Qo'llanma")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"👋 Xush kelibsiz, Admin!\n\n"
            f"🎛 Admin paneli:\n"
            f"📊 Hisobot - Hodimlar hisoboti\n"
            f"👥 Kutish ro'yxati - Yangi foydalanuvchilar\n"
            f"🗑 Hodimni o'chirish - Hodimni tizimdan o'chirish\n"
            f"🏢 Ofisni Belgilash - Koordinatalar\n"
            f"⏰ Ish Vaqtini Sozlash - Vaqt belgilash\n"
            f"📅 Hisobot Oralig'i - Interval sozlash\n"
            f"📖 Qo'llanma - Bot ishlatish bo'yicha video",
            reply_markup=reply_markup
        )
        return
    
    # Tasdiqlangan hodim
    if db.is_approved(user_id):
        keyboard = [
            [KeyboardButton("📍 Lokatsiya yuborish")],
            [KeyboardButton("📊 Mening hisobotim"), KeyboardButton("📖 Qo'llanma")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"👋 Xush kelibsiz, {full_name}!\n\n"
            f"✅ Siz tizimga muvaffaqiyatli kirgansiz.\n"
            f"📍 Ishga kelganda 'Lokatsiya yuborish' tugmasini bosing.",
            reply_markup=reply_markup
        )
        return

    # Yangi yoki o'chirilgan hodim
    db.add_employee(user_id, username, full_name)
    
    # Adminlarga xabar berish
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🆕 Yangi hodim ro'yxatdan o'tdi!\n\n"
                     f"👤 {full_name}\n"
                     f"🆔 @{username}\n\n"
                     f"Tasdiqlash uchun '👥 Kutish ro'yxati' bo'limiga o'ting."
            )
        except Exception as e:
            logger.error(f"Adminga xabar yuborishda xato: {e}")
            
    await update.message.reply_text(
        f"👋 Assalomu alaykum, {full_name}!\n\n"
        f"✅ Sizning so'rovingiz adminga yuborildi.\n"
        f"⏳ Iltimos, tasdiqlashni kuting."
    )


async def show_pending_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kutish ro'yxatini ko'rsatish"""
    # Agar callback orqali chaqirilgan bo'lsa
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message_func = query.edit_message_text
    else:
        message_func = update.message.reply_text

    pending = db.get_pending_users()
    
    if not pending:
        await message_func("✅ Kutish ro'yxati bo'sh")
        return

    text = "👥 Tasdiqlashni kutayotganlar:\n\n"
    keyboard = []
    
    for user in pending:
        text += f"👤 {user['name']} (@{user['username']})\n"
        keyboard.append([
            InlineKeyboardButton(f"✅ {user['name']}", callback_data=f"approve_{user['user_id']}"),
            InlineKeyboardButton(f"❌ Rad etish", callback_data=f"reject_{user['user_id']}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message_func(text, reply_markup=reply_markup)


async def show_pending_users_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kutish ro'yxati (text message uchun)"""
    await show_pending_users(update, context)


async def start_approval_with_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tasdiqlash jarayonini boshlash (ish vaqti bilan)"""
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split("_")[1])
    
    # Context'ga saqlash
    context.user_data['approving_user_id'] = user_id
    
    # Hodim ma'lumotlarini olish
    pending = db.get_pending_users()
    user_info = None
    for user in pending:
        if user['user_id'] == user_id:
            user_info = user
            break
    
    if not user_info:
        await query.edit_message_text("❌ Foydalanuvchi topilmadi!")
        return ConversationHandler.END
    
    context.user_data['approving_user_name'] = user_info['name']
    context.user_data['approving_username'] = user_info['username']
    
    await query.edit_message_text(
        f"⏰ Ish vaqtini sozlash\n\n"
        f"👤 Hodim: {user_info['name']}\n"
        f"🆔 @{user_info['username']}\n\n"
        f"Ish boshlanish vaqtini kiriting (0-23):\n"
        f"Misol: 9"
    )
    
    return WAITING_APPROVE_START_TIME


async def receive_approval_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ish boshlanish vaqtini qabul qilish"""
    text = update.message.text.strip()
    
    try:
        start_hour = int(text)
        
        if not (0 <= start_hour < 24):
            await update.message.reply_text("❌ Vaqt 0-23 oralig'ida bo'lishi kerak!")
            return WAITING_APPROVE_START_TIME
        
        context.user_data['approve_start_hour'] = start_hour
        
        await update.message.reply_text(
            f"✅ Boshlanish: {start_hour}:00\n\n"
            f"Endi tugash vaqtini kiriting (0-23):\n"
            f"Misol: 18"
        )
        
        return WAITING_APPROVE_END_TIME
        
    except ValueError:
        await update.message.reply_text("❌ Iltimos, raqam kiriting (0-23)!")
        return WAITING_APPROVE_START_TIME


async def receive_approval_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugash vaqtini qabul qilish va tasdiqlash"""
    text = update.message.text.strip()
    
    try:
        end_hour = int(text)
        start_hour = context.user_data.get('approve_start_hour')
        
        if not (0 <= end_hour < 24):
            await update.message.reply_text("❌ Vaqt 0-23 oralig'ida bo'lishi kerak!")
            return WAITING_APPROVE_END_TIME
            
        if start_hour >= end_hour:
            await update.message.reply_text("❌ Tugash vaqti boshlanish vaqtidan katta bo'lishi kerak!")
            return WAITING_APPROVE_END_TIME
            
        # Ma'lumotlarni olish
        user_id = context.user_data.get('approving_user_id')
        user_name = context.user_data.get('approving_user_name')
        username = context.user_data.get('approving_username')
        
        # 1. Ish vaqtini saqlash
        set_employee_work_hours(user_id, start_hour, end_hour, username, user_name)
        
        # 2. Bazada tasdiqlash
        if db.approve_user(user_id):
            await update.message.reply_text(
                f"✅ Hodim muvaffaqiyatli tasdiqlandi!\n\n"
                f"👤 {user_name}\n"
                f"⏰ Ish vaqti: {start_hour}:00 - {end_hour}:00"
            )
            
            # Hodimga xabar
            try:
                keyboard = [
                    [KeyboardButton("📍 Lokatsiya yuborish")],
                    [KeyboardButton("📊 Mening hisobotim"), KeyboardButton("📖 Qo'llanma")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ Tabriklaymiz! Sizning arizangiz tasdiqlandi.\n\n"
                         f"⏰ Ish vaqtingiz: {start_hour}:00 - {end_hour}:00\n\n"
                         f"Endi botdan to'liq foydalanishingiz mumkin.",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Hodimga xabar yuborishda xato: {e}")
        else:
            await update.message.reply_text("❌ Bazaga yozishda xato bo'ldi!")
            
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Iltimos, raqam kiriting (0-23)!")
        return WAITING_APPROVE_END_TIME


async def cancel_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tasdiqlashni bekor qilish"""
    await update.message.reply_text("❌ Tasdiqlash bekor qilindi.")
    return ConversationHandler.END


async def reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None):
    """Foydalanuvchini rad etish"""
    # Agar user_id argument sifatida berilmagan bo'lsa (callback dan emas)
    if user_id is None:
        query = update.callback_query
        user_id = int(query.data.split("_")[1])
        await query.answer()
        message_func = query.edit_message_text
    else:
        message_func = update.message.reply_text

    if db.remove_employee(user_id):
        await message_func("❌ Foydalanuvchi rad etildi va o'chirildi.")
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Kechirasiz, sizning arizangiz rad etildi."
            )
        except:
            pass
    else:
        await message_func("❌ Xatolik yuz berdi")


async def show_remove_employee_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """O'chirish menyusi"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message_func = query.edit_message_text
    else:
        message_func = update.message.reply_text
        
    employees = db.get_all_active_employees()
    # Adminni chiqarib tashlash
    employees = [e for e in employees if not config.is_admin(e[0])]
    
    if not employees:
        await message_func("👥 O'chirish uchun hodimlar yo'q")
        return
        
    keyboard = []
    for user_id, username, full_name in employees:
        name = full_name or username or f"ID: {user_id}"
        keyboard.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"remove_{user_id}")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message_func("🗑 O'chiriladigan hodimni tanlang:", reply_markup=reply_markup)


async def show_remove_employee_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """O'chirish menyusi (text)"""
    await show_remove_employee_menu(update, context)


async def remove_employee(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None):
    """Hodimni o'chirish"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message_func = query.edit_message_text
        if user_id is None:
            user_id = int(query.data.split("_")[1])
    else:
        message_func = update.message.reply_text
        
    if db.remove_employee(user_id):
        await message_func("✅ Hodim muvaffaqiyatli o'chirildi.")
        
        # Ro'yxatni yangilash
        await show_remove_employee_menu(update, context)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Siz tizimdan o'chirildingiz.\nQayta ulanish uchun /start ni bosing."
            )
        except:
            pass
    else:
        await message_func("❌ Xatolik yuz berdi")


# ==================== ISH VAQTINI TAHRIRLASH (MAVJUD HODIMLAR) ====================

async def show_employees_for_work_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ish vaqtini sozlash uchun hodimlar ro'yxatini ko'rsatish"""
    # Agar callback orqali chaqirilgan bo'lsa
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message_func = query.edit_message_text
    else:
        message_func = update.message.reply_text

    employees = db.get_all_active_employees()
    
    if not employees:
        await message_func("📊 Hozircha hodimlar yo'q")
        return

    # Ish vaqtlarini yuklash
    work_hours_data = load_employee_work_hours()
    
    text = "⏰ Ish vaqtini sozlash uchun hodimni tanlang:\n\n"
    keyboard = []
    
    for user_id, username, full_name in employees:
        # Adminlarni o'tkazib yuborish
        if config.is_admin(user_id):
            continue
            
        name = full_name or username or f"ID: {user_id}"
        
        # Hozirgi ish vaqtini ko'rsatish
        user_hours = work_hours_data.get(str(user_id))
        if user_hours:
            time_str = f"({user_hours['work_start']}:00 - {user_hours['work_end']}:00)"
        else:
            time_str = "(Sozlanmagan)"
            
        text += f"👤 {name} {time_str}\n"
        
        keyboard.append([
            InlineKeyboardButton(f"✏️ {name}", callback_data=f"edit_hours_{user_id}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message_func(text, reply_markup=reply_markup)


async def start_edit_work_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ish vaqtini tahrirlashni boshlash"""
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split("_")[2])
    
    # Hodim ma'lumotlarini olish
    employees = db.get_all_active_employees()
    user_info = None
    for uid, uname, fname in employees:
        if uid == user_id:
            user_info = {"user_id": uid, "username": uname, "name": fname}
            break
    
    if not user_info:
        await query.edit_message_text("❌ Hodim topilmadi!")
        return ConversationHandler.END
        
    # Context'ga saqlash
    context.user_data['editing_user_id'] = user_id
    context.user_data['editing_user_name'] = user_info['name']
    context.user_data['editing_username'] = user_info['username']
    
    await query.edit_message_text(
        f"⏰ Ish vaqtini tahrirlash\n\n"
        f"👤 Hodim: {user_info['name']}\n"
        f"🆔 @{user_info['username']}\n\n"
        f"Yangi ish boshlanish vaqtini kiriting (0-23):\n"
        f"Misol: 9"
    )
    
    return 20  # WAITING_EDIT_START_TIME


async def receive_edit_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tahrirlash: Boshlanish vaqtini qabul qilish"""
    text = update.message.text.strip()
    
    try:
        start_hour = int(text)
        
        if not (0 <= start_hour < 24):
            await update.message.reply_text("❌ Vaqt 0-23 oralig'ida bo'lishi kerak!")
            return 20
        
        context.user_data['edit_start_hour'] = start_hour
        
        await update.message.reply_text(
            f"✅ Boshlanish: {start_hour}:00\n\n"
            f"Endi yangi tugash vaqtini kiriting (0-23):\n"
            f"Misol: 18"
        )
        
        return 21  # WAITING_EDIT_END_TIME
        
    except ValueError:
        await update.message.reply_text("❌ Iltimos, raqam kiriting (0-23)!")
        return 20


async def receive_edit_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tahrirlash: Tugash vaqtini qabul qilish va saqlash"""
    text = update.message.text.strip()
    
    try:
        end_hour = int(text)
        start_hour = context.user_data.get('edit_start_hour')
        
        if not (0 <= end_hour < 24):
            await update.message.reply_text("❌ Vaqt 0-23 oralig'ida bo'lishi kerak!")
            return 21
            
        if start_hour >= end_hour:
            await update.message.reply_text("❌ Tugash vaqti boshlanish vaqtidan katta bo'lishi kerak!")
            return 21
            
        # Ma'lumotlarni olish
        user_id = context.user_data.get('editing_user_id')
        user_name = context.user_data.get('editing_user_name')
        username = context.user_data.get('editing_username')
        
        # Saqlash
        set_employee_work_hours(user_id, start_hour, end_hour, username, user_name)
        
        # Adminga xabar
        await update.message.reply_text(
            f"✅ Ish vaqti yangilandi!\n\n"
            f"👤 {user_name}\n"
            f"⏰ Yangi vaqt: {start_hour}:00 - {end_hour}:00"
        )
        
        # Hodimga xabar
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"ℹ️ Sizning ish vaqtingiz o'zgartirildi.\n\n"
                     f"⏰ Yangi ish vaqti: {start_hour}:00 - {end_hour}:00"
            )
        except Exception as e:
            logger.error(f"Hodimga xabar yuborishda xato: {e}")
            
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Iltimos, raqam kiriting (0-23)!")
        return 21

async def cancel_edit_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tahrirlashni bekor qilish"""
    await update.message.reply_text("❌ Tahrirlash bekor qilindi.")
    return ConversationHandler.END
