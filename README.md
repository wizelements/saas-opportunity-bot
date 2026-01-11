# SaaS Opportunity Bot

Automatically scans Hacker News for SaaS opportunities in high-value industries. Now with **ottomator Live Agent Studio** integration for conversational AI-powered analysis!

## What it does

1. **Scans** Hacker News for posts/comments
2. **Detects** pain point signals ("I wish there was...", "I'd pay for...", etc.)
3. **Filters** by high-value industries (finance, legal, healthcare, real estate, SaaS/B2B, agencies, e-commerce)
4. **Scores** opportunities by engagement and signal strength
5. **Outputs** prioritized list to CSV and JSON
6. **AI Analysis** (new!) - Uses LLM to generate actionable SaaS ideas from pain points

## Quick Start

### CLI Mode (Original)

```bash
cd saas-opportunity-bot
pip install -r requirements.txt
python main.py
```

### Agent Mode (ottomator)

```bash
# Copy environment file and configure
cp agent/.env.example agent/.env
# Edit agent/.env with your API keys

# Run the agent locally
pip install -r requirements.txt
python agent/saas_agent.py
```

The agent runs at `http://localhost:8001` and accepts conversational queries like:
- "Scan for opportunities"
- "Find fintech opportunities"  
- "Analyze the top 10 pain points"
- "Show me healthcare pain points"

## ottomator Live Agent Studio Deployment

This bot is compatible with the [ottomator Live Agent Studio](https://studio.ottomator.ai).

### Docker Deployment

```bash
# Build the image
docker build -t saas-opportunity-agent .

# Run with environment variables
docker run -d -p 8001:8001 \
  -e API_BEARER_TOKEN=your_token \
  -e OPENAI_API_KEY=sk-your-key \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_SERVICE_KEY=your_key \
  saas-opportunity-agent
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `API_BEARER_TOKEN` | Yes | Authentication token (ottomator provides this) |
| `OPENAI_API_KEY` | Yes | OpenAI API key for AI analysis |
| `LLM_MODEL` | No | Model to use (default: gpt-4o-mini) |
| `PORT` | No | Port to run on (default: 8001) |
| `SUPABASE_URL` | For Studio | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | For Studio | Supabase service key |

### API Endpoint

**POST** `/api/saas-opportunity-agent`

Request:
```json
{
  "query": "Find opportunities in fintech",
  "user_id": "user123",
  "request_id": "req456", 
  "session_id": "session789"
}
```

Response:
```json
{
  "success": true
}
```

The agent response is stored in the Supabase `messages` table for the ottomator UI to display.

## Configuration

Edit `config.py` to customize:

- **INDUSTRIES**: Keywords for each industry vertical
- **PAIN_SIGNALS**: Phrases that indicate buying intent
- **SUBREDDITS**: Which subreddits to scan (for future Reddit integration)
- **HN_STORIES_TO_CHECK**: How many HN stories to analyze

## Output

Results are saved to `results/` folder:
- `opportunities_YYYYMMDD_HHMMSS.csv` - Spreadsheet format
- `opportunities_YYYYMMDD_HHMMSS.json` - JSON format

Each opportunity includes:
- Priority score (higher = better opportunity)
- Source (hackernews)
- Title and text snippet
- Direct URL
- Pain signals detected
- Industries identified

## GitHub Actions (Automated Scans)

The bot runs daily at 8am UTC via GitHub Actions. Results are committed to the `results/` folder.

To trigger a manual scan, go to Actions > SaaS Opportunity Scan > Run workflow.

## Architecture

```
saas-opportunity-bot/
├── agent/
│   ├── saas_agent.py      # FastAPI agent for ottomator
│   └── .env.example       # Environment template
├── scrapers/
│   ├── hn_scraper.py      # Hacker News API scanner
│   └── reddit_scraper.py  # Reddit scanner (needs OAuth)
├── results/               # Scan outputs
├── config.py              # Industries, signals, settings
├── main.py                # CLI entry point
├── Dockerfile             # Container build
└── requirements.txt       # Python dependencies
```

## Rate Limits

- Hacker News: No strict limit (uses public Firebase API)
- OpenAI: Based on your API tier

## Contributing

This agent is part of the [ottomator agents collection](https://github.com/coleam00/ottomator-agents). See the main repository for contribution guidelines.
