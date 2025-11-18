# Deployment Tayyor ✅

## O'zgarishlar

### 1. Mini App Alohida Deploy
- ✅ Mini app papkasi `.gitignore` ga qo'shildi
- ✅ Frontend: https://map-for-marking-domain-static1.onrender.com/
- ✅ Backend: https://map-for-marking-domain-1.onrender.com
- ✅ Bot faqat API orqali ulanadi

### 2. Production Sozlamalari
- ✅ `.env` da `BACKEND_URL` production ga o'zgartirildi
- ✅ `.env.example` yangilandi
- ✅ Barcha qo'llanmalar yangilandi

### 3. Optimizatsiya
- ✅ 18 ta keraksiz fayl o'chirildi
- ✅ Faqat 15 ta asosiy fayl qoldi
- ✅ Loyiha hajmi ~70% kamaydi

## Deployment Qadamlari

### Render.com da Deploy (Tavsiya etiladi) ⭐

#### 1. GitHub Repository
Repository: https://github.com/Lakodros-dev/HR-tracker.git

#### 2. Render.com Sozlamalari
1. [Render Dashboard](https://dashboard.render.com/) ga kiring
2. "New +" → "Web Service"
3. GitHub repository: `Lakodros-dev/HR-tracker`

**Build & Start:**
```
Build Command: pip install -r requirements.txt
Start Command: python bot.py
```

**Environment Variables:**
```
BOT_TOKEN=7838291404:AAHUp8U6IcHCmU1LouUhPyUNHGZDn82f6VU
ADMIN_ID=sizning_telegram_id
OFFICE_LATITUDE=41.2995
OFFICE_LONGITUDE=69.2401
ALLOWED_DISTANCE=100
MINI_APP_URL=https://map-for-marking-domain-static1.onrender.com/
BACKEND_URL=https://map-for-marking-domain-1.onrender.com
```

4. "Create Web Service" → Deploy boshlanadi (3-5 daqiqa)
5. Logs da `🤖 Bot ishga tushdi!` xabarini kutamiz

### Bot Deploy (VPS/Cloud)

```bash
# 1. Repository clone
git clone https://github.com/Lakodros-dev/HR-tracker.git
cd HR-tracker

# 2. Dependencies
pip install -r requirements.txt

# 3. Environment
cp .env.example .env
nano .env  # BOT_TOKEN, ADMIN_ID ni to'ldiring

# 4. Ishga tushirish
python bot.py

# 5. Systemd service (ixtiyoriy)
sudo nano /etc/systemd/system/worker-bot.service
sudo systemctl enable worker-bot
sudo systemctl start worker-bot
```

### Systemd Service Misoli

```ini
[Unit]
Description=Worker Tracker Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/worker-tracker-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Tekshirish

```bash
# Bot ishlayaptimi?
systemctl status worker-bot

# Loglarni ko'rish
journalctl -u worker-bot -f

# Database
ls -lh attendance.db
```

## Mini App

Allaqachon deploy qilingan va ishlayapti:
- ✅ Frontend: Render
- ✅ Backend: Render
- ✅ Bot bilan integratsiya qilingan

## Xavfsizlik

⚠️ **Muhim:**
- `.env` faylini git ga commit qilmang
- `BOT_TOKEN` ni hech qayerda oshkor qilmang
- Database backup oling
- HTTPS ishlatilsin

## Monitoring

- Bot loglarini kuzating
- Database hajmini tekshiring
- Server resurslarini monitoring qiling

## Backup

```bash
# Database backup
cp attendance.db attendance.db.backup

# Cron job (har kuni)
0 0 * * * cp /path/to/attendance.db /path/to/backups/attendance-$(date +\%Y\%m\%d).db
```

## Hammasi tayyor! 🚀

Bot production uchun tayyor va deploy qilishingiz mumkin.
