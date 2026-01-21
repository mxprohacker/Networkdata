import telebot
from telebot import types

# --- ማሳሰቢያ፡ Token እና ID በድጋሚ ማረጋገጥዎን አይርሱ ---
API_TOKEN = '8148403216:AAElZ4fJTPpANRzXDSz9_TTVOjeWZpgRhjQ'
ADMIN_ID = 7813450584 

bot = telebot.TeleBot(API_TOKEN)

# ዳታ መዋቅር
bot_data = {
    "main_buttons": ["📚 Tutorials", "📢 News"],
    "sub_buttons": {
        "📚 Tutorials": ["Python", "JavaScript"],
        "📢 News": ["Tech News", "Bot Updates"]
    },
    "contents": {},
    "users": set() 
}

def build_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btns = [types.KeyboardButton(b) for b in bot_data["main_buttons"]]
    markup.add(*btns)
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton('⚙️ Admin Panel'))
    return markup

def build_sub_menu(parent_btn):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    subs = bot_data["sub_buttons"].get(parent_btn, [])
    btns = [types.KeyboardButton(s) for s in subs]
    markup.add(*btns)
    markup.add(types.KeyboardButton('🔙 ወደ ኋላ ተመለስ'))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot_data["users"].add(message.chat.id)
    bot.send_message(message.chat.id, "እንኳን ወደ 𝗠𝗫 ረዳት bot በደህና መጡ!", reply_markup=build_main_menu(message.from_user.id))

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    text = message.text
    user_id = message.from_user.id
    bot_data["users"].add(message.chat.id)

    if text == '🔙 ወደ ኋላ ተመለስ':
        bot.send_message(message.chat.id, "ወደ ዋናው ገጽ ተመልሰዋል", reply_markup=build_main_menu(user_id))
    
    elif text in bot_data["main_buttons"]:
        bot.send_message(message.chat.id, f"የ {text} ዝርዝር፦", reply_markup=build_sub_menu(text))
    
    elif any(text in subs for subs in bot_data["sub_buttons"].values()):
        data = bot_data["contents"].get(text)
        if not data:
            bot.send_message(message.chat.id, "ለዚህ ክፍል መረጃ አልተጻፈም")
        else:
            # የይዘት አይነቶችን ማረጋገጥ (Document ተጨምሯል)
            if data['type'] == 'text':
                bot.send_message(message.chat.id, data['value'])
            elif data['type'] == 'photo':
                bot.send_photo(message.chat.id, data['value'], caption=data.get('caption', ''))
            elif data['type'] == 'video':
                bot.send_video(message.chat.id, data['value'], caption=data.get('caption', ''))
            elif data['type'] == 'document':
                bot.send_document(message.chat.id, data['value'], caption=data.get('caption', ''))

    elif text == '⚙️ Admin Panel' and user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("➕ ዋና Button ጨምር", callback_data="add_main"),
            types.InlineKeyboardButton("➕ ንዑስ Button ጨምር", callback_data="add_sub_select"),
            types.InlineKeyboardButton("📝 ይዘት (Content) ቀይር", callback_data="edit_content_select"),
            types.InlineKeyboardButton("✏️ የባተን ስም ቀይር", callback_data="rename_btn_select"),
            types.InlineKeyboardButton("❌ Button አጥፋ", callback_data="delete_btn"),
            types.InlineKeyboardButton("📢 መልእክት ለሁሉም ላክ (Broadcast)", callback_data="broadcast")
        )
        bot.send_message(message.chat.id, "የአድሚን መቆጣጠሪያ፦", reply_markup=markup)

