import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://graph.facebook.com/v19.0"


class MetaAPIError(Exception):
    pass


class MetaAPI:
    def __init__(self, access_token: str, account_id: str):
        self.token = access_token
        self.account_id = account_id

    def _params(self, extra: dict = None) -> dict:
        p = {"access_token": self.token}
        if extra:
            p.update(extra)
        return p

    async def _get(self, endpoint: str, params: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{BASE_URL}/{endpoint}",
                params=self._params(params)
            )
            data = r.json()
            if "error" in data:
                raise MetaAPIError(data["error"].get("message", "שגיאה לא ידועה"))
            return data

    async def _post(self, endpoint: str, data: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{BASE_URL}/{endpoint}",
                params={"access_token": self.token},
                data=data or {}
            )
            result = r.json()
            if "error" in result:
                raise MetaAPIError(result["error"].get("message", "שגיאה לא ידועה"))
            return result

    # ─── קמפיינים ───────────────────────────────────────────────

    async def get_campaigns(self) -> list:
        data = await self._get(
            f"{self.account_id}/campaigns",
            {
                "fields": "id,name,status,objective,daily_budget,lifetime_budget,spend_cap",
                "limit": 50
            }
        )
        return data.get("data", [])

    async def get_campaign_insights(self, campaign_id: str, days: int = 7) -> dict:
        data = await self._get(
            f"{campaign_id}/insights",
            {
                "fields": "impressions,clicks,spend,ctr,cpc,cpp,reach,frequency,actions",
                "date_preset": f"last_{days}_days",
            }
        )
        result = data.get("data", [])
        return result[0] if result else {}

    async def toggle_campaign(self, campaign_id: str, status: str) -> bool:
        """status: ACTIVE or PAUSED"""
        result = await self._post(f"{campaign_id}", {"status": status})
        return result.get("success", False)

    async def update_campaign_budget(self, campaign_id: str, daily_budget: int) -> bool:
        """daily_budget in cents (e.g. 5000 = 50 ILS)"""
        result = await self._post(f"{campaign_id}", {"daily_budget": str(daily_budget)})
        return result.get("success", False)

    # ─── אדסטים ─────────────────────────────────────────────────

    async def get_adsets(self, campaign_id: str) -> list:
        data = await self._get(
            f"{campaign_id}/adsets",
            {
                "fields": "id,name,status,daily_budget,targeting,optimization_goal,bid_amount",
                "limit": 50
            }
        )
        return data.get("data", [])

    async def toggle_adset(self, adset_id: str, status: str) -> bool:
        result = await self._post(f"{adset_id}", {"status": status})
        return result.get("success", False)

    async def update_adset_budget(self, adset_id: str, daily_budget: int) -> bool:
        result = await self._post(f"{adset_id}", {"daily_budget": str(daily_budget)})
        return result.get("success", False)

    async def get_adset_insights(self, adset_id: str, days: int = 7) -> dict:
        data = await self._get(
            f"{adset_id}/insights",
            {
                "fields": "impressions,clicks,spend,ctr,cpc,reach,actions",
                "date_preset": f"last_{days}_days",
            }
        )
        result = data.get("data", [])
        return result[0] if result else {}

    # ─── מודעות ──────────────────────────────────────────────────

    async def get_ads(self, adset_id: str) -> list:
        data = await self._get(
            f"{adset_id}/ads",
            {"fields": "id,name,status,creative", "limit": 50}
        )
        return data.get("data", [])

    # ─── דוח חשבון ───────────────────────────────────────────────

    async def get_account_insights(self, days: int = 7) -> dict:
        data = await self._get(
            f"{self.account_id}/insights",
            {
                "fields": "impressions,clicks,spend,ctr,cpc,reach,frequency,actions,cost_per_action_type",
                "date_preset": f"last_{days}_days",
                "level": "account"
            }
        )
        result = data.get("data", [])
        return result[0] if result else {}

    async def get_account_spend_limit(self) -> dict:
        data = await self._get(
            self.account_id,
            {"fields": "name,currency,account_status,spend_cap,amount_spent,balance"}
        )
        return data

    # ─── דוח יומי מלא ────────────────────────────────────────────

    async def get_full_daily_report(self) -> dict:
        """משיג את כל הנתונים לדוח היומי"""
        try:
            account_info = await self.get_account_spend_limit()
            insights_today = await self.get_account_insights(days=1)
            insights_7d = await self.get_account_insights(days=7)
            campaigns = await self.get_campaigns()

            active_campaigns = [c for c in campaigns if c.get("status") == "ACTIVE"]
            paused_campaigns = [c for c in campaigns if c.get("status") == "PAUSED"]

            return {
                "account_info": account_info,
                "insights_today": insights_today,
                "insights_7d": insights_7d,
                "campaigns": campaigns,
                "active_count": len(active_campaigns),
                "paused_count": len(paused_campaigns),
            }
        except MetaAPIError as e:
            return {"error": str(e)}
