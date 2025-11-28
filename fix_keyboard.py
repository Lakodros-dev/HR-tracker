with open('employee_management.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 31-qatorni o'zgartirish
old_line = '            [KeyboardButton("📖 Qo\'llanma")]'
new_line = '            [KeyboardButton("📆 Oylik Hisobot"), KeyboardButton("📖 Qo\'llanma")]'

content = content.replace(old_line, new_line)

# 44-qatorga qo'shish
old_text = '            f"📅 Hisobot Oralig\'i - Interval sozlash\\n"\n            f"📖 Qo\'llanma - Bot ishlatish bo\'yicha video"'
new_text = '            f"📅 Hisobot Oralig\'i - Interval sozlash\\n"\n            f"📆 Oylik Hisobot - Hodim ish soatlari\\n"\n            f"📖 Qo\'llanma - Bot ishlatish bo\'yicha video"'

content = content.replace(old_text, new_text)

with open('employee_management.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fayl yangilandi!")
