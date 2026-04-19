from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services import MetaAPI, MetaAPIError
from utils import back_keyboard, confirm_keyboard, get_account

router = Router()


class BudgetState(StatesGroup):
    waiting_for_amount = State()
    confirming = State()


@router.callback_query(F.data.startswith("budget:campaign:"))
async def budget_campaign_start(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    account_key = parts[2]
    campaign_id = parts[3]

    await state.set_state(BudgetState.waiting_for_amount)
    await state.update_data(
        entity_type="campaign",
        entity_id=campaign_id,
        account_key=account_key
    )

    await callback.message.edit_text(
        "💰 *שינוי תקציב קמפיין*\n\n"
        "הזן תקציב יומי חדש בדולרים (לדוגמה: `50` = $50/יום)\n\n"
        "⚠️ הסכום המינימלי הוא $1/יום",
        parse_mode="Markdown",
        reply_markup=back_keyboard(f"campaign:view:{account_key}:{campaign_id}")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("budget:adset:"))
async def budget_adset_start(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    account_key = parts[2]
    adset_id = parts[3]

    await state.set_state(BudgetState.waiting_for_amount)
    await state.update_data(
        entity_type="adset",
        entity_id=adset_id,
        account_key=account_key
    )

    await callback.message.edit_text(
        "💰 *שינוי תקציב אדסט*\n\n"
        "הזן תקציב יומי חדש בדולרים (לדוגמה: `30` = $30/יום)\n\n"
        "⚠️ הסכום המינימלי הוא $1/יום",
        parse_mode="Markdown",
        reply_markup=back_keyboard("menu:adsets")
    )
    await callback.answer()


@router.message(BudgetState.waiting_for_amount)
async def budget_receive_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace("$", "").replace("₪", "").replace(",", "")

    try:
        amount = float(text)
        if amount < 1:
            await message.answer("❌ הסכום חייב להיות לפחות $1")
            return
        if amount > 100000:
            await message.answer("❌ הסכום חייב להיות מתחת ל-$100,000")
            return

        amount_cents = int(amount * 100)
        await state.update_data(amount=amount_cents, amount_display=amount)
        await state.set_state(BudgetState.confirming)

        data = await state.get_data()
        entity_type = "קמפיין" if data["entity_type"] == "campaign" else "אדסט"

        await message.answer(
            f"⚠️ *אישור שינוי תקציב*\n\n"
            f"תקציב יומי חדש ל{entity_type}: *${amount:.2f}*\n\n"
            f"האם לאשר?",
            parse_mode="Markdown",
            reply_markup=confirm_keyboard(
                "budget:confirm",
                "budget:cancel"
            )
        )

    except ValueError:
        await message.answer("❌ הזן מספר תקין (לדוגמה: `50` או `49.99`)")


@router.callback_query(F.data == "budget:confirm")
async def budget_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    account_key = data["account_key"]
    entity_type = data["entity_type"]
    entity_id = data["entity_id"]
    amount_cents = data["amount"]
    amount_display = data["amount_display"]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text("⏳ *מעדכן תקציב...*", parse_mode="Markdown")

    try:
        api = MetaAPI(acc.token, acc.account_id)

        if entity_type == "campaign":
            success = await api.update_campaign_budget(entity_id, amount_cents)
        else:
            success = await api.update_adset_budget(entity_id, amount_cents)

        await state.clear()

        if success:
            entity_label = "הקמפיין" if entity_type == "campaign" else "האדסט"
            await callback.message.edit_text(
                f"✅ *תקציב {entity_label} עודכן ל-${amount_display:.2f}/יום*",
                parse_mode="Markdown",
                reply_markup=back_keyboard("menu:campaigns")
            )
        else:
            await callback.message.edit_text(
                "❌ *עדכון התקציב נכשל*",
                parse_mode="Markdown",
                reply_markup=back_keyboard("menu:campaigns")
            )

    except MetaAPIError as e:
        await state.clear()
        await callback.message.edit_text(
            f"❌ *שגיאת API:*\n`{e}`",
            parse_mode="Markdown",
            reply_markup=back_keyboard("menu:campaigns")
        )
    await callback.answer()


@router.callback_query(F.data == "budget:cancel")
async def budget_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ *ביטול שינוי תקציב*",
        parse_mode="Markdown",
        reply_markup=back_keyboard("menu:campaigns")
    )
    await callback.answer("בוטל")
