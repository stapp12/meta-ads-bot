from aiogram import Router, F
from aiogram.types import CallbackQuery
from services import MetaAPI, MetaAPIError
from utils import accounts_keyboard, report_period_keyboard, back_keyboard, format_currency, format_number, format_percent, get_account

router = Router()


@router.callback_query(F.data == "menu:report")
async def report_select_account(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 *דוח ביצועים*\n\nבחר חשבון:",
        parse_mode="Markdown",
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
        f"📊 *דוח — {acc.name}*\n\nבחר תקופה:",
        parse_mode="Markdown",
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

    await callback.message.edit_text("⏳ *טוען נתונים...*", parse_mode="Markdown")

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
            f"📊 *דוח {period_label} — {acc.name}*\n\n"
            f"💰 *הוצאה:* {spend}\n"
            f"👁️ *חשיפות:* {impressions}\n"
            f"🖱️ *קליקים:* {clicks}\n"
            f"📈 *CTR:* {ctr}\n"
            f"💵 *CPC:* {cpc}\n"
            f"🎯 *טווח הגעה:* {reach}\n"
            f"🔁 *תדירות:* {freq}\n\n"
            f"🟢 קמפיינים פעילים: *{active}*\n"
            f"🔴 קמפיינים מושהים: *{paused}*"
        )

        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=report_period_keyboard(account_key)
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ *שגיאת API:*\n`{e}`",
            parse_mode="Markdown",
            reply_markup=back_keyboard("menu:report")
        )
    await callback.answer()


def build_daily_report_text(report_data: dict, acc_name: str) -> str:
    """בניית טקסט דוח יומי לשליחה אוטומטית"""
    if "error" in report_data:
        return f"❌ שגיאה בטעינת דוח עבור {acc_name}: {report_data['error']}"

    insights = report_data.get("insights_today", {})
    account_info = report_data.get("account_info", {})
    currency = account_info.get("currency", "USD")

    spend = format_currency(insights.get("spend", "0"), currency)
    impressions = format_number(insights.get("impressions", "0"))
    clicks = format_number(insights.get("clicks", "0"))
    ctr = format_percent(insights.get("ctr", "0"))
    cpc = format_currency(insights.get("cpc", "0"), currency)

    return (
        f"📊 *דוח יומי — {acc_name}*\n\n"
        f"💰 הוצאה: {spend}\n"
        f"👁️ חשיפות: {impressions}\n"
        f"🖱️ קליקים: {clicks}\n"
        f"📈 CTR: {ctr}\n"
        f"💵 CPC: {cpc}\n"
        f"🟢 פעילים: {report_data.get('active_count', 0)} | "
        f"🔴 מושהים: {report_data.get('paused_count', 0)}"
    )
