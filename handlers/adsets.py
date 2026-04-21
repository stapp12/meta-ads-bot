from aiogram import Router, F
from aiogram.types import CallbackQuery
from services import MetaAPI, MetaAPIError
from utils import (
    esc, accounts_keyboard, adsets_keyboard, adset_actions_keyboard,
    back_keyboard, format_currency, format_number, format_percent,
    status_emoji, status_hebrew, get_account
)

router = Router()


@router.callback_query(F.data == "menu:adsets")
async def adsets_select_account(callback: CallbackQuery):
    await callback.message.edit_text(
        "📋 <b>ניהול אדסטים</b>\n\nבחר חשבון:",
        parse_mode="HTML",
        reply_markup=accounts_keyboard("adsets:account")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adsets:account:"))
async def adsets_select_campaign(callback: CallbackQuery):
    account_key = callback.data.split(":")[2]
    acc = get_account(account_key)
    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await callback.message.edit_text("⏳ טוען קמפיינים...", parse_mode="HTML")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        campaigns = await api.get_campaigns()

        if not campaigns:
            await callback.message.edit_text(
                "📭 <b>אין קמפיינים בחשבון זה</b>",
                parse_mode="HTML",
                reply_markup=back_keyboard("menu:adsets")
            )
            return

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for c in campaigns[:15]:
            emoji = status_emoji(c.get("status", "PAUSED"))
            name = c.get("name", "ללא שם")[:30]
            buttons.append([InlineKeyboardButton(
                text=f"{emoji} {name}",
                callback_data=f"adsets:list:{account_key}:{c['id']}"
            )])
        buttons.append([InlineKeyboardButton(text="🔙 חזרה", callback_data="menu:adsets")])

        await callback.message.edit_text(
            f"📋 <b>אדסטים — {esc(acc.name)}</b>\n\nבחר קמפיין:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ <b>שגיאת API:</b>\n<code>{esc(str(e))}</code>",
            parse_mode="HTML",
            reply_markup=back_keyboard("menu:adsets")
        )
    await callback.answer()


@router.callback_query(F.data.startswith("adsets:list:"))
async def adsets_list(callback: CallbackQuery):
    parts = callback.data.split(":")
    account_key = parts[2]
    campaign_id = parts[3]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await callback.message.edit_text("⏳ טוען אדסטים...", parse_mode="HTML")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        adsets = await api.get_adsets(campaign_id)

        if not adsets:
            await callback.message.edit_text(
                "📭 <b>אין אדסטים בקמפיין זה</b>",
                parse_mode="HTML",
                reply_markup=back_keyboard(f"adsets:account:{account_key}")
            )
            return

        active = sum(1 for a in adsets if a.get("status") == "ACTIVE")
        text = (
            f"📋 <b>אדסטים</b>\n\n"
            f"סה\"כ: <b>{len(adsets)}</b> | 🟢 פעילים: <b>{active}</b>\n\n"
            "בחר אדסט:"
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=adsets_keyboard(adsets, account_key, campaign_id)
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ <b>שגיאת API:</b>\n<code>{esc(str(e))}</code>",
            parse_mode="HTML",
            reply_markup=back_keyboard("menu:adsets")
        )
    await callback.answer()


@router.callback_query(F.data.startswith("adset:view:"))
async def adset_view(callback: CallbackQuery):
    parts = callback.data.split(":")
    account_key = parts[2]
    campaign_id = parts[3]
    adset_id = parts[4]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await callback.message.edit_text("⏳ טוען מידע על אדסט...", parse_mode="HTML")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        adsets = await api.get_adsets(campaign_id)
        adset = next((a for a in adsets if a["id"] == adset_id), None)

        if not adset:
            await callback.answer("❌ אדסט לא נמצא", show_alert=True)
            return

        insights = await api.get_adset_insights(adset_id, days=7)
        status = adset.get("status", "UNKNOWN")
        daily_budget = adset.get("daily_budget")
        budget_str = f"${int(daily_budget)/100:.2f}/יום" if daily_budget else "לפי קמפיין"

        text = (
            f"{status_emoji(status)} <b>{esc(adset.get('name', 'ללא שם'))}</b>\n\n"
            f"📌 סטטוס: <b>{status_hebrew(status)}</b>\n"
            f"🎯 מטרת אופטימיזציה: {esc(adset.get('optimization_goal', 'לא ידוע'))}\n"
            f"💰 תקציב: {esc(budget_str)}\n\n"
            f"📊 <b>ביצועים (7 ימים):</b>\n"
            f"💵 הוצאה: {format_currency(insights.get('spend', '0'))}\n"
            f"👁️ חשיפות: {format_number(insights.get('impressions', '0'))}\n"
            f"🖱️ קליקים: {format_number(insights.get('clicks', '0'))}\n"
            f"📈 CTR: {format_percent(insights.get('ctr', '0'))}\n"
            f"💵 CPC: {format_currency(insights.get('cpc', '0'))}\n"
            f"🎯 Reach: {format_number(insights.get('reach', '0'))}"
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=adset_actions_keyboard(adset_id, account_key, campaign_id, status)
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ <b>שגיאת API:</b>\n<code>{esc(str(e))}</code>",
            parse_mode="HTML",
            reply_markup=back_keyboard(f"adsets:list:{account_key}:{campaign_id}")
        )
    await callback.answer()


@router.callback_query(F.data.startswith("adset:toggle:"))
async def adset_toggle(callback: CallbackQuery):
    parts = callback.data.split(":")
    account_key = parts[2]
    campaign_id = parts[3]
    adset_id = parts[4]
    new_status = parts[5]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    try:
        api = MetaAPI(acc.token, acc.account_id)
        success = await api.toggle_adset(adset_id, new_status)

        if success:
            action = "הופעל ✅" if new_status == "ACTIVE" else "הושהה ⏸️"
            await callback.answer(f"האדסט {action}", show_alert=True)
            callback.data = f"adset:view:{account_key}:{campaign_id}:{adset_id}"
            await adset_view(callback)
        else:
            await callback.answer("❌ הפעולה נכשלה", show_alert=True)

    except MetaAPIError as e:
        await callback.answer(f"❌ שגיאה: {str(e)[:100]}", show_alert=True)
