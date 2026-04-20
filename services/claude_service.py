import logging
import anthropic
from config import config

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """אתה מנתח קמפיינים מומחה של Meta Ads.
אתה מספק ניתוחים חכמים, ממוקדים ואקציונביליים בעברית.
התשובות שלך ישירות, ברורות ועם המלצות ספציפיות.
השתמש באימוג'י בצורה מדודה כדי לשפר קריאות."""


async def analyze_campaigns(report_data: dict, account_name: str) -> str:
    """ניתוח קמפיינים עם Claude"""
    try:
        insights_today = report_data.get("insights_today", {})
        insights_7d = report_data.get("insights_7d", {})
        campaigns = report_data.get("campaigns", [])

        prompt = f"""נתח את נתוני המודעות הבאים עבור חשבון "{account_name}":

**נתונים להיום:**
- הוצאה: ${insights_today.get('spend', '0')}
- חשיפות: {insights_today.get('impressions', '0')}
- קליקים: {insights_today.get('clicks', '0')}
- CTR: {insights_today.get('ctr', '0')}%
- CPC: ${insights_today.get('cpc', '0')}

**נתונים 7 ימים אחרונים:**
- הוצאה כוללת: ${insights_7d.get('spend', '0')}
- חשיפות: {insights_7d.get('impressions', '0')}
- קליקים: {insights_7d.get('clicks', '0')}
- CTR ממוצע: {insights_7d.get('ctr', '0')}%
- CPC ממוצע: ${insights_7d.get('cpc', '0')}

**קמפיינים פעילים:** {report_data.get('active_count', 0)}
**קמפיינים מושהים:** {report_data.get('paused_count', 0)}

ספק:
1. סיכום ביצועים (2-3 משפטים)
2. 2-3 תצפיות חשובות
3. 2-3 המלצות מעשיות ספציפיות
4. האם יש משהו דחוף לטפל בו?

כתוב בצורה תמציתית ומקצועית."""

        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    except Exception as e:
        logger.error(f"שגיאת Claude: {e}")
        return "❌ לא ניתן לטעון ניתוח AI כרגע."


async def analyze_single_campaign(campaign: dict, insights: dict) -> str:
    """ניתוח קמפיין בודד"""
    try:
        prompt = f"""נתח את הקמפיין הבא:

**שם:** {campaign.get('name', 'לא ידוע')}
**סטטוס:** {campaign.get('status', 'לא ידוע')}
**מטרה:** {campaign.get('objective', 'לא ידוע')}
**תקציב יומי:** ${int(campaign.get('daily_budget', 0)) / 100:.2f} (אם קיים)

**ביצועים (7 ימים):**
- הוצאה: ${insights.get('spend', '0')}
- חשיפות: {insights.get('impressions', '0')}
- קליקים: {insights.get('clicks', '0')}
- CTR: {insights.get('ctr', '0')}%
- CPC: ${insights.get('cpc', '0')}
- טווח הגעה: {insights.get('reach', '0')}

תן ניתוח קצר (3-4 משפטים) עם המלצה מעשית אחת ספציפית."""

        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    except Exception as e:
        logger.error(f"שגיאת Claude: {e}")
        return "❌ לא ניתן לטעון ניתוח AI כרגע."


async def get_optimization_tips(campaigns: list, account_name: str) -> str:
    """טיפים לאופטימיזציה"""
    try:
        campaigns_summary = "\n".join([
            f"- {c.get('name', 'ללא שם')}: {c.get('status', '?')} | תקציב: ${int(c.get('daily_budget', 0)) / 100:.2f}/יום"
            for c in campaigns[:10]
        ])

        prompt = f"""עבור חשבון "{account_name}" עם הקמפיינים הבאים:
{campaigns_summary}

תן 3 טיפים מעשיים לאופטימיזציה שניתן ליישם עכשיו.
כל טיפ: שורה אחת, ישיר ואקציונבילי."""

        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    except Exception as e:
        logger.error(f"שגיאת Claude: {e}")
        return "❌ לא ניתן לטעון טיפים כרגע."
