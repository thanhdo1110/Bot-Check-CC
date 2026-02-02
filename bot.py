"""
Telegram Bot CC Checker using aiogram.
High-performance bot for internal API testing.
Only requires BOT_TOKEN - no API_ID or API_HASH needed!

Copyright © CTDOTEAM - Đỗ Thành #1110
This bot is provided AS-IS without warranties.
Use only for authorized testing purposes.
The author is NOT responsible for misuse, legal consequences, or damages.
"""

import asyncio
import sys
import re
import logging
import time
import io
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, BufferedInputFile

from config import config, Config
from api_client import api_client, check_card_quick
from bin_lookup import format_bin_info
from database import db


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

logging.getLogger("aiogram").setLevel(logging.WARNING)

ADMIN_IDS = config.ADMIN_IDS

REQUIRED_CHANNEL_ID = -1003517529010

last_check_time = {}

MAINTENANCE_MODE = False

if not Config.validate():
    logger.error("Bot cannot start without proper configuration")
    logger.info("Please update your .env file with BOT_TOKEN")
    sys.exit(1)


bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()


def get_user_status_label(user_id):
    """Get status label for output."""
    if user_id in ADMIN_IDS:
        return "Admin"
    
    can_check, status = db.check_limit(user_id)
    if status == "premium":
        user_info = db.get_user(user_id)
        expiry = user_info[1].split()[0] if user_info and user_info[1] else "Unlimited"
        return f"💎 Premium (Exp: {expiry})"
    elif status == "vip":
        user_info = db.get_user(user_id)
        expiry = user_info[1].split()[0] if user_info and user_info[1] else "Unlimited"
        return f"⭐ VIP User (Exp: {expiry})"
    elif status == "public_free":
        return "Free User (Public)"
    else:
        return "Free User"


def can_user_check(user_id):
    """Check if user can check card (cooldown & daily limit)."""
    if user_id in ADMIN_IDS:
        return True, 0
        
    can_check, status = db.check_limit(user_id)
    
    if not can_check:
        if status == "inactive":
            return False, "inactive"
        return False, "Daily limit reached. Upgrade to get more checks!"
    
    # VIP and Premium have no cooldown
    # Only Free and Public Free have 30s cooldown
    if status in ["free", "public_free"]:
        last_time = last_check_time.get(user_id, 0)
        elapsed = time.time() - last_time
        if elapsed < 30:
            remaining = int(30 - elapsed)
            return False, f"Spam detected! Wait {remaining}s."
    
    return True, 0


def update_user_check(user_id):
    """Update user check usage."""
    if user_id not in ADMIN_IDS:
        db.increment_usage(user_id)
        last_check_time[user_id] = time.time()


async def check_channel_member(user_id: int) -> bool:
    """Check if user is member of required channel."""
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"Failed to check channel membership: {e}")
        return False


