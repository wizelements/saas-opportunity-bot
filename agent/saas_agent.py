"""
SaaS Opportunity Bot Agent for oTTomator Live Agent Studio
Conversational AI agent that scans and analyzes SaaS opportunities from Hacker News.
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
from anyio import to_thread

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="SaaS Opportunity Bot Agent",
    description="AI agent that scans Hacker News for SaaS opportunities in high-value industries",
    version="1.0.0"
)
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scanner components imported lazily in functions to avoid startup crashes
# from scrapers.hn_scraper import scan_hacker_news
# from config import INDUSTRIES, PAIN_SIGNALS


def get_scanner_components():
    """Lazy load scanner components to avoid import failures at startup."""
    from scrapers.hn_scraper import scan_hacker_news
    from config import INDUSTRIES, PAIN_SIGNALS
    return scan_hacker_news, INDUSTRIES, PAIN_SIGNALS


# Request/Response Models (ottomator standard)
class AgentRequest(BaseModel):
    query: str
    user_id: str
    request_id: str
    session_id: str


class AgentResponse(BaseModel):
    success: bool


# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    """Verify the bearer token against environment variable."""
    expected_token = os.getenv("API_BEARER_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=500, detail="API_BEARER_TOKEN not set")
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return True


async def call_llm(system_prompt: str, user_message: str, context: str = "") -> str:
    """Call OpenAI API to generate response."""
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY not configured. Please set your API key."
    
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    if context:
        messages.append({"role": "assistant", "content": f"Context from previous analysis:\n{context}"})
    messages.append({"role": "user", "content": user_message})
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LLM_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
        
        if response.status_code != 200:
            return f"LLM Error: {response.text}"
        
        data = response.json()
        return data["choices"][0]["message"]["content"]


def score_opportunity(opp: dict) -> int:
    """Score an opportunity based on various factors."""
    score = 0
    score += len(opp.get("pain_signals", [])) * 10
    score += len(opp.get("industries", [])) * 5
    
    post_score = opp.get("score", 0)
    if post_score > 100:
        score += 20
    elif post_score > 50:
        score += 10
    elif post_score > 10:
        score += 5
    
    num_comments = opp.get("num_comments", 0)
    if num_comments > 50:
        score += 15
    elif num_comments > 20:
        score += 10
    elif num_comments > 5:
        score += 5
    
    return score


def run_scan(industry_filter: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """Run the HN scanner and return opportunities."""
    scan_hacker_news, _, _ = get_scanner_components()
    opportunities = []
    
    for opp in scan_hacker_news():
        opp["priority_score"] = score_opportunity(opp)
        
        # Apply industry filter if specified
        if industry_filter:
            if industry_filter.lower() not in [i.lower() for i in opp.get("industries", [])]:
                continue
        
        opportunities.append(opp)
        
        if len(opportunities) >= limit * 3:  # Get extra to filter/sort
            break
    
    # Sort by priority score
    opportunities.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
    return opportunities[:limit]


def format_opportunities(opportunities: List[Dict], limit: int = 10) -> str:
    """Format opportunities for display."""
    if not opportunities:
        return "No opportunities found matching your criteria."
    
    lines = [f"Found {len(opportunities)} opportunities:\n"]
    
    for i, opp in enumerate(opportunities[:limit], 1):
        lines.append(f"**#{i} [Score: {opp['priority_score']}]**")
        lines.append(f"📌 {opp['title']}")
        if opp.get('text'):
            lines.append(f"   {opp['text'][:200]}...")
        lines.append(f"🔍 Signals: {', '.join(opp['pain_signals'][:3])}")
        if opp['industries']:
            lines.append(f"🏢 Industries: {', '.join(opp['industries'])}")
        lines.append(f"🔗 {opp['url']}")
        lines.append("")
    
    return "\n".join(lines)


def get_industry_summary(opportunities: List[Dict]) -> str:
    """Get industry breakdown."""
    industry_counts = {}
    for opp in opportunities:
        for ind in opp.get("industries", []):
            industry_counts[ind] = industry_counts.get(ind, 0) + 1
    
    if not industry_counts:
        return "No industry-specific opportunities found."
    
    lines = ["**Industry Breakdown:**"]
    for ind, count in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  • {ind}: {count} opportunities")
    return "\n".join(lines)


def parse_user_intent(query: str) -> Dict[str, Any]:
    """Parse user query to determine intent."""
    _, INDUSTRIES, _ = get_scanner_components()
    query_lower = query.lower()
    
    intent = {
        "action": "scan",  # scan, analyze, explain, list
        "industry_filter": None,
        "limit": 10
    }
    
    # Check for specific actions
    if any(word in query_lower for word in ["analyze", "analysis", "insights", "summarize", "summary"]):
        intent["action"] = "analyze"
    elif any(word in query_lower for word in ["explain", "what is", "how does", "help"]):
        intent["action"] = "explain"
    elif any(word in query_lower for word in ["list industries", "what industries", "available industries"]):
        intent["action"] = "list_industries"
    elif any(word in query_lower for word in ["list signals", "what signals", "pain signals"]):
        intent["action"] = "list_signals"
    
    # Check for industry filter
    for industry in INDUSTRIES.keys():
        if industry.lower().replace("_", " ") in query_lower or industry.lower() in query_lower:
            intent["industry_filter"] = industry
            break
    
    # Check for limit
    for word in query_lower.split():
        if word.isdigit():
            intent["limit"] = min(int(word), 50)
            break
    
    return intent


# In-memory cache for scan results (per session)
scan_cache: Dict[str, List[Dict]] = {}


async def process_query(query: str, session_id: str) -> str:
    """Process user query and return response."""
    intent = parse_user_intent(query)
    
    # Handle different intents
    if intent["action"] == "explain":
        return """**SaaS Opportunity Bot** 🚀

