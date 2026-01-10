"""Reddit scraper using public JSON API (no auth required)"""

import requests
import time
from typing import Generator
import sys
sys.path.append('..')
from config import SUBREDDITS, PAIN_SIGNALS, INDUSTRIES


def get_subreddit_posts(subreddit: str, limit: int = 50) -> list[dict]:
    """Fetch recent posts from a subreddit using public JSON API"""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {"User-Agent": "SaaSOpportunityBot/1.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("children", [])
    except Exception as e:
        print(f"Error fetching r/{subreddit}: {e}")
        return []


def get_post_comments(permalink: str, limit: int = 100) -> list[dict]:
    """Fetch comments for a specific post"""
    url = f"https://www.reddit.com{permalink}.json?limit={limit}"
    headers = {"User-Agent": "SaaSOpportunityBot/1.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if len(data) > 1:
            return extract_comments(data[1].get("data", {}).get("children", []))
        return []
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []


def extract_comments(children: list, depth: int = 0) -> list[dict]:
    """Recursively extract comments from nested structure"""
    comments = []
    for child in children:
        if child.get("kind") == "t1":
            data = child.get("data", {})
            comments.append({
                "body": data.get("body", ""),
                "score": data.get("score", 0),
                "author": data.get("author", ""),
            })
            # Get replies
            replies = data.get("replies")
            if isinstance(replies, dict):
                reply_children = replies.get("data", {}).get("children", [])
                comments.extend(extract_comments(reply_children, depth + 1))
    return comments


def contains_pain_signal(text: str) -> tuple[bool, list[str]]:
    """Check if text contains pain point signals"""
    text_lower = text.lower()
    found_signals = []
    for signal in PAIN_SIGNALS:
        if signal.lower() in text_lower:
            found_signals.append(signal)
    return len(found_signals) > 0, found_signals


def identify_industry(text: str) -> list[str]:
    """Identify which industries the text relates to"""
    text_lower = text.lower()
    found_industries = []
    for industry, keywords in INDUSTRIES.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found_industries.append(industry)
                break
    return found_industries


def scan_reddit() -> Generator[dict, None, None]:
    """Scan Reddit for SaaS opportunities"""
    print("Scanning Reddit...")
    
    for subreddit in SUBREDDITS:
        print(f"  Checking r/{subreddit}...")
        posts = get_subreddit_posts(subreddit)
        
        for post in posts:
            data = post.get("data", {})
            title = data.get("title", "")
            selftext = data.get("selftext", "")
            permalink = data.get("permalink", "")
            full_text = f"{title} {selftext}"
            
            has_pain, signals = contains_pain_signal(full_text)
            industries = identify_industry(full_text)
            
            if has_pain:
                yield {
                    "source": "reddit",
                    "subreddit": subreddit,
                    "title": title,
                    "text": selftext[:500] if selftext else "",
                    "url": f"https://reddit.com{permalink}",
                    "score": data.get("score", 0),
                    "num_comments": data.get("num_comments", 0),
                    "pain_signals": signals,
                    "industries": industries,
                    "type": "post",
                }
            
            # Check comments for pain signals
            if data.get("num_comments", 0) > 5:
                comments = get_post_comments(permalink)
                for comment in comments:
                    body = comment.get("body", "")
                    has_pain, signals = contains_pain_signal(body)
                    if has_pain and comment.get("score", 0) >= 3:
                        yield {
                            "source": "reddit",
                            "subreddit": subreddit,
                            "title": f"Comment on: {title[:50]}",
                            "text": body[:500],
                            "url": f"https://reddit.com{permalink}",
                            "score": comment.get("score", 0),
                            "pain_signals": signals,
                            "industries": identify_industry(body),
                            "type": "comment",
                        }
                time.sleep(1)  # Rate limiting
        
        time.sleep(2)  # Rate limiting between subreddits


if __name__ == "__main__":
    for opportunity in scan_reddit():
        print(f"\n{'='*60}")
        print(f"[{opportunity['subreddit']}] {opportunity['title']}")
        print(f"Signals: {opportunity['pain_signals']}")
        print(f"Industries: {opportunity['industries']}")
        print(f"URL: {opportunity['url']}")
