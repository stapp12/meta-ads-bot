import os
from dataclasses import dataclass, field
from typing import Dict
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AccountConfig:
    name: str
    token: str
    account_id: str
    account_type: str  # "business" or "personal"


@dataclass
class Config:
    TELEGRAM_TOKEN: str = field(default_factory=lambda: os.getenv("TELEGRAM_TOKEN", ""))
    ADMIN_CHAT_ID: int = field(default_factory=lambda: int(os.getenv("ADMIN_CHAT_ID", "0")))
    ANTHROPIC_API_KEY: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    REPORT_HOUR: int = field(default_factory=lambda: int(os.getenv("REPORT_HOUR", "8")))
    META_APP_ID: str = "940027548867403"

    @property
    def accounts(self) -> Dict[str, AccountConfig]:
        return {
            "kohavi_main": AccountConfig(
                name="Kohavi Lab - ראשי",
                token=os.getenv("TOKEN_KOHAVI", ""),
                account_id="act_769641286031489",
                account_type="business"
            ),
            "kohavi_boostly": AccountConfig(
                name="Kohavi Lab - Boostly",
                token=os.getenv("TOKEN_KOHAVI", ""),  # אותו System User Token
                account_id="act_1755921072055014",
                account_type="business"
            ),
            "boostlyisrael": AccountConfig(
                name="Boostly Israel",
                token=os.getenv("TOKEN_BOOSTLYISRAEL", ""),
                account_id="act_1262785792546371",
                account_type="business"
            ),
            "holyland": AccountConfig(
                name="Holyland Secrets",
                token=os.getenv("TOKEN_HOLYLAND", ""),
                account_id="act_822829733869759",
                account_type="business"
            ),
            "meayan": AccountConfig(
                name="מעיין - חשבון אישי",
                token=os.getenv("TOKEN_MEAYAN", ""),
                account_id="act_1748593649883651",
                account_type="personal"
            ),
        }


config = Config()
