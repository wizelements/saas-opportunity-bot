"""Hacker News scraper using official API"""

import requests
from typing import Generator
from config import PAIN_SIGNALS, INDUSTRIES, HN_STORIES_TO_CHECK, HN_MIN_COMMENTS


HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


def get_top_stories(limit: int = HN_STORIES_TO_CHECK) -> list[int]:
    """Get IDs of top stories"""
    try:
        response = requests.get(f"{HN_API_BASE}/topstories.json", timeout=10)
        response.raise_for_status()
        return response.json()[:limit]
    except Exception as e:
        print(f"Error fetching top stories: {e}")
        return []


def get_new_stories(limit: int = HN_STORIES_TO_CHECK) -> list[int]:
    """Get IDs of new stories"""
    try:
        response = requests.get(f"{HN_API_BASE}/newstories.json", timeout=10)
        response.raise_for_status()
        return response.json()[:limit]
    except Exception as e:
        print(f"Error fetching new stories: {e}")
        return []


def get_ask_stories(limit: int = 50) -> list[int]:
    """Get IDs of Ask HN stories (often contain pain points)"""
    try:
        response = requests.get(f"{HN_API_BASE}/askstories.json", timeout=10)
        response.raise_for_status()
        return response.json()[:limit]
    except Exception as e:
        print(f"Error fetching ask stories: {e}")
        return []


def get_item(item_id: int) -> dict:
    """Get a single HN item (story or comment)"""
    try:
        response = requests.get(f"{HN_API_BASE}/item/{item_id}.json", timeout=10)
        response.raise_for_status()
        return response.json() or {}
    except Exception as e:
        print(f"Error fetching item {item_id}: {e}")
        return {}


def get_comments(story: dict, max_depth: int = 2, current_depth: int = 0) -> list[dict]:
    """Recursively get comments for a story"""
    comments = []
    kids = story.get("kids", [])
    
    for kid_id in kids[:20]:  # Limit to first 20 comments per level
        comment = get_item(kid_id)
        if comment and comment.get("type") == "comment" and not comment.get("deleted"):
            comments.append(comment)
            if current_depth < max_depth:
                comments.extend(get_comments(comment, max_depth, current_depth + 1))
    
    return comments


def contains_pain_signal(text: str) -> tuple[bool, list[str]]:
    """Check if text contains pain point signals"""
    if not text:
        return False, []
    text_lower = text.lower()
    found_signals = []
    for signal in PAIN_SIGNALS:
        if signal.lower() in text_lower:
            found_signals.append(signal)
    return len(found_signals) > 0, found_signals


def identify_industry(text: str) -> list[str]:
    """Identify which industries the text relates to"""
    if not text:
        return []
    text_lower = text.lower()
    found_industries = []
    for industry, keywords in INDUSTRIES.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found_industries.append(industry)
                break
    return found_industries


def scan_hacker_news() -> Generator[dict, None, None]:
    """Scan Hacker News for SaaS opportunities"""
    print("Scanning Hacker News...")
    
    # Combine different story sources
    story_ids = set()
    story_ids.update(get_top_stories())
    story_ids.update(get_new_stories())
    story_ids.update(get_ask_stories())
    
    print(f"  Checking {len(story_ids)} stories...")
    
    for story_id in story_ids:
        story = get_item(story_id)
        if not story:
            continue
        
        title = story.get("title", "")
        text = story.get("text", "")  # For Ask HN posts
        full_text = f"{title} {text}"
        
        has_pain, signals = contains_pain_signal(full_text)
        industries = identify_industry(full_text)
        
        # Check the story itself
        if has_pain:
            yield {
                "source": "hackernews",
                "title": title,
                "text": text[:500] if text else "",
                "url": f"https://news.ycombinator.com/item?id={story_id}",
                "score": story.get("score", 0),
                "num_comments": story.get("descendants", 0),
                "pain_signals": signals,
                "industries": industries,
                "type": "story",
            }
        
        # Check comments if story has enough engagement
        if story.get("descendants", 0) >= HN_MIN_COMMENTS:
            comments = get_comments(story)
            for comment in comments:
                comment_text = comment.get("text", "")
                has_pain, signals = contains_pain_signal(comment_text)
                
                if has_pain:
                    yield {
                        "source": "hackernews",
                        "title": f"Comment on: {title[:50]}",
                        "text": comment_text[:500] if comment_text else "",
                        "url": f"https://news.ycombinator.com/item?id={comment.get('id')}",
                        "score": 0,  # HN comments don't show score
                        "pain_signals": signals,
                        "industries": identify_industry(comment_text),
                        "type": "comment",
                    }


if __name__ == "__main__":
    for opportunity in scan_hacker_news():
        print(f"\n{'='*60}")
        print(f"[HN] {opportunity['title']}")
        print(f"Signals: {opportunity['pain_signals']}")
        print(f"Industries: {opportunity['industries']}")
        print(f"URL: {opportunity['url']}")
