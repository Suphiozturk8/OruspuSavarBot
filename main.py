
from re import match
from emoji import is_emoji

from pyrogram import Client, filters, enums
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from configparser import ConfigParser


config = ConfigParser()
config.read("config.ini")


app = Client(
    "my_bot",
    api_id=config["bot"]["api_id"],
    api_hash=config["bot"]["api_hash"],
    bot_token=config["bot"]["bot_token"]
)


def tr_to_en(text):
   tr_chars = {
       "ı": "i", "İ": "I",
       "ğ": "g", "Ğ": "G",
       "ü": "u", "Ü": "U",
       "ş": "s", "Ş": "S",
       "ö": "o", "Ö": "O",
       "ç": "c", "Ç": "C",
       "â": "a", "Â": "A",
       "î": "i", "Î": "I",
       "û": "u", "Û": "U"
   }
   for tr_char, en_char in tr_chars.items():
       text = text.replace(tr_char, en_char)
   return text


def check_username_pattern(username, full_name):
    pattern = r"^[A-Za-z]+_[A-Za-z0-9]+$"
    if not match(pattern, username):
        return False
    
    username_prefix = username.lower().split("_")[0]
    first_name = full_name.lower().split()[0]
    
    return tr_to_en(first_name) == username_prefix


def check_double_emoji_at_end(name):
    if len(name) >= 2:
        chars = list(name)
        if len(chars) >= 2:
            last_two = chars[-2:]
            if (is_emoji(last_two[0]) and 
                is_emoji(last_two[1]) and 
                last_two[0] == last_two[1]):
                return True
    return False


async def check_admin_rights(chat_id, user_id):
    member = await app.get_chat_member(chat_id, user_id)
    if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        if member.privileges.can_restrict_members:
            return True
    return False


@app.on_chat_member_updated()
async def ban_suspicious_users(client, chat_member):
    if chat_member.new_chat_member and not chat_member.old_chat_member:
        user = chat_member.new_chat_member.user
        username = user.username
        full_name = user.full_name
        
        if username and check_username_pattern(username, full_name): # and check_double_emoji_at_end(full_name):
            try:
                await client.ban_chat_member(
                    chat_id=chat_member.chat.id,
                    user_id=user.id
                )
                
                unban_button = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "Banı Kaldır",
                        callback_data=f"unban_{user.id}"
                    )]
                ])
                
                ban_message = f"""
    **Şüpheli Kullanıcı Banlandı**
    **Kullanıcı:** @{username}
    **İsim:** {full_name}
    **ID:** `{user.id}`
    """
                await client.send_message(
                    chat_member.chat.id,
                    ban_message,
                    reply_markup=unban_button
                )
                
            except Exception as e:
                print(f"Banlama hatası: {e}")


@app.on_callback_query(filters.regex(r"unban_"))
async def handle_unban(client, callback_query):
    try:
        user_id = int(callback_query.data.split("_")[1])
        chat_id = callback_query.message.chat.id
        
        has_rights = await check_admin_rights(chat_id, callback_query.from_user.id)
        
        if has_rights:
            await client.unban_chat_member(chat_id, user_id)
            unban_message = f"""
**Ban Kaldırıldı**
**Kullanıcı ID:** `{user_id}`
**İşlemi Yapan Admin:** {callback_query.from_user.mention}
"""
            await callback_query.message.edit_text(unban_message)
            await callback_query.answer("Kullanıcının banı kaldırıldı!")
        else:
            await callback_query.answer(
                "Bu işlem için admin olmanız ve üyeleri banlama/banını kaldırma yetkinizin olması gerekiyor!",
                show_alert=True
            )
            
    except Exception as e:
        await callback_query.answer(f"Hata oluştu: {str(e)}", show_alert=True)


def get_start_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "Botu Grubuna Ekle",
            url=f"https://t.me/{app.me.username}?startgroup=true"
        )]
    ])


@app.on_message(filters.command("start"))
async def start_command(client, message):
    if message.chat.type == ChatType.PRIVATE:
        start_text = f"""
Merhaba {message.from_user.mention}!

 Ben o*uspu hesapları tespit edip engellemek için geliştirilmiş bir güvenlik botuyum.

Özelliklerim:
- O*uspu kullanıcı adı formatına sahip hesapları tespit ederim
- O*uspu hesapları otomatik olarak banlarım
- Adminlere ban kaldırma olanağı veririm

Grubunuzu o*uspulardan uzak tutmak için beni grubunuza ekleyebilir ve admin yapabilirsiniz!

Not: Grubunuzda düzgün çalışabilmem için bana şu yetkileri vermeyi unutmayın:
- Üye Engelleme
- Mesaj Silme
- Mesaj Sabitleme
"""
        await message.reply_text(
            start_text,
            reply_markup=get_start_button()
        )
    else:
        group_text = f"""
Bot zaten bu grupta aktif durumda!

Düzgün çalışabilmem için lütfen admin yetkilerimi kontrol edin.
"""
        await message.reply_text(group_text)


app.run()
