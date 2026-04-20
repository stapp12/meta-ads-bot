from aiogram import Router, F
from aiogram.types import CallbackQuery
from services import MetaAPI, MetaAPIError
from services.claude_service import analyze_campaigns, analyze_single_campaign, get_optimization_tips
from utils import accounts_keyboard, back_keyboard, get_account

router = Router()


@router.callback_query(F.data == "menu:ai")
async def ai_select_account(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 *ניתוח AI — Meta Ads*\n\nבחר חשבון לניתוח:",
        parse_mode="Markdown",
        reply_markup=accounts_keyboard("ai:account")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ai:account:"))
async def ai_analyze_account(callback: CallbackQuery):
    account_key = callback.data.split(":")[2]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await callback.message.edit_text(
        f"🤖 *מנתח את {acc.name}...*\n\nאנא המתן, זה עלול לקחת כמה שניות.",
        parse_mode="Markdown"
    )

    try:
        api = MetaAPI(acc.token, acc.account_id)
        report_data = await api.get_full_daily_report()

        analysis = await analyze_campaigns(report_data, acc.name)

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💡 טיפים לאופטימיזציה", callback_data=f"ai:tips:{account_key}")],
            [InlineKeyboardButton(text="🔙 חזרה", callback_data="menu:ai")]
        ])

        await callback.message.edit_text(
            f"🤖 *ניתוח AI — {acc.name}*\n\n{analysis}",
            parse_mode="Markdown",
            reply_markup=kb
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ *שגיאת API:*\n`{e}`",
            parse_mode="Markdown",
            reply_markup=back_keyboard("menu:ai")
        )
    await callback.answer()


@router.callback_query(F.data.startswith("ai:tips:"))
async def ai_optimization_tips(callback: CallbackQuery):
    account_key = callback.data.split(":")[2]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await callback.message.edit_text("💡 *מכין טיפים לאופטימיזציה...*", parse_mode="Markdown")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        campaigns = await api.get_campaigns()
        tips = await get_optimization_tips(campaigns, acc.name)

        await callback.message.edit_text(
            f"💡 *טיפים לאופטימיזציה — {acc.name}*\n\n{tips}",
            parse_mode="Markdown",
            reply_markup=back_keyboard(f"ai:account:{account_key}")
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ *שגיאת API:*\n`{e}`",
            parse_mode="Markdown",
            reply_markup=back_keyboard("menu:ai")
        )
    await callback.answer()


@router.callback_query(F.data.startswith("ai:campaign:"))
async def ai_analyze_campaign(callback: CallbackQuery):
    parts = callback.data.split(":")
    account_key = parts[2]
    campaign_id = parts[3]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await callback.message.edit_text("🤖 *מנתח קמפיין...*", parse_mode="Markdown")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        campaigns = await api.get_campaigns()
        campaign = next((c for c in campaigns if c["id"] == campaign_id), {})
        insights = await api.get_campaign_insights(campaign_id, days=7)

        analysis = await analyze_single_campaign(campaign, insights)

        await callback.message.edit_text(
            f"🤖 *ניתוח AI — {campaign.get('name', 'קמפיין')}*\n\n{analysis}",
            parse_mode="Markdown",
            reply_markup=back_keyboard(f"campaign:view:{account_key}:{campaign_id}")
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ *שגיאת API:*\n`{e}`",
            parse_mode="Markdown",
            reply_markup=back_keyboard(f"campaign:view:{account_key}:{campaign_id}")
        )
    await callback.answer()


@router.callback_query(F.data.startswith("ai:adset:"))
async def ai_analyze_adset(callback: CallbackQuery):
    parts = callback.data.split(":")
    account_key = parts[2]
    adset_id = parts[3]
    acc = get_account(account_key)

    if not acc or not acc.token:
        await callback.answer("❌ Token לא מוגדר", show_alert=True)
        return

    await callback.message.edit_text("🤖 *מנתח אדסט...*", parse_mode="Markdown")

    try:
        api = MetaAPI(acc.token, acc.account_id)
        insights = await api.get_adset_insights(adset_id, days=7)

        fake_campaign = {"name": f"אדסט {adset_id}", "status": "ACTIVE", "objective": "—"}
        analysis = await analyze_single_campaign(fake_campaign, insights)

        await callback.message.edit_text(
            f"🤖 *ניתוח AI — אדסט*\n\n{analysis}",
            parse_mode="Markdown",
            reply_markup=back_keyboard("menu:adsets")
        )

    except MetaAPIError as e:
        await callback.message.edit_text(
            f"❌ *שגיאת API:*\n`{e}`",
            parse_mode="Markdown",
            reply_markup=back_keyboard("menu:adsets")
        )
    await callback.answer()
