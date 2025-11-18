# Render.com Deploy Qo'llanma 🚀

## Tezkor Deploy

### 1. GitHub Repository
✅ Repository tayyor: https://github.com/Lakodros-dev/HR-tracker.git

### 2. Render.com Sozlamalari

#### A. Yangi Web Service yarating
1. [Render Dashboard](https://dashboard.render.com/) ga kiring
2. **"New +"** → **"Web Service"** tanlang
3. GitHub repository ni ulang: `Lakodros-dev/HR-tracker`

#### B. Sozlamalar (rasmda ko'rsatilganidek)

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
python bot.py
```

**Python Runtime:**
```
Python 3.11.9
```
⚠️ **Muhim:** Python 3.13 ishlatmang! Faqat 3.11.x

#### C. Environment Variables

Quyidagi o'zgaruvchilarni qo'shing:

```env
BOT_TOKEN=7838291404:AAHUp8U6IcHCmU1LouUhPyUNHGZDn82f6VU
ADMIN_ID=sizning_telegram_id_raqamingiz
OFFICE_LATITUDE=41.2995
OFFICE_LONGITUDE=69.2401
ALLOWED_DISTANCE=100
MINI_APP_URL=https://map-for-marking-domain-static1.onrender.com/
BACKEND_URL=https://map-for-marking-domain-1.onrender.com
```

**ADMIN_ID ni qanday topish:**
1. Telegram da `@userinfobot` ga `/start` yuboring
2. Sizning ID raqamingizni ko'rsatadi
3. Shu raqamni `ADMIN_ID` ga kiriting

### 3. Deploy Boshlash

1. **"Create Web Service"** tugmasini bosing
2. Deploy jarayoni boshlanadi (3-5 daqiqa)
3. **Logs** bo'limida quyidagi xabarni kutamiz:
   ```
   🤖 Bot ishga tushdi!
   ```

### 4. Tekshirish

Deploy muvaffaqiyatli bo'lsa:
- ✅ Logs da `🤖 Bot ishga tushdi!` ko'rinadi
- ✅ Telegram botga `/start` yuboring
- ✅ Admin klaviaturasi paydo bo'ladi

## Muammolarni Hal Qilish

### Xato: Python 3.13 AttributeError
**Sabab:** Python 3.13 qo'llab-quvvatlanmaydi

**Yechim:**
1. Render sozlamalarida **Runtime** ni `Python 3.11.9` ga o'zgartiring
2. Redeploy qiling

### Xato: BOT_TOKEN topilmadi
**Sabab:** Environment Variables to'g'ri kiritilmagan

**Yechim:**
1. Render Dashboard → Service → Environment
2. `BOT_TOKEN` ni tekshiring
3. Redeploy qiling

### Xato: Backend dan sozlamalar olinmadi (404)
**Ogohlantirish:** Bu normal, local `settings.json` ishlatiladi

**Agar muammo bo'lsa:**
1. `BACKEND_URL` to'g'ri ekanligini tekshiring
2. Backend service ishlayotganligini tekshiring

### Bot ishlamayapti
**Tekshirish:**
1. Logs ni o'qing
2. Environment Variables to'liq ekanligini tekshiring
3. `ADMIN_ID` raqam ekanligini tekshiring (string emas!)

## Qo'shimcha Ma'lumot

### Free Plan Cheklovlari
- ✅ 750 soat/oy (yetarli)
- ✅ 512 MB RAM
- ⚠️ 15 daqiqa faoliyatsizlikdan keyin uxlaydi
- ⚠️ Birinchi so'rovda uyg'onishi 30 sekund oladi

### Uxlashni Oldini Olish
Render Free plan da bot 15 daqiqa faoliyatsizlikdan keyin uxlaydi.

**Yechim:** Cron job yoki UptimeRobot ishlatib, har 10 daqiqada ping yuboring.

### Monitoring
- Render Dashboard → Logs
- Telegram bot orqali `/refresh` komandasi

## Tayyor! 🎉

Bot deploy qilindi va ishlayapti!

**Keyingi qadamlar:**
1. Botga `/start` yuboring
2. Admin klaviaturasini ko'ring
3. Hodimlarni qo'shing va test qiling

---

**Yordam kerakmi?**
- [Render Documentation](https://render.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
