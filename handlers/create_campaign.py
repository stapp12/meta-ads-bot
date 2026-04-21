from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services import MetaAPI, MetaAPIError
from utils import esc, accounts_keyboard, objectives_keyboard, back_keyboard, get_account

router = Router()


class CreateCampaignState(StatesGroup):
    choosing_account = State()
    entering_name = State()
    choosing_objective = State()
    entering_budget = State()
    entering_start_date = State()
    entering_end_date = State()
    confirming = State()


@router.callback_query(F.data == "menu:create_campaign")
async def create_campaign_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCampaignState.choosing_account)
    await callback.message.edit_text(
        "➕ <b>יצירת קמפיין חדש</b>\n\nבחר חשבון פרסום:",
        parse_mode="HTML",
        reply_markup=accounts_keyboard("create:account")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("create:account:"))
async def create_campaign_account(callback: CallbackQuery, state: FSMContext):
    account_key = callback.data.split(":")[2]
    acc = get_account(account_key)
    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await state.update_data(account_key=account_key)
    await state.set_state(CreateCampaignState.entering_name)

    await callback.message.edit_text(
        f"➕ <b>יצירת קמפיין — {esc(acc.name)}</b>\n\n"
        "הזן <b>שם לקמפיין</b>:",
        parse_mode="HTML",
        reply_markup=back_keyboard("menu:create_campaign")
    )
    await callback.answer()


@router.message(CreateCampaignState.entering_name)
async def create_campaign_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("❌ שם הקמפיין לא יכול להיות ריק")
        return

    await state.update_data(name=name)
    await state.set_state(CreateCampaignState.choosing_objective)

    await message.answer(
        f"✅ שם: <b>{esc(name)}</b>\n\nבחר <b>מטרת הקמפיין</b>:",
        parse_mode="HTML",
        reply_markup=objectives_keyboard()
    )


@router.callback_query(F.data.startswith("create:objective:"))
async def create_campaign_objective(callback: CallbackQuery, state: FSMContext):
    objective = callback.data.split(":")[2]
    await state.update_data(objective=objective)
    await state.set_state(CreateCampaignState.entering_budget)

    await callback.message.edit_text(
        f"✅ מטרה: <b>{esc(objective)}</b>\n\n"
        "הזן <b>תקציב יומי</b> בשקלים (לדוגמה: <code>100</code> = ₪100/יום):",
        parse_mode="HTML",
        reply_markup=back_keyboard("menu:create_campaign")
    )
    await callback.answer()


@router.message(CreateCampaignState.entering_budget)
async def create_campaign_budget(message: Message, state: FSMContext):
    text = message.text.strip().replace("₪", "").replace("$", "").replace(",", "")
    try:
        amount = float(text)
        if amount < 1:
            await message.answer("❌ התקציב חייב להיות לפחות ₪1")
            return
    except ValueError:
        await message.answer("❌ הזן מספר תקין (לדוגמה: <code>100</code>)", parse_mode="HTML")
        return

    amount_cents = int(amount * 100)
    await state.update_data(daily_budget=amount_cents, budget_display=amount)
    await state.set_state(CreateCampaignState.entering_start_date)

    await message.answer(
        f"✅ תקציב: <b>₪{amount:.2f}/יום</b>\n\n"
        "הזן <b>תאריך התחלה</b> (פורמט: YYYY-MM-DD, לדוגמה: <code>2025-01-01</code>):",
        parse_mode="HTML"
    )


@router.message(CreateCampaignState.entering_start_date)
async def create_campaign_start_date(message: Message, state: FSMContext):
    date_str = message.text.strip()
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        await message.answer("❌ פורמט שגוי. הזן תאריך בפורמט: <code>YYYY-MM-DD</code>", parse_mode="HTML")
        return

    await state.update_data(start_date=date_str)
    await state.set_state(CreateCampaignState.entering_end_date)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏩ ללא תאריך סיום", callback_data="create:no_end_date")]
    ])

    await message.answer(
        f"✅ תאריך התחלה: <b>{esc(date_str)}</b>\n\n"
        "הזן <b>תאריך סיום</b> (פורמט: YYYY-MM-DD) או לחץ על 'ללא תאריך סיום':",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.callback_query(F.data == "create:no_end_date")
async def create_campaign_no_end_date(callback: CallbackQuery, state: FSMContext):
    await state.update_data(end_date=None)
    await state.set_state(CreateCampaignState.confirming)
    await _show_confirmation(callback.message, state)
    await callback.answer()


@router.message(CreateCampaignState.entering_end_date)
async def create_campaign_end_date(message: Message, state: FSMContext):
    date_str = message.text.strip()
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        await message.answer("❌ פורמט שגוי. הזן תאריך בפורמט: <code>YYYY-MM-DD</code>", parse_mode="HTML")
        return

    await state.update_data(end_date=date_str)
    await state.set_state(CreateCampaignState.confirming)
    await _show_confirmation(message, state)


async def _show_confirmation(message, state: FSMContext):
    data = await state.get_data()
    acc = get_account(data["account_key"])
    end_date_str = f"<b>{esc(data['end_date'])}</b>" if data.get("end_date") else "ללא הגבלה"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ צור קמפיין", callback_data="create:confirm"),
         InlineKeyboardButton(text="❌ ביטול", callback_data="menu:back")]
    ])

    await message.answer(
        f"📋 <b>אישור יצירת קמפיין</b>\n\n"
        f"🏢 חשבון: <b>{esc(acc.name)}</b>\n"
        f"📝 שם: <b>{esc(data['name'])}</b>\n"
        f"🎯 מטרה: <b>{esc(data['objective'])}</b>\n"
        f"💰 תקציב יומי: <b>₪{data['budget_display']:.2f}</b>\n"
        f"📅 התחלה: <b>{esc(data['start_date'])}</b>\n"
        f"📅 סיום: {end_date_str}\n\n"
        f"⚠️ הקמפיין ייווצר במצב <b>מושהה</b>",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.callback_query(F.data == "create:confirm")
async def create_campaign_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    acc = get_account(data["account_key"])

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text("⏳ יוצר קמפיין...", parse_mode="HTML")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        campaign_id = await api.create_campaign(
            name=data["name"],
            objective=data["objective"],
            daily_budget=data["daily_budget"],
            start_time=data["start_date"],
            end_time=data.get("end_date"),
        )
        await state.clear()

        await callback.message.edit_text(
            f"✅ <b>קמפיין נוצר בהצלחה!</b>\n\n"
            f"📝 שם: <b>{esc(data['name'])}</b>\n"
            f"🆔 ID: <code>{esc(campaign_id)}</code>\n\n"
            f"הקמפיין נמצא במצב מושהה — הפעל אותו דרך ניהול קמפיינים.",
            parse_mode="HTML",
            reply_markup=back_keyboard("menu:campaigns")
        )

    except MetaAPIError as e:
        await state.clear()
        await callback.message.edit_text(
            f"❌ <b>שגיאה ביצירת הקמפיין:</b>\n<code>{esc(str(e))}</code>",
            parse_mode="HTML",
            reply_markup=back_keyboard("menu:create_campaign")
        )
    await callback.answer()
