from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services import MetaAPI, MetaAPIError
from utils import accounts_keyboard, objectives_keyboard, back_keyboard, confirm_keyboard, get_account, esc

router = Router()

OBJECTIVE_LABELS = {
    "OUTCOME_AWARENESS": "מודעות",
    "OUTCOME_TRAFFIC": "תנועה",
    "OUTCOME_ENGAGEMENT": "מעורבות",
    "OUTCOME_LEADS": "לידים",
    "OUTCOME_SALES": "מכירות",
    "OUTCOME_APP_PROMOTION": "אפליקציה",
}


class CreateCampaignState(StatesGroup):
    select_account = State()
    enter_name = State()
    select_objective = State()
    enter_budget = State()
    enter_start_date = State()
    enter_end_date = State()
    confirm = State()


@router.callback_query(F.data == "menu:create")
async def create_select_account(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCampaignState.select_account)
    await callback.message.edit_text(
        "➕ <b>יצירת קמפיין חדש</b>\n\nבחר חשבון:",
        parse_mode="HTML",
        reply_markup=accounts_keyboard("create:account")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("create:account:"))
async def create_enter_name(callback: CallbackQuery, state: FSMContext):
    account_key = callback.data.split(":")[2]
    acc = get_account(account_key)
    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await state.update_data(account_key=account_key)
    await state.set_state(CreateCampaignState.enter_name)

    await callback.message.edit_text(
        f"➕ <b>יצירת קמפיין — {esc(acc.name)}</b>\n\n"
        "✏️ שלח את <b>שם הקמפיין</b>:",
        parse_mode="HTML",
        reply_markup=back_keyboard("menu:create")
    )
    await callback.answer()


