import logging
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import config
from services import MetaAPI, MetaAPIError
from services.claude_service import analyze_campaigns

logger = logging.getLogger(__name__)


async def send_daily_reports(bot: Bot):
    """שולח דוחות יומיים לכל החשבונות"""
    logger.info("📊 שולח דוחות יומיים...")

    for acc_key, acc in config.accounts.items():
        if not acc.token:
            continue
        try:
            api = MetaAPI(acc.token, acc.account_id)
            report_data = await api.get_full_daily_report()

            if "error" in report_data:
                await bot.send_message(
                    config.ADMIN_CHAT_ID,
                    f"❌ *שגיאה בדוח {acc.name}:* {report_data['error']}",
                    parse_mode="Markdown"
                )
                continue

            insights = report_data.get("insights_today", {})
            account_info = report_data.get("account_info", {})
            currency = account_info.get("currency", "USD")
            symbol = "₪" if currency == "ILS" else "$"

            spend = float(insights.get("spend", 0))
            impressions = int(float(insights.get("impressions", 0)))
            clicks = int(float(insights.get("clicks", 0)))
            ctr = float(insights.get("ctr", 0))
            cpc = float(insights.get("cpc", 0))

            report_text = (
                f"🌅 *דוח בוקר — {acc.name}*\n\n"
                f"💰 הוצאה היום: *{symbol}{spend:,.2f}*\n"
                f"👁️ חשיפות: *{impressions:,}*\n"
                f"🖱️ קליקים: *{clicks:,}*\n"
                f"📈 CTR: *{ctr:.2f}%*\n"
                f"💵 CPC: *{symbol}{cpc:.2f}*\n\n"
                f"🟢 קמפיינים פעילים: *{report_data.get('active_count', 0)}*\n"
                f"🔴 קמפיינים מושהים: *{report_data.get('paused_count', 0)}*"
            )

            await bot.send_message(
                config.ADMIN_CHAT_ID,
                report_text,
                parse_mode="Markdown"
            )

            # ניתוח AI
            analysis = analyze_campaigns(report_data, acc.name)
            await bot.send_message(
                config.ADMIN_CHAT_ID,
                f"🤖 *ניתוח AI — {acc.name}*\n\n{analysis}",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"שגיאה בדוח {acc.name}: {e}")
            await bot.send_message(
                config.ADMIN_CHAT_ID,
                f"❌ *שגיאה בדוח {acc.name}:* `{str(e)[:200]}`",
                parse_mode="Markdown"
            )


def setup_scheduler(scheduler: AsyncIOScheduler, bot: Bot):
    """מגדיר את המשימות המתוזמנות"""
    scheduler.add_job(
        send_daily_reports,
        trigger="cron",
        hour=config.REPORT_HOUR,
        minute=0,
        args=[bot],
        id="daily_report",
        replace_existing=True
    )
    logger.info(f"✅ דוחות יומיים מוגדרים לשעה {config.REPORT_HOUR}:00")