async def generate_invite_link(days: int = 1) -> str:
    """Generate single-use invite link for required channel."""
    try:
        expire_date = datetime.now() + timedelta(days=days)
        link = await bot.create_chat_invite_link(
            chat_id=REQUIRED_CHANNEL_ID,
            member_limit=1,
            expire_date=expire_date,
            name=f"Bot Invite - {datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        return link.invite_link
    except Exception as e:
        logger.error(f"Failed to create invite link: {e}")
        return None


async def ensure_channel_member(message: types.Message) -> bool:
    """Ensure user is channel member. Returns True if OK, False if need to join."""
    user_id = message.from_user.id
    
    if user_id in ADMIN_IDS:
        return True
    
    is_member = await check_channel_member(user_id)
    if is_member:
        return True
    
    invite_link = await generate_invite_link(days=1)
    
    if invite_link:
        await message.reply(
            "🔐 **Account Verification**\n\n"
            "You must join our internal channel to use this bot.\n\n"
            f"👉 [Click here to join the channel]({invite_link})\n\n"
            "⚠️ This link is single-use and expires in 24h.\n"
            "After joining, please try your command again.",
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            "🔐 **Verification Failed**\n\n"
            "Unable to create invite link. Please contact Admin."
        )
    
    return False

def parse_card_input(text: str) -> tuple:
    """Parse card input in various formats."""
    text = re.sub(r'^/[a-zA-Z0-9_]+\s*', '', text.strip(), flags=re.IGNORECASE)
    
    parts = text.split("|")
    
    if len(parts) == 4:
        card_number, month, year, cvv = [p.strip() for p in parts]
    elif len(parts) == 3:
        card_number = parts[0].strip()
        date_part = parts[1].strip()
        cvv = parts[2].strip()
        
        if "/" in date_part:
            month, year = date_part.split("/")
        else:
            return None
    else:
        return None
    
    card_number = re.sub(r'\D', '', card_number)
    month = re.sub(r'\D', '', month)
    year = re.sub(r'\D', '', year)
    cvv = re.sub(r'\D', '', cvv)
    
    if len(card_number) < 13 or len(card_number) > 19:
        return None
    if not month or int(month) < 1 or int(month) > 12:
        return None
    if len(year) == 2:
        year = "20" + year
    if len(year) != 4:
        return None
    if len(cvv) < 3 or len(cvv) > 4:
        return None
    
    return card_number, month, year, cvv


def format_result(result: dict, user_id: int, is_mass_mode: bool = False) -> str:
    """Format check result for Telegram message.
    
    Args:
        result: Check result dict
        user_id: User ID
        is_mass_mode: If True, skip BIN info for declined cards to save resources
    """
    status = result.get("status", "unknown")
    card = result.get("card_display", result.get("card", ""))
    message = result.get("message", "")
    time_taken = result.get("time_taken", 0)
    bin_info = result.get("bin_info", {})
    stripe_card = result.get("stripe_card_info", {})
    amount = result.get("amount", 100)
    is_auth_mode = result.get("is_auth_mode", False)
    
    if is_auth_mode:
        gateway = "Stripe Auth"
    else:
        gateway = f"Stripe ${amount/100}"
        
    if status == "charged":
        status_line = f"𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 ✅"
        hashtag = "#APPROVED"
    elif status == "approved":
        status_line = f"𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 [CCN] ✅"
        hashtag = "#CCN"
    elif status == "declined":
        status_line = f"𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗 ❌"
        hashtag = "#DECLINED"
    else:
        status_line = f"𝗘𝗥𝗥𝗢𝗥 ⚠️"
        hashtag = "#ERROR"
    
    lines = [
        f"{hashtag} {status_line}",
        f"𝗖𝗔𝗥𝗗: `{card}`",
    ]
    
    if message:
        lines.append(f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: {message}")
    
    cvc_check = stripe_card.get("cvc_check", "unknown")
    cvc_status = "pass" if cvc_check == "pass" else "fail" if cvc_check == "fail" else "unchecked"
    
    is_live = status in ["charged", "approved"]
    show_bin_info = bin_info and (is_live or not is_mass_mode)
    
    if show_bin_info:
        brand = bin_info.get("brand", "UNKNOWN")
        type_ = bin_info.get("type", "UNKNOWN")
        level = bin_info.get("level", "UNKNOWN")
        
        lines.append("")
        lines.append(f"𝗕𝗶𝗻 𝗜𝗻𝗳𝗼: {brand} - {type_} - {level}")
        
        bank = bin_info.get("bank", "UNKNOWN")
        lines.append(f"𝗕𝗮𝗻𝗸: {bank}")
        
        country_name = bin_info.get("country_name", "UNKNOWN")
        country_flag = bin_info.get("country_flag", "🏳️")
        lines.append(f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country_name} {country_flag}")
    
    lines.append("")
    lines.append(f"𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻: {time_taken} seconds")
    lines.append(f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: {gateway}")
    
    # User Status Footer
    user_status = get_user_status_label(user_id)
    lines.append(f"👤 **User**: {user_status}")
    
    return "\n".join(lines)


def format_declined(result: dict, user_id: int, is_mass_mode: bool = False) -> str:
    """Format declined card result.
    
    Args:
        result: Check result dict
        user_id: User ID
        is_mass_mode: If True, skip BIN info to save resources
    """
    card = result.get("card_display", result.get("card", ""))
    message = result.get("message", "Card declined")
    time_taken = result.get("time_taken", 0)
    bin_info = result.get("bin_info", {})
    decline_code = result.get("decline_code", "")
    amount = result.get("amount", 100)
    is_auth_mode = result.get("is_auth_mode", False)
    
    if is_auth_mode:
        gateway = "Stripe Auth"
    else:
        gateway = f"Stripe ${amount/100}"
    
    lines = [
        f"#DECLINED 𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗 ❌",
        f"𝗖𝗔𝗥𝗗: `{card}`",
        f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: {message}",
    ]
    
    if decline_code:
        lines.append(f"𝗖𝗼𝗱𝗲: {decline_code}")
    
    # Only show BIN info if NOT in mass mode (to save resources)
    if bin_info and not is_mass_mode:
        brand = bin_info.get("brand", "UNKNOWN")
        type_ = bin_info.get("type", "UNKNOWN")
        level = bin_info.get("level", "UNKNOWN")
        
        lines.append("")
        lines.append(f"𝗕𝗶𝗻 𝗜𝗻𝗳𝗼: {brand} - {type_} - {level}")
        
        bank = bin_info.get("bank", "UNKNOWN")
        lines.append(f"𝗕𝗮𝗻𝗸: {bank}")
        
        country_name = bin_info.get("country_name", "UNKNOWN")
        country_flag = bin_info.get("country_flag", "🏳️")
        lines.append(f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country_name} {country_flag}")
    
    lines.append("")
    lines.append(f"𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻: {time_taken} seconds")
    lines.append(f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: {gateway}")
    
    # User Status Footer
    user_status = get_user_status_label(user_id)
    lines.append(f"👤 **User**: {user_status}")
    
    return "\n".join(lines)


@dp.message(Command("add"))
async def add_free_handler(message: types.Message):
    """Handle /add command (Admin only) - Activate Free Plan."""
    if message.from_user.id not in ADMIN_IDS:
        return
        
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: `/add <user_id>`\nExample: `/add 123456789`")
        return
        
    try:
        user_id = int(args[1])
        db.activate_user(user_id)
        await message.reply(f"✅ User `{user_id}` activated on Free Plan (50 requests/day).")
        
    except ValueError:
        await message.reply("❌ Invalid format")


@dp.message(Command("addvip"))
async def addvip_handler(message: types.Message):
    """Handle /addvip command (Admin only)."""
    if message.from_user.id not in ADMIN_IDS:
        return
        
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: `/addvip <user_id> <days>`\nExample: `/addvip 123456789 30`")
        return
        
    try:
        user_id = int(args[1])
        days_str = args[2].lower().replace("d", "")
        days = int(days_str)
        
        expiry = db.set_vip(user_id, days)
        await message.reply(f"✅ User `{user_id}` upgraded to VIP until {expiry}")
        
    except ValueError:
        await message.reply("❌ Invalid format")


@dp.message(Command("addpre"))
async def addpre_handler(message: types.Message):
    """Handle /addpre command (Admin only) - Add Premium user."""
    if message.from_user.id not in ADMIN_IDS:
        return
        
    args = message.text.split()
    if len(args) < 3:
        await message.reply(
            "💎 **Add Premium User**\n\n"
            "Usage: `/addpre <user_id> <days>`\n"
            "Example: `/addpre 123456789 30`\n\n"
            "📊 Premium: 2000 checks/day, no delay"
        )
        return
        
    try:
        user_id = int(args[1])
        days_str = args[2].lower().replace("d", "")
        days = int(days_str)
        
        expiry = db.set_premium(user_id, days)
        await message.reply(
            f"💎 User `{user_id}` upgraded to **Premium** until {expiry}\n"
            f"• 2000 checks/day\n"
            f"• No cooldown"
        )
        
    except ValueError:
        await message.reply("❌ Invalid format")



@dp.message(Command("public"))
async def public_handler(message: types.Message):
    """Handle /public command (Admin only) - Toggle public mode."""
    if message.from_user.id not in ADMIN_IDS:
        return
        
    args = message.text.split()
    
    if len(args) < 2:
        # Show current status
        current = db.get_public_mode()
        status = "🟢 ON" if current else "🔴 OFF"
        await message.reply(
            f"📢 **Public Mode:** {status}\n\n"
            f"Usage:\n"
            f"• `/public on` - Allow everyone to use bot\n"
            f"• `/public off` - Only added users can use bot"
        )
        return
    
    action = args[1].lower()
    
    if action == "on":
        db.set_public_mode(True)
        await message.reply(
            "🟢 **Public Mode: ON**\n\n"
            "✅ Everyone can use the bot as Free User\n"
            "• VIP/Premium/Admin keep their privileges\n"
            "• Free User: 50 checks/day, 30s delay"
        )
    elif action == "off":
        db.set_public_mode(False)
        await message.reply(
            "🔴 **Public Mode: OFF**\n\n"
            "⛔ Only users added via /add or /addvip can use the bot"
        )
    else:
        await message.reply("❌ Usage: `/public on` or `/public off`")


@dp.message(Command("noti"))
async def noti_handler(message: types.Message):
    """Handle /noti command (Admin only) - Send notification to all users."""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    notification_text = None
    
    # Check if replying to a message
    if message.reply_to_message:
        # Get text from replied message
        replied = message.reply_to_message
        if replied.text:
            notification_text = replied.text
        elif replied.caption:
            notification_text = replied.caption
    else:
        # Get text after /noti command
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            notification_text = args[1]
    
    if not notification_text:
        await message.reply(
            "📢 **Send Notification**\n\n"
            "Usage:\n"
            "• `/noti <message>` - Send a message\n"
            "• Reply to a message + `/noti` - Forward that message\n\n"
            "Supports: Bold, Italic, Code, Links..."
        )
        return
    
    # Get all user IDs
    user_ids = db.get_all_user_ids()
    
    if not user_ids:
        await message.reply("⚠️ No users in database.")
        return
    
    status_msg = await message.reply(f"📤 Sending notification to {len(user_ids)} users...")
    
    success = 0
    failed = 0
    
    for user_id in user_ids:
        try:
            await bot.send_message(
                user_id, 
                f"📢 **ANNOUNCEMENT**\n\n{notification_text}",
                parse_mode=ParseMode.MARKDOWN
            )
            success += 1
        except Exception as e:
            failed += 1
            logger.debug(f"Failed to send to {user_id}: {e}")
        
        # Small delay to avoid rate limiting
        if success % 20 == 0:
            await asyncio.sleep(1)
    
    await status_msg.edit_text(
        f"✅ **Notification Sent**\n\n"
        f"📤 Success: {success}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {len(user_ids)}"
    )


@dp.message(Command("bot"))
async def bot_toggle_handler(message: types.Message):
    """Handle /bot on|off command (Admin only) - Toggle maintenance mode."""
    global MAINTENANCE_MODE
    
    if message.from_user.id not in ADMIN_IDS:
        return
    
    args = message.text.split()
    
    if len(args) < 2:
        status = "🔴 OFF (Maintenance)" if MAINTENANCE_MODE else "🟢 ON (Running)"
        await message.reply(
            f"🤖 **Bot Status:** {status}\n\n"
            f"Usage:\n"
            f"• `/bot on` - Enable bot for all users\n"
            f"• `/bot off` - Maintenance mode (Admins only)"
        )
        return
    
    action = args[1].lower()
    
    if action == "on":
        MAINTENANCE_MODE = False
        await message.reply(
            "🟢 **Bot Status: ONLINE**\n\n"
            "✅ All users can now use the bot."
        )
    elif action == "off":
        MAINTENANCE_MODE = True
        await message.reply(
            "🔴 **Bot Status: MAINTENANCE**\n\n"
            "⚠️ Only Admins can use the bot now.\n"
            "Other users will see maintenance message."
        )
    else:
        await message.reply("❌ Usage: `/bot on` or `/bot off`")


async def execute_check(message: types.Message, mode: str):
    """Common logic for executing a check command."""
    user_id = message.from_user.id
    
    # Check maintenance mode
    if MAINTENANCE_MODE and user_id not in ADMIN_IDS:
        await message.reply(
            "🔧 **Bot is under maintenance**\n\n"
            "Please try again later. We apologize for the inconvenience."
        )
        return
    
    # Check channel membership first
    if not await ensure_channel_member(message):
        return
    
    user_id = message.from_user.id
    can, msg = can_user_check(user_id)
    if not can:
        if msg == "inactive":
            await message.reply("⛔ **Account Inactive**\nContact Admin to activate checking.")
        else:
            sent = await message.reply(f"⚠️ {msg}")
            await asyncio.sleep(2)
            try:
                await sent.delete()
            except:
                pass
        return

    text = message.text or ""
    parsed = parse_card_input(text)
    
    if not parsed:
        await message.reply(
            "❌ **Invalid format!**\n\n"
            "📝 Use: `/cmd card|month|year|cvv`"
        )
        return
    
    update_user_check(user_id)
    
    card_number, month, year, cvv = parsed
    logger.info(f"Check ({mode}) {card_number[:6]}... | User: {user_id}")
    
    processing_msg = await message.reply(
        f"⏳ **Checking ({mode})...**\n"
        f"💳 `{card_number[:6]}xxxxxx{card_number[-4:]}`"
    )
    
    try:
        card_data = f"{card_number}|{month}|{year}|{cvv}"
        result = await check_card_quick(card_data, subscribe=True, mode=mode)
        
        if result.get("status") == "declined":
            response = format_declined(result, user_id)
        else:
            response = format_result(result, user_id)
            
            # Forward to Channel if approved
            try:
                await bot.send_message(FORWARD_CHANNEL, response)
            except Exception as e:
                logger.error(f"Failed to forward to channel: {e}")
            
        await processing_msg.edit_text(response)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing_msg.edit_text(f"🔴 **Error:** `{str(e)}`")


@dp.message(Command("start", "help"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    status = get_user_status_label(user_id)
    public_mode = "🟢 ON" if db.get_public_mode() else "🔴 OFF"
    
    welcome = f"""
🤖 **CC CHECKER BOT (PRO)**
━━━━━━━━━━━━━━━━━━━━
👤 **Your Status**: {status}
📢 **Public Mode**: {public_mode}

🔧 **Commands:**
• `/cc` - Charge $1
• `/cc5` - Charge $5
• `/auth` - Auth $1
• `/auth5` - Auth $5

📚 **Mass Check:**
• `/mass` - Mass Charge $1
• `/mass5` - Mass Charge $5
• `/mass_auth` - Mass Auth $1
• `/mass_auth5` - Mass Auth $5

📝 **Limits:**
- Free: 50 check/day, 30s delay
- ⭐ VIP: 200 check/day, no delay
- 💎 Premium: 2000 check/day, no delay

━━━━━━━━━━━━━━━━━━━━
🔐 Checker Bot Api...
    """
    
    # Add admin commands if user is admin
    if user_id in ADMIN_IDS:
        admin_cmds = """
🛠 **Admin Commands:**
• `/add <user_id>` - Activate Free User
• `/addvip <user_id> <days>` - Add VIP (200/day)
• `/addpre <user_id> <days>` - Add Premium (2000/day)
• `/public on/off` - Toggle public mode
• `/noti <message>` - Send notification to all users
• `/bot on/off` - Toggle maintenance mode
"""
        welcome += admin_cmds
    
    await message.reply(welcome)


# Register handlers
@dp.message(Command("cc"))
async def cmd_cc(msg: types.Message): await execute_check(msg, "default")

@dp.message(Command("cc5"))
async def cmd_cc5(msg: types.Message): await execute_check(msg, "5")

@dp.message(Command("auth"))
async def cmd_auth(msg: types.Message): await execute_check(msg, "auth")

@dp.message(Command("auth5"))
async def cmd_auth5(msg: types.Message): await execute_check(msg, "auth5")


# Forward Channel ID
FORWARD_CHANNEL = -1003454405312

async def execute_mass_check(message: types.Message, mode: str):
    """Common logic for mass check. Supports text input or .txt file reply."""
    user_id = message.from_user.id
    
    # Check maintenance mode
    if MAINTENANCE_MODE and user_id not in ADMIN_IDS:
        await message.reply(
            "🔧 **Bot is under maintenance**\n\n"
            "Please try again later. We apologize for the inconvenience."
        )
        return
    
    # Check channel membership first
    if not await ensure_channel_member(message):
        return
    
    can, msg = can_user_check(user_id)
    if not can:
        if msg == "inactive":
            await message.reply("⛔ **Account Inactive**\nContact Admin to activate checking.")
        else:
            await message.reply(f"⚠️ {msg}")
        return

    lines = []
    
    # Check if replying to a document (file)
    if message.reply_to_message and message.reply_to_message.document:
        doc = message.reply_to_message.document
        
        # Check if it's a .txt file
        if doc.file_name and doc.file_name.lower().endswith('.txt'):
            try:
                # Download file
                file = await bot.get_file(doc.file_id)
                file_data = await bot.download_file(file.file_path)
                
                # Read content
                content = file_data.read().decode('utf-8', errors='ignore')
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                
            except Exception as e:
                logger.error(f"Failed to read file: {e}")
                await message.reply("❌ **Failed to read file**\nPlease check your file format.")
                return
        else:
            await message.reply("❌ **Invalid file type**\nPlease reply to a `.txt` file.")
            return
    else:
        # Read from message text
        text = message.text or ""
        text = re.sub(r'^/[a-zA-Z0-9_]+\s*', '', text.strip())
        lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        await message.reply(
            "❌ **Invalid Input**\n\n"
            "📝 Usage:\n"
            "• `/mass card1|mm|yy|cvv`\n"
            "• Reply to a `.txt` file with `/mass`"
        )
        return
    
    total_in_file = len(lines)
    
    # Get remaining limit for user
    is_admin = user_id in ADMIN_IDS
    remaining, daily_limit, status = db.get_remaining_limit(user_id, is_admin)
    
    if remaining <= 0 and not is_admin:
        await message.reply("❌ **Daily limit reached!**\nUpgrade to VIP/Premium for more checks.")
        return
    
    # Limit cards to check based on remaining quota
    if not is_admin and total_in_file > remaining:
        lines = lines[:remaining]
        total = remaining
        limit_note = f"\n⚠️ Only checking {remaining}/{total_in_file} cards (limit reached)"
    else:
        total = total_in_file
        limit_note = ""

    start_time = time.time()
    status_msg = await message.reply(f"🔄 **Mass Check ({mode}) Started**\n📊 Total: {total}{limit_note}")
    
    approved = 0
    declined = 0
    live_cards = []  # Collect live cards
    
    for i, line in enumerate(lines, 1):
        parsed = parse_card_input(line)
        if not parsed:
            continue
            
        update_user_check(user_id)
        
        card_num, m, y, c = parsed
        card_data = f"{card_num}|{m}|{y}|{c}"
        
        try:
            res = await check_card_quick(card_data, subscribe=True, mode=mode)
            if res["status"] in ["charged", "approved"]:
                approved += 1
                live_cards.append(card_data)  # Save live card
                result_text = format_result(res, user_id, is_mass_mode=True)
                await message.reply(result_text)
                
                # Forward to Channel
                try:
                    await bot.send_message(FORWARD_CHANNEL, result_text)
                except Exception as e:
                    logger.error(f"Failed to forward to channel: {e}")
            else:
                declined += 1
        except:
            declined += 1
            
        if i % 5 == 0 or i == total:
            elapsed = round(time.time() - start_time, 1)
            try:
                await status_msg.edit_text(
                    f"🔄 **Mass Check ({mode})**\n"
                    f"📊 Total: {total}\n"
                    f"⏳ Progress: {i}/{total}\n"
                    f"✅ Live: {approved} | ❌ Die: {declined}\n"
                    f"⏱️ Time: {elapsed}s"
                )
            except: pass
    
    # Calculate total time
    total_time = round(time.time() - start_time, 1)
    avg_time = round(total_time / total, 2) if total > 0 else 0
    
    await status_msg.edit_text(
        f"✅ **Completed ({mode})**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Total Cards:** {total}\n"
        f"✅ **Live:** {approved}\n"
        f"❌ **Dead:** {declined}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ **Total Time:** {total_time}s\n"
        f"⚡ **Avg/Card:** {avg_time}s{limit_note}"
    )
    
    # Send live.txt file if there are live cards
    if live_cards:
        file_content = "\n".join(live_cards)
        file_bytes = file_content.encode('utf-8')
        input_file = BufferedInputFile(file_bytes, filename="live.txt")
        
        await message.reply_document(
            document=input_file,
            caption=f"✅ **Live Cards ({len(live_cards)})**\nMode: {mode} | Time: {total_time}s"
        )

@dp.message(Command("mass"))
async def cmd_mass(msg: types.Message): await execute_mass_check(msg, "default")

@dp.message(Command("mass5"))
async def cmd_mass5(msg: types.Message): await execute_mass_check(msg, "5")

@dp.message(Command("mass_auth"))
async def cmd_mass_auth(msg: types.Message): await execute_mass_check(msg, "auth")

@dp.message(Command("mass_auth5"))
async def cmd_mass_auth5(msg: types.Message): await execute_mass_check(msg, "auth5")


async def main():
    logger.info("CC Checker Bot starting...")
    logger.info(f"Loaded Admin IDs: {config.ADMIN_IDS}")
    try:
        await dp.start_polling(bot)
    finally:
        await api_client.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
