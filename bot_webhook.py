"""
Bot uchun webhook server - backend dan settings yangilash uchun
"""
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

SETTINGS_FILE = 'settings.json'

@app.route('/api/update_settings', methods=['POST'])
def update_settings():
    """Backend dan settings yangilash"""
    try:
        data = request.json
        print(f"📥 Yangi settings keldi: {data}")
        
        # Mavjud settings ni o'qish
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            settings = {}
        
        # Yangi ma'lumotlarni qo'shish
        if 'office_area' in data:
            settings['office_area'] = data['office_area']
            settings['use_area_mode'] = data.get('use_area_mode', True)
            print(f"✅ Office area yangilandi: {settings['office_area']}")
        
        # Faylga yozish
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Settings.json saqlandi!")
        
        # Bot cache ni tozalash
        try:
            from settings_manager import clear_cache
            clear_cache()
            print(f"🔄 Bot cache tozalandi!")
        except Exception as cache_error:
            print(f"⚠️ Cache tozalashda xato: {cache_error}")
        
        return jsonify({
            'success': True,
            'message': 'Settings yangilandi'
        })
    
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("🚀 Bot webhook server ishga tushmoqda...")
    print(f"📁 Settings fayl: {os.path.abspath(SETTINGS_FILE)}")
    app.run(host='0.0.0.0', port=5000, debug=True)
