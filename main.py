"""
SaaS Opportunity Bot
Scans Reddit and Hacker News for pain points in high-value industries.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

from scrapers.reddit_scraper import scan_reddit
from scrapers.hn_scraper import scan_hacker_news
from config import OUTPUT_DIR


def score_opportunity(opp: dict) -> int:
    """Score an opportunity based on various factors"""
    score = 0
    
    # More pain signals = higher score
    score += len(opp.get("pain_signals", [])) * 10
    
    # Industry relevance
    score += len(opp.get("industries", [])) * 5
    
    # Engagement (upvotes/score)
    post_score = opp.get("score", 0)
    if post_score > 100:
        score += 20
    elif post_score > 50:
        score += 10
    elif post_score > 10:
        score += 5
    
    # Comments indicate discussion
    num_comments = opp.get("num_comments", 0)
    if num_comments > 50:
        score += 15
    elif num_comments > 20:
        score += 10
    elif num_comments > 5:
        score += 5
    
    return score


def save_results(opportunities: list[dict], output_dir: str = OUTPUT_DIR):
    """Save results to CSV and JSON"""
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as CSV
    csv_path = Path(output_dir) / f"opportunities_{timestamp}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if opportunities:
            writer = csv.DictWriter(f, fieldnames=[
                "priority_score", "source", "title", "text", "url", 
                "score", "pain_signals", "industries", "type"
            ])
            writer.writeheader()
            for opp in opportunities:
                row = {
                    **opp,
                    "pain_signals": ", ".join(opp.get("pain_signals", [])),
                    "industries": ", ".join(opp.get("industries", [])),
                }
                writer.writerow(row)
    
    # Save as JSON
    json_path = Path(output_dir) / f"opportunities_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(opportunities, f, indent=2)
    
    return csv_path, json_path


def print_summary(opportunities: list[dict]):
    """Print a summary of findings"""
    print("\n" + "=" * 70)
    print("TOP SAAS OPPORTUNITIES")
    print("=" * 70)
    
    # Sort by priority score
    sorted_opps = sorted(opportunities, key=lambda x: x.get("priority_score", 0), reverse=True)
    
    for i, opp in enumerate(sorted_opps[:20], 1):
        print(f"\n#{i} [Score: {opp['priority_score']}] [{opp['source'].upper()}]")
        print(f"   {opp['title'][:70]}")
        print(f"   Signals: {', '.join(opp['pain_signals'][:3])}")
        if opp['industries']:
            print(f"   Industries: {', '.join(opp['industries'])}")
        print(f"   URL: {opp['url']}")
    
    # Industry summary
    print("\n" + "=" * 70)
    print("INDUSTRY BREAKDOWN")
    print("=" * 70)
    industry_counts = {}
    for opp in opportunities:
        for ind in opp.get("industries", []):
            industry_counts[ind] = industry_counts.get(ind, 0) + 1
    
    for ind, count in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ind}: {count} opportunities")


def main():
    print("=" * 70)
    print("SAAS OPPORTUNITY BOT")
    print("Finding pain points in high-value industries...")
    print("=" * 70)
    
    all_opportunities = []
    
    # Scan Reddit
    try:
        for opp in scan_reddit():
            opp["priority_score"] = score_opportunity(opp)
            all_opportunities.append(opp)
            print(f"  Found: {opp['title'][:50]}...")
    except KeyboardInterrupt:
        print("\nReddit scan interrupted, continuing with HN...")
    except Exception as e:
        print(f"Reddit error: {e}")
    
    # Scan Hacker News
    try:
        for opp in scan_hacker_news():
            opp["priority_score"] = score_opportunity(opp)
            all_opportunities.append(opp)
            print(f"  Found: {opp['title'][:50]}...")
    except KeyboardInterrupt:
        print("\nHN scan interrupted...")
    except Exception as e:
        print(f"HN error: {e}")
    
    if all_opportunities:
        # Save results
        csv_path, json_path = save_results(all_opportunities)
        print(f"\n✓ Saved {len(all_opportunities)} opportunities to:")
        print(f"  - {csv_path}")
        print(f"  - {json_path}")
        
        # Print summary
        print_summary(all_opportunities)
    else:
        print("\nNo opportunities found. Try adjusting config.py")


if __name__ == "__main__":
    main()