I scan Hacker News for pain points that indicate SaaS opportunities in high-value industries.

**What I look for:**
• Pain signals like "I wish there was...", "I'd pay for...", "so frustrating"
• Industries: Finance, Legal, Healthcare, Real Estate, SaaS/B2B, Agencies, E-commerce, Developers

**Commands you can try:**
• "Scan for opportunities" - Run a fresh scan
• "Find fintech opportunities" - Filter by industry
• "Analyze the top 10" - Get AI insights
• "Show me healthcare pain points" - Industry-specific scan
• "List industries" - See all tracked industries
• "List signals" - See pain point signals I detect"""
    
    if intent["action"] == "list_industries":
        _, INDUSTRIES, _ = get_scanner_components()
        lines = ["**Tracked Industries:**"]
        for industry, keywords in INDUSTRIES.items():
            lines.append(f"• **{industry.replace('_', ' ').title()}**: {', '.join(keywords[:5])}...")
        return "\n".join(lines)
    
    if intent["action"] == "list_signals":
        _, _, PAIN_SIGNALS = get_scanner_components()
        lines = ["**Pain Point Signals I Detect:**"]
        for i, signal in enumerate(PAIN_SIGNALS, 1):
            lines.append(f"{i}. \"{signal}\"")
        return "\n".join(lines)
    
    # Run scan (offload to thread to avoid blocking event loop)
    print(f"Running scan with filter: {intent['industry_filter']}, limit: {intent['limit']}")
    opportunities = await to_thread.run_sync(
        run_scan,
        intent["industry_filter"],
        intent["limit"]
    )
    
    # Cache results for this session
    scan_cache[session_id] = opportunities
    
    if intent["action"] == "analyze":
        # Use LLM to analyze opportunities
        if not opportunities:
            return "No opportunities found to analyze. Try running a scan first."
        
        opp_summary = json.dumps([{
            "title": o["title"],
            "text": o.get("text", "")[:300],
            "pain_signals": o["pain_signals"],
            "industries": o["industries"],
            "score": o["priority_score"],
            "url": o["url"]
        } for o in opportunities[:15]], indent=2)
        
        system_prompt = """You are a SaaS opportunity analyst. Analyze the following pain points found on Hacker News and provide:
1. Top 3-5 most promising SaaS ideas based on these pain points
2. Market size potential (small/medium/large)
3. Competition level (low/medium/high based on your knowledge)
4. Quick MVP suggestion for the top opportunity

Be specific, actionable, and entrepreneurial. Format with markdown."""
        
        analysis = await call_llm(system_prompt, f"Analyze these opportunities:\n{opp_summary}")
        
        return f"""**AI Analysis of {len(opportunities)} Opportunities**

{analysis}

---
*Based on live scan of Hacker News*"""
    
    # Default: show scan results
    result = format_opportunities(opportunities, intent["limit"])
    result += "\n\n" + get_industry_summary(opportunities)
    result += "\n\n💡 *Say \"analyze\" for AI insights on these opportunities*"
    
    return result


# Supabase integration (optional - for conversation history)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase_client = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("Supabase client initialized")
    except ImportError:
        print("Supabase client not installed, conversation history disabled")
    except Exception as e:
        print(f"Supabase initialization failed ({e}), conversation history disabled")
        supabase_client = None


async def store_message(session_id: str, message_type: str, content: str, data: Optional[Dict] = None):
    """Store a message in Supabase (if configured)."""
    if not supabase_client:
        return
    
    message_obj = {"type": message_type, "content": content}
    if data:
        message_obj["data"] = data
    
    try:
        supabase_client.table("messages").insert({
            "session_id": session_id,
            "message": message_obj
        }).execute()
    except Exception as e:
        print(f"Failed to store message: {e}")


@app.post("/api/saas-opportunity-agent", response_model=AgentResponse)
async def saas_opportunity_agent(
    request: AgentRequest,
    authenticated: bool = Depends(verify_token)
):
    """Main agent endpoint for ottomator Live Agent Studio."""
    try:
        # Store user's query
        await store_message(
            session_id=request.session_id,
            message_type="human",
            content=request.query
        )
        
        # Process query and get response
        agent_response = await process_query(request.query, request.session_id)
        
        # Store agent's response
        await store_message(
            session_id=request.session_id,
            message_type="ai",
            content=agent_response,
            data={"request_id": request.request_id}
        )
        
        return AgentResponse(success=True)
        
    except Exception as e:
        print(f"Error processing request: {e}")
        await store_message(
            session_id=request.session_id,
            message_type="ai",
            content=f"I encountered an error: {str(e)}",
            data={"error": str(e), "request_id": request.request_id}
        )
        return AgentResponse(success=False)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "saas-opportunity-bot"}


@app.get("/")
async def root():
    """Root endpoint with agent info."""
    return {
        "name": "SaaS Opportunity Bot",
        "version": "1.0.0",
        "description": "Scans Hacker News for SaaS opportunities in high-value industries",
        "endpoint": "/api/saas-opportunity-agent"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
