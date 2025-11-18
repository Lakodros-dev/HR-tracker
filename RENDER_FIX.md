# Render Deploy Xatosini Tuzatish ⚠️

## Xato
```
Timed out: Port scan timeout reached, no open ports detected.
Bind your service to at least one port.
If you don't need to receive traffic on any port, create a background worker instead.
```

## Sabab
Telegram bot hech qanday HTTP portni tinglamaydi, lekin siz "Web Service" yaratdingiz.

## Yechim

### Variant 1: Mavjud Service ni O'chirish va Qayta Yaratish (Tavsiya etiladi)

1. **Eski service ni o'chiring:**
   - Render Dashboard → Service → Settings
   - Pastga scroll qiling
   - "Delete Service" tugmasini bosing

2. **Yangi Background Worker yarating:**
   - "New +" → **"Background Worker"** (Web Service emas!)
   - GitHub: `Lakodros-dev/HR-tracker`
   - Branch: `main`
   - Runtime: `Python 3.11.9`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`

3. **Environment Variables qo'shing:**
   ```
   BOT_TOKEN=7838291404:AAHUp8U6IcHCmU1LouUhPyUNHGZDn82f6VU
   ADMIN_ID=sizning_telegram_id
   OFFICE_LATITUDE=41.2995
   OFFICE_LONGITUDE=69.2401
   ALLOWED_DISTANCE=100
   MINI_APP_URL=https://map-for-marking-domain-static1.onrender.com/
   BACKEND_URL=https://map-for-marking-domain-1.onrender.com
   ```

4. **"Create Background Worker"** tugmasini bosing

### Variant 2: render.yaml Ishlatish

Agar `render.yaml` faylini ishlatmoqchi bo'lsangiz:

1. Repository da `render.yaml` mavjud (allaqachon `type: worker` ga o'zgartirilgan)
2. Render Dashboard da "New +" → "Blueprint"
3. Repository ni tanlang
4. Render avtomatik ravishda `render.yaml` ni o'qiydi va Background Worker yaratadi

## Web Service vs Background Worker

| Xususiyat | Web Service | Background Worker |
|-----------|-------------|-------------------|
| HTTP Port | Kerak ✅ | Kerak emas ❌ |
| Telegram Bot | Ishlamaydi ❌ | Ishlaydi ✅ |
| Uxlash (Free) | 15 daqiqada | Uxlamaydi |
| Narx | Free/Paid | Free/Paid |

## Tekshirish

Deploy muvaffaqiyatli bo'lsa:
- ✅ Logs da `🤖 Bot ishga tushdi!` ko'rinadi
- ✅ Telegram botga `/start` yuboring
- ✅ Admin klaviaturasi paydo bo'ladi

## Qo'shimcha Yordam

Agar muammo davom etsa:
1. Logs ni diqqat bilan o'qing
2. Environment Variables to'liq ekanligini tekshiring
3. Python versiyasi 3.11.9 ekanligini tekshiring (3.13 emas!)

---

**Muhim:** Background Worker yaratganingizdan keyin, eski Web Service ni o'chirishni unutmang!
