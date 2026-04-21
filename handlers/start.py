from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from config import config
from utils import main_menu_keyboard, esc

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_CHAT_ID


@router.message(Command("start"))
async def cmd_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ אין לך הרשאה להשתמש בבוט זה.")
        return

    await message.answer(
        "👋 <b>ברוך הבא למנהל המודעות!</b>\n\n"
        "🎯 אני עוזר לך לנהל ולנתח את קמפיינים שלך ב-Meta Ads.\n\n"
        "בחר פעולה:",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("📋 <b>תפריט ראשי</b>", parse_mode="HTML", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:back")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📋 <b>תפריט ראשי</b> — בחר פעולה:",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def settings_menu(callback: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 חזרה", callback_data="menu:back")],
    ])
    await callback.message.edit_text(
        f"⚙️ <b>הגדרות</b>\n\n"
        f"⏰ דוח יומי שולח בשעה: <b>{config.REPORT_HOUR}:00</b>\n"
        f"👤 Chat ID: <code>{config.ADMIN_CHAT_ID}</code>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()
