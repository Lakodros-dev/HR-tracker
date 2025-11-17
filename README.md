# Worker Tracker Bot

Telegram bot hodimlarning lokatsiyasini kuzatish va davomat nazorati uchun.

## Xususiyatlar

- 📍 Avtomatik lokatsiya kuzatuvi
- ⏰ Ish vaqti va kechikish hisobi
- 📊 Kunlik statistika
- 🗺 Mini app orqali ofis hududini belgilash
- 👥 Hodimlarni boshqarish (tasdiqlash, o'chirish)
- 🔔 Avtomatik eslatmalar

## O'rnatish

```bash
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

**Admin:**
- `/start` - Admin paneli
- `/refresh` - Sozlamalarni yangilash

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

### Bot Deploy
1. VPS/Cloud server (DigitalOcean, AWS, etc.)
2. `git clone` repository
3. `.env` faylini sozlang
4. `pip install -r requirements.txt`
5. `python bot.py` (yoki systemd service)

### Mini App
Allaqachon deploy qilingan:
- Frontend: https://map-for-marking-domain-static1.onrender.com/
- Backend: https://map-for-marking-domain-1.onrender.com

## License

MIT
