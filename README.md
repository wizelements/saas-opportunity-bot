# SaaS Opportunity Bot

Automatically scans Reddit and Hacker News for SaaS opportunities in high-value industries.

## What it does

1. **Scans** Reddit subreddits and Hacker News for posts/comments
2. **Detects** pain point signals ("I wish there was...", "I'd pay for...", etc.)
3. **Filters** by high-value industries (finance, legal, healthcare, real estate, SaaS/B2B, agencies, e-commerce)
4. **Scores** opportunities by engagement and signal strength
5. **Outputs** prioritized list to CSV and JSON

## Quick Start

```bash
cd saas-opportunity-bot
pip install -r requirements.txt
python main.py
```

## Configuration

Edit `config.py` to customize:

- **INDUSTRIES**: Keywords for each industry vertical
- **PAIN_SIGNALS**: Phrases that indicate buying intent
- **SUBREDDITS**: Which subreddits to scan
- **HN_STORIES_TO_CHECK**: How many HN stories to analyze

## Output

Results are saved to `results/` folder:
- `opportunities_YYYYMMDD_HHMMSS.csv` - Spreadsheet format
- `opportunities_YYYYMMDD_HHMMSS.json` - JSON format

Each opportunity includes:
- Priority score (higher = better opportunity)
- Source (reddit/hackernews)
- Title and text snippet
- Direct URL
- Pain signals detected
- Industries identified

## Scheduling (Optional)

Run daily with Windows Task Scheduler or cron:

```bash
# Linux/Mac cron (daily at 8am)
0 8 * * * cd /path/to/saas-opportunity-bot && python main.py

# Windows Task Scheduler
# Action: python
# Arguments: main.py
# Start in: C:\Users\jacla\projects\saas-opportunity-bot
```

## Rate Limits

- Reddit: ~60 requests/minute (public API)
- Hacker News: No strict limit, but be respectful

The bot includes delays between requests to avoid hitting limits.
