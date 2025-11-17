# Tezkor Boshlash

## 1. O'rnatish

```bash
pip install -r requirements.txt
```

## 2. Sozlash

`.env` faylini yarating:
```env
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
MINI_APP_URL=https://map-for-marking-domain-static1.onrender.com/
BACKEND_URL=https://map-for-marking-domain-1.onrender.com
```

**Eslatma:** Mini app allaqachon deploy qilingan. Yuqoridagi URL larni ishlatishingiz mumkin.

## 3. Ishga Tushirish

```bash
# Bot
python bot.py
```

## 4. Test Qilish

1. Telegram botda `/start` yuboring
2. Admin sifatida "👥 Kutish ro'yxati" ni oching
3. O'zingizni tasdiqlang
4. Lokatsiya yuboring

## 5. Mini App

Mini app allaqachon deploy qilingan va ishlayapti:
- Frontend: https://map-for-marking-domain-static1.onrender.com/
- Backend: https://map-for-marking-domain-1.onrender.com

BotFather da mini app URL ni sozlang (yuqoridagi frontend URL)

## Muammolar?

- Bot ishlamayapti? → `BOT_TOKEN` to'g'rimi?
- Lokatsiya qabul qilinmayapti? → Tasdiqlangan-tasdiqlanmaganini tekshiring
- Mini app ishlamayapti? → Backend ishlamoqdami?

## Asosiy Fayllar

- `bot.py` - Asosiy bot
- `database.py` - Ma'lumotlar bazasi
- `scheduler_tasks.py` - Avtomatik vazifalar
- `settings.json` - Sozlamalar

**Eslatma:** Mini app alohida deploy qilingan, bot faqat API orqali ulanadi.