# --- Admin Callback Handlers ---
@bot.callback_query_handler(func=lambda call: True)
def admin_callback(call):
    if call.data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "ለተጠቃሚዎች እንዲደርስ የሚፈልጉትን መልእክት (ጽሁፍ፣ ፎቶ፣ ቪዲዮ ወይም ፋይል) ይላኩ...")
        bot.register_next_step_handler(msg, send_broadcast)

    elif call.data == "edit_content_select":
        markup = types.InlineKeyboardMarkup()
        for parent, subs in bot_data["sub_buttons"].items():
            for s in subs:
                markup.add(types.InlineKeyboardButton(f"{parent} -> {s}", callback_data=f"econt_{s}"))
        bot.edit_message_text("ይዘት መቀየር የሚፈልጉትን ይምረጡ፦", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("econt_"):
        btn_name = call.data.replace("econt_", "")
        msg = bot.send_message(call.message.chat.id, f"ለ '{btn_name}' አዲስ ይዘት (ጽሁፍ/ፎቶ/ቪዲዮ/ፋይል) ይላኩ...")
        bot.register_next_step_handler(msg, lambda m: update_content_final(m, btn_name))

    elif call.data == "rename_btn_select":
        markup = types.InlineKeyboardMarkup()
        for b in bot_data["main_buttons"]:
            markup.add(types.InlineKeyboardButton(f"✏️ ዋና: {b}", callback_data=f"ren_main_{b}"))
        for parent, subs in bot_data["sub_buttons"].items():
            for s in subs:
                markup.add(types.InlineKeyboardButton(f"✏️ ንዑስ: {s}", callback_data=f"ren_sub_{parent}_{s}"))
        bot.edit_message_text("ስሙ እንዲቀየር የሚፈልጉትን ባተን ይምረጡ፦", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("ren_main_"):
        old_name = call.data.replace("ren_main_", "")
        msg = bot.send_message(call.message.chat.id, f"የ '{old_name}' አዲስ ስም ይላኩ...")
        bot.register_next_step_handler(msg, lambda m: finish_rename_main(m, old_name))

    elif call.data.startswith("ren_sub_"):
        parts = call.data.split("_")
        # parts index check
        parent, old_name = parts[2], parts[3]
        msg = bot.send_message(call.message.chat.id, f"የንዑስ ባተን '{old_name}' አዲስ ስም ይላኩ...")
        bot.register_next_step_handler(msg, lambda m: finish_rename_sub(m, parent, old_name))

    elif call.data == "delete_btn":
        markup = types.InlineKeyboardMarkup()
        for b in bot_data["main_buttons"]:
            markup.add(types.InlineKeyboardButton(f"🗑 ዋና: {b}", callback_data=f"delmain_{b}"))
        for parent, subs in bot_data["sub_buttons"].items():
            for s in subs:
                markup.add(types.InlineKeyboardButton(f"🗑 ንዑስ: {s}", callback_data=f"delsub_{parent}_{s}"))
        bot.edit_message_text("ማጥፋት የሚፈልጉትን ይምረጡ፦", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("delmain_"):
        name = call.data.replace("delmain_", "")
        if name in bot_data["main_buttons"]: bot_data["main_buttons"].remove(name)
        if name in bot_data["sub_buttons"]: del bot_data["sub_buttons"][name]
        bot.send_message(call.message.chat.id, f"✅ '{name}' ተወግዷል!", reply_markup=build_main_menu(call.from_user.id))

    elif call.data.startswith("delsub_"):
        parts = call.data.split("_")
        parent, sub = parts[1], parts[2]
        if sub in bot_data["sub_buttons"].get(parent, []):
            bot_data["sub_buttons"][parent].remove(sub)
            bot.send_message(call.message.chat.id, f"✅ ንዑስ ባተን ተሰርዟል!")

    elif call.data == "add_main":
        msg = bot.send_message(call.message.chat.id, "የአዲሱን ዋና ባተን ስም ይላኩ...")
        bot.register_next_step_handler(msg, add_main_final)

    elif call.data == "add_sub_select":
        markup = types.InlineKeyboardMarkup()
        for b in bot_data["main_buttons"]:
            markup.add(types.InlineKeyboardButton(b, callback_data=f"asub_{b}"))
        bot.edit_message_text("ንዑስ ባተኑ የትኛው ስር ይሁን?", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("asub_"):
        parent = call.data.replace("asub_", "")
        msg = bot.send_message(call.message.chat.id, f"ለ '{parent}' ንዑስ ባተን ስም ይላኩ...")
        bot.register_next_step_handler(msg, lambda m: add_sub_final(m, parent))

# --- Broadcast Logic ---
def send_broadcast(message):
    count = 0
    for user_id in bot_data["users"]:
        try:
            if message.content_type == 'text':
                bot.send_message(user_id, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(user_id, message.video.file_id, caption=message.caption)
            elif message.content_type == 'document':
                bot.send_document(user_id, message.document.file_id, caption=message.caption)
            count += 1
        except Exception:
            pass
    bot.send_message(ADMIN_ID, f"✅ መልእክቱ ለ {count} ተጠቃሚዎች ደርሷል!")

# --- Helper Functions ---
def update_content_final(message, btn_name):
    # ሰነድን (document) ለመቀበል የተጨመረ logic
    if message.content_type == 'text':
        bot_data["contents"][btn_name] = {'type': 'text', 'value': message.text}
    elif message.content_type == 'photo':
        bot_data["contents"][btn_name] = {'type': 'photo', 'value': message.photo[-1].file_id, 'caption': message.caption}
    elif message.content_type == 'video':
        bot_data["contents"][btn_name] = {'type': 'video', 'value': message.video.file_id, 'caption': message.caption}
    elif message.content_type == 'document':
        bot_data["contents"][btn_name] = {'type': 'document', 'value': message.document.file_id, 'caption': message.caption}
    else:
        bot.send_message(message.chat.id, "❌ ያልተደገፈ የፋይል አይነት ነው። እባክዎ ጽሁፍ፣ ፎቶ፣ ቪዲዮ ወይም ፋይል ይላኩ።")
        return

    bot.send_message(message.chat.id, "✅ ይዘቱ ተዘምኗል!")

def finish_rename_main(message, old_name):
    new_name = message.text
    if old_name in bot_data["main_buttons"]:
        idx = bot_data["main_buttons"].index(old_name)
        bot_data["main_buttons"][idx] = new_name
        bot_data["sub_buttons"][new_name] = bot_data["sub_buttons"].pop(old_name)
        bot.send_message(message.chat.id, f"✅ ስሙ ተቀይሯል!", reply_markup=build_main_menu(message.from_user.id))

def finish_rename_sub(message, parent, old_name):
    new_name = message.text
    if parent in bot_data["sub_buttons"] and old_name in bot_data["sub_buttons"][parent]:
        idx = bot_data["sub_buttons"][parent].index(old_name)
        bot_data["sub_buttons"][parent][idx] = new_name
        if old_name in bot_data["contents"]:
            bot_data["contents"][new_name] = bot_data["contents"].pop(old_name)
        bot.send_message(message.chat.id, f"✅ ስሙ ተቀይሯል!")

def add_main_final(message):
    bot_data["main_buttons"].append(message.text)
    bot_data["sub_buttons"][message.text] = []
    bot.send_message(message.chat.id, "✅ ተሳክቷል!", reply_markup=build_main_menu(message.from_user.id))

def add_sub_final(message, parent):
    bot_data["sub_buttons"][parent].append(message.text)
    bot.send_message(message.chat.id, "✅ ንዑስ ባተን ተጨምሯል!")

bot.infinity_polling()
