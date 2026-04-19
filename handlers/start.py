from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from config import config
from utils import main_menu_keyboard

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_CHAT_ID


@router.message(Command("start"))
async def cmd_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ אין לך הרשאה להשתמש בבוט זה.")
        return

    await message.answer(
        "👋 *ברוך הבא למנהל המודעות!*\n\n"
        "🎯 אני עוזר לך לנהל ולנתח את קמפיינים שלך ב-Meta Ads.\n\n"
        "בחר פעולה:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("📋 *תפריט ראשי*", parse_mode="Markdown", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:back")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📋 *תפריט ראשי* — בחר פעולה:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def settings_menu(callback: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ שעת דוח יומי", callback_data="settings:report_hour")],
        [InlineKeyboardButton(text="🔙 חזרה", callback_data="menu:back")],
    ])
    await callback.message.edit_text(
        f"⚙️ *הגדרות*\n\n"
        f"⏰ דוח יומי שולח בשעה: *{config.REPORT_HOUR}:00*\n"
        f"👤 Chat ID: `{config.ADMIN_CHAT_ID}`",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()
