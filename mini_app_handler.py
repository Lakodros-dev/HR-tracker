"""
Mini App ma'lumotlarini qayta ishlash
"""
import json
from telegram import Update
from telegram.ext import ContextTypes
import config


async def handle_mini_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mini App dan kelgan ma'lumotlarni qayta ishlash"""
    print("=" * 50)
    print("🔔 MINI APP MA'LUMOT KELDI!")
    print(f"User ID: {update.effective_user.id}")
    print(f"Admin ID: {config.ADMIN_ID}")
    print("=" * 50)
    
    if update.effective_user.id != config.ADMIN_ID:
        await update.message.reply_text("❌ Bu funksiya faqat admin uchun!")
        return
    
    try:
        # Web App dan kelgan ma'lumotlarni olish
        data = update.message.web_app_data.data
        print(f"📦 Kelgan ma'lumot (raw): {data}")
        
        import json
        location_data = json.loads(data)
        print(f"📊 JSON parse qilindi: {location_data}")
        
        # Bounds formatini tekshirish
        if 'bounds' in location_data:
            print("✅ Bounds formati topildi!")
            bounds = location_data['bounds']
            print(f"📍 Bounds: {bounds}")
            
            # Bounds'dan point1 va point2 yaratish
            point1 = {
                'lat': bounds['north'],
                'lng': bounds['west']
            }
            point2 = {
                'lat': bounds['south'],
                'lng': bounds['east']
            }
            
            # JSON bazaga saqlash
            update_area_env_file(point1, point2)
            
            # Hudud maydonini hisoblash
            area = calculate_area_from_points(point1, point2)
            
            # Javob yuborish
            await update.message.reply_text(
                f"✅ Hudud qabul qilindi!\n\n"
                f"📍 Shimol: {bounds['north']:.6f}\n"
                f"📍 Janub: {bounds['south']:.6f}\n"
                f"📍 Sharq: {bounds['east']:.6f}\n"
                f"📍 G'arb: {bounds['west']:.6f}\n\n"
                f"📐 Hudud: {area:.0f} m²\n\n"
                f"✅ Sozlamalar saqlandi!"
            )
            
            # Qo'shimcha ma'lumot
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [InlineKeyboardButton("📊 Hodimlar Holati", callback_data="admin_status")],
                [InlineKeyboardButton("🗺 Xaritada Ko'rish", callback_data="view_on_map")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Keyingi qadamlar:",
                reply_markup=reply_markup
            )
        
        # Eski format (action bilan)
        elif 'action' in location_data:
            action = location_data.get('action')
            
            if action == 'set_office_location':
                # Oddiy lokatsiya (nuqta + radius)
                latitude = location_data.get('latitude')
                longitude = location_data.get('longitude')
                radius = location_data.get('radius', 100)
                
                if latitude and longitude:
                    update_location_env_file(latitude, longitude, radius)
                    
                    await update.message.reply_text(
                        f"✅ Ofis joyi o'rnatildi!\n\n"
                        f"📍 Latitude: {latitude:.6f}\n"
                        f"📍 Longitude: {longitude:.6f}\n"
                        f"🔵 Radius: {radius} metr"
                    )
                else:
                    await update.message.reply_text("❌ Koordinatalar topilmadi!")
            
            elif action == 'set_office_area':
                # Hudud (ikki nuqta)
                point1 = location_data.get('point1')
                point2 = location_data.get('point2')
                
                if point1 and point2:
                    update_area_env_file(point1, point2)
                    area = calculate_area_from_points(point1, point2)
                    
                    await update.message.reply_text(
                        f"✅ Ofis hududi o'rnatildi!\n\n"
                        f"📍 1-nuqta: {point1['lat']:.6f}, {point1['lng']:.6f}\n"
                        f"📍 2-nuqta: {point2['lat']:.6f}, {point2['lng']:.6f}\n"
                        f"📐 Hudud: {area:.0f} m²"
                    )
                else:
                    await update.message.reply_text("❌ Hudud nuqtalari topilmadi!")
        
        else:
            await update.message.reply_text("❌ Noma'lum ma'lumot formati!")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON xato: {e}")
        await update.message.reply_text(f"❌ JSON o'qishda xato: {str(e)}")
    except Exception as e:
        print(f"❌ Umumiy xato: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"❌ Xato: {str(e)}")


def update_location_env_file(latitude, longitude, radius):
    """Lokatsiya JSON bazaga yangilash"""
    from settings_manager import update_office_location
    return update_office_location(latitude, longitude, radius)


def update_area_env_file(point1, point2):
    """Hudud JSON bazaga yangilash"""
    from settings_manager import update_office_area
    return update_office_area(point1, point2)


def calculate_area_from_points(point1, point2):
    """Ikki nuqta orqali hudud maydonini hisoblash"""
    import math
    R = 6371000  # Earth's radius in meters
    
    lat1 = point1['lat'] * math.pi / 180
    lat2 = point2['lat'] * math.pi / 180
    lng1 = point1['lng'] * math.pi / 180
    lng2 = point2['lng'] * math.pi / 180
    
    dlat = abs(lat2 - lat1)
    dlng = abs(lng2 - lng1)
    
    # Calculate distances
    lat_distance = dlat * R
    lng_distance = dlng * R * math.cos((lat1 + lat2) / 2)
    
    return lat_distance * lng_distance
