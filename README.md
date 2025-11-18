# Worker Tracker Bot

Telegram bot hodimlarning lokatsiyasini kuzatish va davomat nazorati uchun.

## Xususiyatlar

- 📍 Avtomatik lokatsiya kuzatuvi
- ⏰ Ish vaqti va kechikish hisobi
- 📊 Kunlik statistika
- 🗺 Mini app orqali ofis hududini belgilash
- 👥 Hodimlarni boshqarish (tasdiqlash, o'chirish)
- 🔔 Avtomatik eslatmalar
- 📖 Video qo'llanma (admin va hodimlar uchun)

## O'rnatish

**Talablar:**
- Python 3.11.x (3.13 qo'llab-quvvatlanmaydi)
- pip

```bash
# Python versiyasini tekshirish
python --version  # 3.11.x bo'lishi kerak

# Dependencies
pip install -r requirements.txt

# .env faylini sozlash
cp .env.example .env
# BOT_TOKEN, ADMIN_ID va boshqalarni to'ldiring
```

## Ishga Tushirish

```bash
# Bot
python bot.py

# Bot webhook (ixtiyoriy - local test uchun)
python bot_webhook.py
```

## Mini App Deploy

Mini app alohida deploy qilingan:
- Frontend: https://map-for-marking-domain-static1.onrender.com/
- Backend: https://map-for-marking-domain-1.onrender.com

Agar o'zingizning mini app ni deploy qilmoqchi bo'lsangiz:
1. `WorkerTrackerOfficeMap/` papkasini alohida repository ga ko'chiring
2. Render/Vercel/Netlify da deploy qiling
3. `.env` da `MINI_APP_URL` va `BACKEND_URL` ni yangilang

## Sozlamalar

`settings.json` faylida:
- `work_hours` - Ish vaqti
- `lunch_hours` - Tushlik vaqti
- `location_interval` - Lokatsiya so'rash oralig'i
- `office_area` - Ofis hududi (mini app orqali belgilanadi)

## Komandalar

**Hodim:**
- `/start` - Ro'yxatdan o'tish
- `/report` - Bugungi hisobot
- 📖 Qo'llanma - Video qo'llanma

**Admin:**
- `/start` - Admin paneli
- `/refresh` - Sozlamalarni yangilash
- 📖 Qo'llanma - Admin uchun video qo'llanma

## Arxitektura

```
bot.py                  # Asosiy bot
database.py             # SQLite database
scheduler_tasks.py      # Avtomatik vazifalar
employee_management.py  # Hodimlarni boshqarish
work_time_tracker.py    # Ish vaqti kuzatuvi
settings_manager.py     # Sozlamalar (backend dan)
config.py               # Konfiguratsiya
utils.py                # Yordamchi funksiyalar

Mini App (alohida deploy):
  Frontend: Render/Vercel
  Backend: Render
```

## Deployment

### Render.com da Deploy (Tavsiya etiladi)

#### 1. GitHub Repository
Repository allaqachon tayyor: https://github.com/Lakodros-dev/HR-tracker.git

#### 2. Render.com da yangi Web Service yarating
1. [Render Dashboard](https://dashboard.render.com/) ga kiring
2. "New +" → "Web Service" tanlang
3. GitHub repository ni ulang: `Lakodros-dev/HR-tracker`
4. Quyidagi sozlamalarni kiriting:

**Asosiy sozlamalar:**
- **Name:** `worker-tracker-bot` (yoki istalgan nom)
- **Region:** Oregon (yoki yaqin region)
- **Branch:** `main`
- **Runtime:** `Python 3.11.9` ⚠️ (3.13 emas!)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python bot.py`
- **Instance Type:** `Free` (yoki istalgan plan)

**Environment Variables (muhim!):**
```
BOT_TOKEN=7838291404:AAHUp8U6IcHCmU1LouUhPyUNHGZDn82f6VU
ADMIN_ID=sizning_telegram_id
OFFICE_LATITUDE=41.2995
OFFICE_LONGITUDE=69.2401
ALLOWED_DISTANCE=100
MINI_APP_URL=https://map-for-marking-domain-static1.onrender.com/
BACKEND_URL=https://map-for-marking-domain-1.onrender.com
```

5. "Create Web Service" tugmasini bosing
6. Deploy jarayoni avtomatik boshlanadi (3-5 daqiqa)

#### 3. Deploy holatini kuzatish
- Logs bo'limida `🤖 Bot ishga tushdi!` xabarini ko'rishingiz kerak
- Agar xato bo'lsa, Environment Variables to'g'ri kiritilganligini tekshiring

### VPS/Cloud Server da Deploy
1. VPS/Cloud server (DigitalOcean, AWS, etc.)
2. `git clone https://github.com/Lakodros-dev/HR-tracker.git`
3. `.env` faylini sozlang
4. `pip install -r requirements.txt`
5. `python bot.py` (yoki systemd service)

### Mini App
Allaqachon deploy qilingan:
- Frontend: https://map-for-marking-domain-static1.onrender.com/
- Backend: https://map-for-marking-domain-1.onrender.com

## License

MIT
