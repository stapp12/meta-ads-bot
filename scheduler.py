import logging
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import config
from services import MetaAPI, MetaAPIError
from utils import esc

logger = logging.getLogger(__name__)


async def send_daily_reports(bot: Bot):
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
                    f"❌ <b>שגיאה בדוח {esc(acc.name)}:</b> {esc(report_data['error'])}",
                    parse_mode="HTML"
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
                f"🌅 <b>דוח בוקר — {esc(acc.name)}</b>\n\n"
                f"💰 הוצאה היום: <b>{symbol}{spend:,.2f}</b>\n"
                f"👁️ חשיפות: <b>{impressions:,}</b>\n"
                f"🖱️ קליקים: <b>{clicks:,}</b>\n"
                f"📈 CTR: <b>{ctr:.2f}%</b>\n"
                f"💵 CPC: <b>{symbol}{cpc:.2f}</b>\n\n"
                f"🟢 קמפיינים פעילים: <b>{report_data.get('active_count', 0)}</b>\n"
                f"🔴 קמפיינים מושהים: <b>{report_data.get('paused_count', 0)}</b>"
            )

            await bot.send_message(config.ADMIN_CHAT_ID, report_text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"שגיאה בדוח {acc.name}: {e}")
            await bot.send_message(
                config.ADMIN_CHAT_ID,
                f"❌ <b>שגיאה בדוח {esc(acc.name)}:</b> <code>{esc(str(e)[:200])}</code>",
                parse_mode="HTML"
            )


def setup_scheduler(scheduler: AsyncIOScheduler, bot: Bot):
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
