import os
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8711960321:AAGSUD1TBBMobGodkcueusHnh3Wm9w5ke-M"
bot = telebot.TeleBot(BOT_TOKEN)

# ⚠️ ضع هنا رقم الـ ID الخاص بحسابك الشخصي الذي استخرجته من userinfobot
ADMIN_CHAT_ID = "ضع_رقم_حسابك_هنا" 

# رقم سيريتل كاش الخاص بك تم حفظه هنا برمجياً
CASH_NUMBER = "0994511020"

app = Flask('')

@app.route('/')
def home():
    return "بوت شحن الألعاب وسيريتل كاش يعمل بنجاح!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

pending_orders = {}

# 1. قائمة الألعاب للمستخدم
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    pending_orders[chat_id] = {}
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("ببجي موبايل (PUBG)", callback_data="usergame_pubg"),
        InlineKeyboardButton("فري فاير (Free Fire)", callback_data="usergame_ff"),
        InlineKeyboardButton("لودو (Ludo)", callback_data="usergame_ludo")
    )
    bot.send_message(chat_id, "🎮 أهلاً بك في بوت الشحن السريع.\nالرجاء اختيار اللعبة المطلوبة لشحنها:", reply_markup=markup)

# 2. حفظ اللعبة وطلب الآيدي أو رقم اللاعب
@bot.callback_query_handler(func=lambda call: call.data.startswith("usergame_"))
def callback_game(call):
    chat_id = call.message.chat.id
    game_selected = call.data.split("_")[1]
    
    pending_orders[chat_id]['game'] = game_selected
    
    bot.delete_message(chat_id, call.message.message_id)
    msg = bot.send_message(chat_id, "📱 يرجى كتابة (معرف اللاعب / Player ID) أو رقم الشحن داخل اللعبة:")
    bot.register_next_step_handler(msg, process_phone_step)

# 3. حفظ آيدي الزبون وطلب الكمية
def process_phone_step(message):
    chat_id = message.chat.id
    phone = message.text
    
    if chat_id not in pending_orders:
        pending_orders[chat_id] = {}
        
    pending_orders[chat_id]['phone'] = phone
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("الكمية الصغرى", callback_data="amt_small"),
        InlineKeyboardButton("الكمية المتوسطة", callback_data="amt_medium"),
        InlineKeyboardButton("الكمية الكبرى", callback_data="amt_large")
    )
    bot.send_message(chat_id, "💎 اختر كمية الشحن أو الجواهر المطلوبة:", reply_markup=markup)

# 4. إرسال الطلب للأدمن للموافقة
@bot.callback_query_handler(func=lambda call: call.data.startswith("amt_"))
def callback_amount(call):
    chat_id = call.message.chat.id
    amount_selected = call.data.split("_")[1]
    
    game = pending_orders.get(chat_id, {}).get('game', 'غير معروف')
    phone = pending_orders.get(chat_id, {}).get('phone', 'غير معروف')
    pending_orders[chat_id]['amount'] = amount_selected
    
    bot.delete_message(chat_id, call.message.message_id)
    bot.send_message(chat_id, "⏳ تم إرسال طلبك للإدارة، يرجى الانتظار لتلقي بيانات الدفع وتأكيد الشحن...")
    
    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(
        InlineKeyboardButton("✅ موافقة وإرسال رقم الكاش", callback_data=f"adm_accept_{chat_id}"),
        InlineKeyboardButton("❌ رفض الطلب", callback_data=f"adm_reject_{chat_id}")
    )
    
    admin_msg = (
        "🚨 **طلب شحن جديد وصلك الآن!**\n\n"
        f"👤 حساب المشتري: {chat_id}\n"
        f"🎮 اللعبة المطلوبة: {game.upper()}\n"
        f"📱 آيدي/رقم الزبون: `{phone}`\n"
        f"📦 الكمية: {amount_selected.upper()}\n\n"
        "هل تريد قبول الطلب وإرسال رقم سيريتل كاش للزبون؟"
    )
    bot.send_message(int(ADMIN_CHAT_ID), admin_msg, reply_markup=admin_markup, parse_mode="Markdown")

# 5. معالجة قرار الأدمن وإرسال رقم الكاش تلقائياً للزبون
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def callback_admin_decision(call):
    data_parts = call.data.split("_")
    action = data_parts[1]        
    user_chat_id = int(data_parts[2])  
    
    bot.delete_message(int(ADMIN_CHAT_ID), call.message.message_id)
    
    if action == "accept":
        bot.send_message(int(ADMIN_CHAT_ID), f"✅ وافقت على الطلب. تم إرسال رقم سيريتل كاش للحساب {user_chat_id} بانتظار تحويله الأموال لتشحن له.")
        
        # الرسالة التي تظهر للزبون وبها رقم سيريتل كاش الخاص بك
        user_msg = (
            "🎉 **تمت الموافقة المبدئية على طلبك!**\n\n"
            f"📌 لإتمام الشحن، يرجى تحويل قيمة الطلب إلى حساب **سيريتل كاش** التالي:\n"
            f"📱 الرقم: `{CASH_NUMBER}`\n\n"
            "بعد تحويل المبلغ، سيتم تثبيت وإرسال الجواهر/الشدات إلى حسابك فوراً!"
        )
        bot.send_message(user_chat_id, user_msg, parse_mode="Markdown")
    elif action == "reject":
        bot.send_message(int(ADMIN_CHAT_ID), f"❌ رفضت طلب الحساب {user_chat_id}.")
        bot.send_message(user_chat_id, "⚠️ نعتذر منك، تم رفض طلب الشحن من قبل الإدارة. يرجى مراجعة الدعم.")

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    print("البوت نصف الآلي جاهز تماماً للتشغيل...")
    bot.infinity_polling()
