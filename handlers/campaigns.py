from aiogram import Router, F
from aiogram.types import CallbackQuery
from services import MetaAPI, MetaAPIError
from utils import (
    accounts_keyboard, campaigns_keyboard, campaign_actions_keyboard,
    back_keyboard, format_currency, format_number, format_percent,
    status_emoji, status_hebrew, get_account, esc
)

router = Router()


@router.callback_query(F.data == "menu:campaigns")
async def campaigns_select_account(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎯 <b>ניהול קמפיינים</b>\n\nבחר חשבון:",
        parse_mode="HTML",
        reply_markup=accounts_keyboard("campaigns:list")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("campaigns:list:"))
async def campaigns_list(callback: CallbackQuery):
    account_key = callback.data.split(":")[2]
    acc = get_account(account_key)
    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await callback.message.edit_text("⏳ <b>טוען קמפיינים...</b>", parse_mode="HTML")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        campaigns = await api.get_campaigns()

        if not campaigns:
            await callback.message.edit_text(
                f"📭 <b>אין קמפיינים בחשבון {esc(acc.name)}</b>",
                parse_mode="HTML",
                reply_markup=back_keyboard("menu:campaigns")
            )
            return

        active = sum(1 for c in campaigns if c.get("status") == "ACTIVE")
        text = (
            f"🎯 <b>קמפיינים — {esc(acc.name)}</b>\n\n"
            f"סה\"כ: <b>{len(campaigns)}</b> | 🟢 פעילים: <b>{active}</b>\n\n"
            "בחר קמפיין לניהול:"
        )
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=campaigns_keyboard(campaigns, account_key)
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ <b>שגיאת API:</b>\n<code>{esc(e)}</code>",
            parse_mode="HTML",
            reply_markup=back_keyboard("menu:campaigns")
        )
    await callback.answer()


@router.callback_query(F.data.startswith("campaign:view:"))
async def campaign_view(callback: CallbackQuery):
    parts = callback.data.split(":")
    account_key = parts[2]
    campaign_id = parts[3]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await callback.message.edit_text("⏳ <b>טוען מידע על קמפיין...</b>", parse_mode="HTML")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        campaigns = await api.get_campaigns()
        campaign = next((c for c in campaigns if c["id"] == campaign_id), None)

        if not campaign:
            await callback.answer("❌ קמפיין לא נמצא", show_alert=True)
            return

        insights = await api.get_campaign_insights(campaign_id, days=7)
        status = campaign.get("status", "UNKNOWN")
        daily_budget = campaign.get("daily_budget")
        budget_str = f"${int(daily_budget)/100:.2f}/יום" if daily_budget else "ללא תקציב יומי"

        text = (
            f"{status_emoji(status)} <b>{esc(campaign.get('name', 'ללא שם'))}</b>\n\n"
            f"📌 סטטוס: <b>{esc(status_hebrew(status))}</b>\n"
            f"🎯 מטרה: {esc(campaign.get('objective', 'לא ידוע'))}\n"
            f"💰 תקציב: {esc(budget_str)}\n\n"
            f"📊 <b>ביצועים (7 ימים):</b>\n"
            f"💵 הוצאה: {esc(format_currency(insights.get('spend', '0')))}\n"
            f"👁️ חשיפות: {esc(format_number(insights.get('impressions', '0')))}\n"
            f"🖱️ קליקים: {esc(format_number(insights.get('clicks', '0')))}\n"
            f"📈 CTR: {esc(format_percent(insights.get('ctr', '0')))}\n"
            f"💵 CPC: {esc(format_currency(insights.get('cpc', '0')))}\n"
            f"🎯 Reach: {esc(format_number(insights.get('reach', '0')))}"
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=campaign_actions_keyboard(campaign_id, account_key, status)
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ <b>שגיאת API:</b>\n<code>{esc(e)}</code>",
            parse_mode="HTML",
            reply_markup=back_keyboard(f"campaigns:list:{account_key}")
        )
    await callback.answer()


@router.callback_query(F.data.startswith("campaign:toggle:"))
async def campaign_toggle(callback: CallbackQuery):
    parts = callback.data.split(":")
    account_key = parts[2]
    campaign_id = parts[3]
    new_status = parts[4]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    try:
        api = MetaAPI(acc.token, acc.account_id)
        success = await api.toggle_campaign(campaign_id, new_status)

        if success:
            action = "הופעל ✅" if new_status == "ACTIVE" else "הושהה ⏸️"
            await callback.answer(f"הקמפיין {action}", show_alert=True)
            callback.data = f"campaign:view:{account_key}:{campaign_id}"
            await campaign_view(callback)
        else:
            await callback.answer("❌ הפעולה נכשלה", show_alert=True)

    except MetaAPIError as e:
        await callback.answer(f"❌ שגיאה: {str(e)[:100]}", show_alert=True)


@router.callback_query(F.data.startswith("campaign:insights:"))
async def campaign_insights(callback: CallbackQuery):
    parts = callback.data.split(":")
    account_key = parts[2]
    campaign_id = parts[3]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await callback.message.edit_text("⏳ <b>טוען נתונים...</b>", parse_mode="HTML")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        ins_1d = await api.get_campaign_insights(campaign_id, days=1)
        ins_7d = await api.get_campaign_insights(campaign_id, days=7)
        ins_30d = await api.get_campaign_insights(campaign_id, days=30)

        text = (
            f"📊 <b>נתוני קמפיין מפורטים</b>\n\n"
            f"📅 <b>היום:</b>\n"
            f"  💵 הוצאה: {esc(format_currency(ins_1d.get('spend','0')))}\n"
            f"  👁️ חשיפות: {esc(format_number(ins_1d.get('impressions','0')))}\n"
            f"  📈 CTR: {esc(format_percent(ins_1d.get('ctr','0')))}\n\n"
            f"📅 <b>7 ימים:</b>\n"
            f"  💵 הוצאה: {esc(format_currency(ins_7d.get('spend','0')))}\n"
            f"  👁️ חשיפות: {esc(format_number(ins_7d.get('impressions','0')))}\n"
            f"  📈 CTR: {esc(format_percent(ins_7d.get('ctr','0')))}\n\n"
            f"📅 <b>30 ימים:</b>\n"
            f"  💵 הוצאה: {esc(format_currency(ins_30d.get('spend','0')))}\n"
            f"  👁️ חשיפות: {esc(format_number(ins_30d.get('impressions','0')))}\n"
            f"  📈 CTR: {esc(format_percent(ins_30d.get('ctr','0')))}"
        )

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 חזרה", callback_data=f"campaign:view:{account_key}:{campaign_id}")]
        ])

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ <b>שגיאת API:</b>\n<code>{esc(e)}</code>",
            parse_mode="HTML",
            reply_markup=back_keyboard(f"campaign:view:{account_key}:{campaign_id}")
        )
    await callback.answer()
