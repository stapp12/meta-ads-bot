import html as _html
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import config


def esc(text) -> str:
    return _html.escape(str(text))


def get_account(account_key: str):
    return config.accounts.get(account_key)


def format_currency(amount_str: str, currency: str = "USD") -> str:
    try:
        amount = float(amount_str or 0)
        symbol = "₪" if currency == "ILS" else "$"
        return f"{symbol}{amount:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


def format_number(num_str: str) -> str:
    try:
        n = int(float(num_str or 0))
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)
    except (ValueError, TypeError):
        return "0"


def format_percent(val: str) -> str:
    try:
        return f"{float(val or 0):.2f}%"
    except (ValueError, TypeError):
        return "0%"


def status_emoji(status: str) -> str:
    return "🟢" if status == "ACTIVE" else "🔴"


def status_hebrew(status: str) -> str:
    return "פעיל" if status == "ACTIVE" else "מושהה"


# ─── Keyboards ───────────────────────────────────────────────────────────────

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 דוח יומי", callback_data="menu:report"),
         InlineKeyboardButton(text="🎯 קמפיינים", callback_data="menu:campaigns")],
        [InlineKeyboardButton(text="📋 אדסטים", callback_data="menu:adsets"),
         InlineKeyboardButton(text="➕ צור קמפיין", callback_data="menu:create")],
        [InlineKeyboardButton(text="⚙️ הגדרות", callback_data="menu:settings")],
    ])


def accounts_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    for key, acc in config.accounts.items():
        emoji = "🏢" if acc.account_type == "business" else "👤"
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {acc.name}",
            callback_data=f"{callback_prefix}:{key}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 חזרה", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def campaigns_keyboard(campaigns: list, account_key: str) -> InlineKeyboardMarkup:
    buttons = []
    for c in campaigns[:15]:
        emoji = status_emoji(c.get("status", "PAUSED"))
        name = c.get("name", "ללא שם")[:30]
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {name}",
            callback_data=f"campaign:view:{account_key}:{c['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 חזרה", callback_data="menu:campaigns")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def campaign_actions_keyboard(campaign_id: str, account_key: str, status: str) -> InlineKeyboardMarkup:
    toggle_text = "⏸️ השהה" if status == "ACTIVE" else "▶️ הפעל"
    toggle_status = "PAUSED" if status == "ACTIVE" else "ACTIVE"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data=f"campaign:toggle:{account_key}:{campaign_id}:{toggle_status}"),
         InlineKeyboardButton(text="📉 שנה תקציב", callback_data=f"budget:campaign:{account_key}:{campaign_id}")],
        [InlineKeyboardButton(text="📋 אדסטים", callback_data=f"adsets:list:{account_key}:{campaign_id}"),
         InlineKeyboardButton(text="📊 נתונים", callback_data=f"campaign:insights:{account_key}:{campaign_id}")],
        [InlineKeyboardButton(text="🔙 חזרה", callback_data=f"campaigns:list:{account_key}")],
    ])


def adsets_keyboard(adsets: list, account_key: str, campaign_id: str) -> InlineKeyboardMarkup:
    buttons = []
    for a in adsets[:10]:
        emoji = status_emoji(a.get("status", "PAUSED"))
        name = a.get("name", "ללא שם")[:30]
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {name}",
            callback_data=f"adset:view:{account_key}:{campaign_id}:{a['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 חזרה", callback_data=f"campaign:view:{account_key}:{campaign_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def adset_actions_keyboard(adset_id: str, account_key: str, campaign_id: str, status: str) -> InlineKeyboardMarkup:
    toggle_text = "⏸️ השהה" if status == "ACTIVE" else "▶️ הפעל"
    toggle_status = "PAUSED" if status == "ACTIVE" else "ACTIVE"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data=f"adset:toggle:{account_key}:{campaign_id}:{adset_id}:{toggle_status}"),
         InlineKeyboardButton(text="📉 שנה תקציב", callback_data=f"budget:adset:{account_key}:{adset_id}")],
        [InlineKeyboardButton(text="🔙 חזרה", callback_data=f"adsets:list:{account_key}:{campaign_id}")],
    ])


def report_period_keyboard(account_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 היום", callback_data=f"report:period:{account_key}:1"),
         InlineKeyboardButton(text="📅 7 ימים", callback_data=f"report:period:{account_key}:7")],
        [InlineKeyboardButton(text="📅 30 ימים", callback_data=f"report:period:{account_key}:30")],
        [InlineKeyboardButton(text="🔙 חזרה", callback_data="menu:report")],
    ])


def objectives_keyboard() -> InlineKeyboardMarkup:
    objectives = [
        ("🎯 מודעות", "OUTCOME_AWARENESS"),
        ("📈 תנועה", "OUTCOME_TRAFFIC"),
        ("💬 מעורבות", "OUTCOME_ENGAGEMENT"),
        ("📥 לידים", "OUTCOME_LEADS"),
        ("🛒 מכירות", "OUTCOME_SALES"),
        ("📱 אפליקציה", "OUTCOME_APP_PROMOTION"),
    ]
    buttons = [[InlineKeyboardButton(text=text, callback_data=f"create:objective:{val}")]
               for text, val in objectives]
    buttons.append([InlineKeyboardButton(text="❌ ביטול", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_keyboard(callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 חזרה", callback_data=callback)]
    ])


def confirm_keyboard(confirm_cb: str, cancel_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ אישור", callback_data=confirm_cb),
         InlineKeyboardButton(text="❌ ביטול", callback_data=cancel_cb)]
    ])
