from aiogram import Router, F
from aiogram.types import CallbackQuery
from services import MetaAPI, MetaAPIError
from utils import esc, accounts_keyboard, report_period_keyboard, back_keyboard, format_currency, format_number, format_percent, get_account

router = Router()


@router.callback_query(F.data == "menu:report")
async def report_select_account(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 <b>דוח ביצועים</b>\n\nבחר חשבון:",
        parse_mode="HTML",
        reply_markup=accounts_keyboard("report:account")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("report:account:"))
async def report_select_period(callback: CallbackQuery):
    account_key = callback.data.split(":")[2]
    acc = get_account(account_key)
    if not acc:
        await callback.answer("❌ חשבון לא נמצא", show_alert=True)
        return

    await callback.message.edit_text(
        f"📊 <b>דוח — {esc(acc.name)}</b>\n\nבחר תקופה:",
        parse_mode="HTML",
        reply_markup=report_period_keyboard(account_key)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("report:period:"))
async def report_show(callback: CallbackQuery):
    parts = callback.data.split(":")
    account_key = parts[2]
    days = int(parts[3])
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר לחשבון זה", show_alert=True)
        return

    await callback.message.edit_text("⏳ טוען נתונים...", parse_mode="HTML")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        insights = await api.get_account_insights(days=days)
        account_info = await api.get_account_spend_limit()
        campaigns = await api.get_campaigns()

        active = sum(1 for c in campaigns if c.get("status") == "ACTIVE")
        paused = sum(1 for c in campaigns if c.get("status") == "PAUSED")

        period_label = {1: "היום", 7: "7 ימים", 30: "30 ימים"}.get(days, f"{days} ימים")
        currency = account_info.get("currency", "USD")

        spend = format_currency(insights.get("spend", "0"), currency)
        impressions = format_number(insights.get("impressions", "0"))
        clicks = format_number(insights.get("clicks", "0"))
        ctr = format_percent(insights.get("ctr", "0"))
        cpc = format_currency(insights.get("cpc", "0"), currency)
        reach = format_number(insights.get("reach", "0"))
        freq = f"{float(insights.get('frequency', 0)):.2f}" if insights.get("frequency") else "—"

        text = (
            f"📊 <b>דוח {esc(period_label)} — {esc(acc.name)}</b>\n\n"
            f"💰 <b>הוצאה:</b> {spend}\n"
            f"👁️ <b>חשיפות:</b> {impressions}\n"
            f"🖱️ <b>קליקים:</b> {clicks}\n"
            f"📈 <b>CTR:</b> {ctr}\n"
            f"💵 <b>CPC:</b> {cpc}\n"
            f"🎯 <b>טווח הגעה:</b> {reach}\n"
            f"🔁 <b>תדירות:</b> {freq}\n\n"
            f"🟢 קמפיינים פעילים: <b>{active}</b>\n"
            f"🔴 קמפיינים מושהים: <b>{paused}</b>"
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=report_period_keyboard(account_key)
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ <b>שגיאת API:</b>\n<code>{esc(str(e))}</code>",
            parse_mode="HTML",
            reply_markup=back_keyboard("menu:report")
        )
    await callback.answer()