@router.message(CreateCampaignState.enter_name)
async def create_enter_name_received(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ שם הקמפיין חייב להכיל לפחות 2 תווים.")
        return
    if len(name) > 200:
        await message.answer("❌ שם הקמפיין ארוך מדי (מקסימום 200 תווים).")
        return

    await state.update_data(campaign_name=name)
    await state.set_state(CreateCampaignState.select_objective)

    await message.answer(
        f"✅ שם: <b>{esc(name)}</b>\n\n"
        "🎯 בחר <b>מטרת הקמפיין</b>:",
        parse_mode="HTML",
        reply_markup=objectives_keyboard()
    )


@router.callback_query(F.data.startswith("create:objective:"))
async def create_select_objective(callback: CallbackQuery, state: FSMContext):
    objective = callback.data.split(":")[2]
    await state.update_data(objective=objective)
    await state.set_state(CreateCampaignState.enter_budget)

    label = OBJECTIVE_LABELS.get(objective, objective)
    await callback.message.edit_text(
        f"✅ מטרה: <b>{esc(label)}</b>\n\n"
        "💰 שלח את <b>התקציב היומי בדולרים</b> (לדוגמה: <code>50</code>):\n\n"
        "⚠️ מינימום $1/יום",
        parse_mode="HTML",
        reply_markup=back_keyboard("menu:create")
    )
    await callback.answer()


@router.message(CreateCampaignState.enter_budget)
async def create_enter_budget_received(message: Message, state: FSMContext):
    text = message.text.strip().replace("$", "").replace("₪", "").replace(",", "")
    try:
        amount = float(text)
        if amount < 1:
            await message.answer("❌ התקציב חייב להיות לפחות $1/יום.")
            return
        if amount > 100000:
            await message.answer("❌ התקציב חייב להיות מתחת ל-$100,000/יום.")
            return
    except ValueError:
        await message.answer("❌ הזן מספר תקין (לדוגמה: <code>50</code>).", parse_mode="HTML")
        return

    await state.update_data(daily_budget=int(amount * 100))
    await state.set_state(CreateCampaignState.enter_start_date)

    await message.answer(
        f"✅ תקציב: <b>${amount:.2f}/יום</b>\n\n"
        "📅 שלח את <b>תאריך התחלה</b> (פורמט: <code>YYYY-MM-DD</code>)\n"
        "או שלח <code>היום</code> להתחלה מיידית:",
        parse_mode="HTML"
    )


@router.message(CreateCampaignState.enter_start_date)
async def create_enter_start_date(message: Message, state: FSMContext):
    from datetime import datetime, date
    text = message.text.strip()

    if text.lower() in ("היום", "today"):
        start = date.today().strftime("%Y-%m-%d")
    else:
        try:
            datetime.strptime(text, "%Y-%m-%d")
            start = text
        except ValueError:
            await message.answer("❌ פורמט לא תקין. שלח תאריך בפורמט <code>YYYY-MM-DD</code> או <code>היום</code>.", parse_mode="HTML")
            return

    await state.update_data(start_time=start)
    await state.set_state(CreateCampaignState.enter_end_date)

    await message.answer(
        f"✅ תאריך התחלה: <b>{esc(start)}</b>\n\n"
        "📅 שלח את <b>תאריך סיום</b> (פורמט: <code>YYYY-MM-DD</code>)\n"
        "או שלח <code>ללא</code> לקמפיין ללא תאריך סיום:",
        parse_mode="HTML"
    )


@router.message(CreateCampaignState.enter_end_date)
async def create_enter_end_date(message: Message, state: FSMContext):
    from datetime import datetime
    text = message.text.strip()

    if text.lower() in ("ללא", "none", "—", "-"):
        end = None
    else:
        try:
            datetime.strptime(text, "%Y-%m-%d")
            end = text
        except ValueError:
            await message.answer("❌ פורמט לא תקין. שלח תאריך <code>YYYY-MM-DD</code> או <code>ללא</code>.", parse_mode="HTML")
            return

    await state.update_data(end_time=end)
    await state.set_state(CreateCampaignState.confirm)

    data = await state.get_data()
    acc = get_account(data["account_key"])
    budget_display = data["daily_budget"] / 100
    objective_label = OBJECTIVE_LABELS.get(data["objective"], data["objective"])
    end_display = esc(end) if end else "ללא הגבלה"

    await message.answer(
        f"📋 <b>סיכום הקמפיין החדש:</b>\n\n"
        f"🏢 חשבון: <b>{esc(acc.name)}</b>\n"
        f"📝 שם: <b>{esc(data['campaign_name'])}</b>\n"
        f"🎯 מטרה: <b>{esc(objective_label)}</b>\n"
        f"💰 תקציב: <b>${budget_display:.2f}/יום</b>\n"
        f"📅 התחלה: <b>{esc(data['start_time'])}</b>\n"
        f"📅 סיום: <b>{end_display}</b>\n\n"
        "האם לאשר ולצור את הקמפיין?",
        parse_mode="HTML",
        reply_markup=confirm_keyboard("create:confirm", "create:cancel")
    )


@router.callback_query(F.data == "create:confirm")
async def create_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    acc = get_account(data["account_key"])

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text("⏳ <b>יוצר קמפיין...</b>", parse_mode="HTML")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        campaign_id = await api.create_campaign(
            name=data["campaign_name"],
            objective=data["objective"],
            daily_budget=data["daily_budget"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
        )
        await state.clear()

        await callback.message.edit_text(
            f"✅ <b>קמפיין נוצר בהצלחה!</b>\n\n"
            f"📝 שם: <b>{esc(data['campaign_name'])}</b>\n"
            f"🆔 ID: <code>{esc(campaign_id)}</code>",
            parse_mode="HTML",
            reply_markup=back_keyboard("menu:campaigns")
        )

    except MetaAPIError as e:
        await state.clear()
        await callback.message.edit_text(
            f"❌ <b>שגיאת API ביצירת קמפיין:</b>\n<code>{esc(e)}</code>",
            parse_mode="HTML",
            reply_markup=back_keyboard("menu:create")
        )
    await callback.answer()


@router.callback_query(F.data == "create:cancel")
async def create_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>יצירת הקמפיין בוטלה</b>",
        parse_mode="HTML",
        reply_markup=back_keyboard("menu:back")
    )
    await callback.answer("בוטל")
