# 🎯 Meta Ads Manager Bot

בוט טלגרם לניהול וניתוח קמפיינים של Meta Ads עם AI.

## פיצ'רים

- 📊 דוחות ביצועים (היום / 7 ימים / 30 ימים)
- 🎯 ניהול קמפיינים (הפעלה/השהיה/תקציב)
- 📋 ניהול אדסטים
- 🤖 ניתוח AI עם Claude Haiku
- 🌅 דוחות יומיים אוטומטיים
- 👥 תמיכה במספר חשבונות מודעות

## הגדרות

### 1. העתק את קובץ ה-env

```bash
cp .env.example .env
```

### 2. מלא את הפרטים ב-.env

```
TELEGRAM_TOKEN=         # מ-@BotFather
ADMIN_CHAT_ID=          # מ-@userinfobot
ANTHROPIC_API_KEY=      # מ-console.anthropic.com
TOKEN_KOHAVI_MAIN=      # System User Token - Kohavi Lab
TOKEN_BOOSTLY=          # System User Token - Boostly
TOKEN_PERSONAL=         # Long-Lived User Token - חשבון אישי
REPORT_HOUR=8           # שעת דוח יומי
```

### 3. התקנת dependencies

```bash
pip install -r requirements.txt
```

### 4. הרצה מקומית

```bash
python bot.py
```

## Deploy ל-Railway

1. Push ל-GitHub
2. Railway → New Project → Deploy from GitHub
3. הוסף את כל ה-environment variables מה-.env
4. הפרויקט יעלה אוטומטית

## חשבונות מוגדרים

| שם | Account ID | סוג |
|---|---|---|
| קוהבי - חשבון ראשי | act_769641286031489 | Business |
| Boostly | act_1755921072055014 | Business |
| חשבון אישי | act_1748593649883651 | Personal |
