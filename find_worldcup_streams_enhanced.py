#!/usr/bin/env python3
"""
Enhanced World Cup 2026 Live Stream Finder
Scrapes multiple sources to find live streaming links for matches.
"""

import re
import sys
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin

try:
    from googlesearch import search
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("Warning: googlesearch module not available. Install with: pip install googlesearch-python", file=sys.stderr)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }

def search_google(query, num=20):
    """Perform Google search and return list of URLs."""
    if not GOOGLE_AVAILABLE:
        return []
    try:
        results = list(search(query, num_results=num, user_agent=get_headers()['User-Agent']))
        return results
    except Exception as e:
        print(f"Google search error: {e}", file=sys.stderr)
        return []

def extract_streaming_links_from_page(url):
    """Extract potential streaming links from a given page."""
    try:
        resp = requests.get(url, headers=get_headers(), timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = set()
        
        # Look for iframes (common for stream embeds)
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src'].strip()
            if src.startswith('http'):
                links.add(src)
        
        # Look for anchor tags with streaming keywords
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href.startswith('http'):
                href = urljoin(url, href)
            text = a.get_text().lower()
            # Keywords indicating stream links
            if any(k in text or k in href.lower() for k in ['stream', 'live', 'watch', 'click', 'link', 'game', 'match']):
                if 'youtube.com' in href or 'twitch.tv' in href or any(domain in href for domain in ['stream', 'live', 'tv', 'sport', 'football']):
                    links.add(href)
        
        # Also search for embed URLs in script tags (simple regex)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                matches = re.findall(r'https?://[^\s"\']+\.(?:m3u8|mp4|ts|m3u)', script.string)
                for m in matches:
                    links.add(m)
        
        return list(links)
    except Exception as e:
        print(f"Error scraping {url}: {e}", file=sys.stderr)
        return []

def search_stream_aggregators():
    """Directly scrape known stream aggregator sites."""
    aggregators = [
        "https://www.sportsurge.net/",
        "https://hesgoal.pro/",
        "https://livetv.sx/",
        "https://www.totalsportek.com/football/",
        "https://weakspell.to/football",
        "https://reddit.soccerstreams.net/",
        "https://www.stream2watch.sx/",
        "https://www.viprow.nu/soccer-streams",
    ]
    all_links = []
    for site in aggregators:
        print(f"Checking aggregator: {site}")
        links = extract_streaming_links_from_page(site)
        if links:
            all_links.extend(links)
        time.sleep(1)  # polite delay
    return list(set(all_links))

def search_reddit_streams():
    """Search Reddit for stream links."""
    queries = [
        "world cup 2026 live stream site:reddit.com",
        "world cup 2026 stream site:reddit.com",
        "soccer streams world cup 2026 site:reddit.com",
    ]
    found = []
    for q in queries:
        urls = search_google(q, num=10)
        for url in urls:
            # Fetch Reddit post and look for stream links in comments (simplified)
            if 'reddit.com' in url:
                try:
                    resp = requests.get(url + '.json', headers=get_headers(), timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        # Extract links from post body and comments
                        # This is complex; simplified: just return the URL itself
                        found.append(url)
                except:
                    pass
        time.sleep(1)
    return list(set(found))

def search_twitter_streams():
    """Search Twitter for live stream links."""
    # Twitter search is limited; we'll just do a Google site search
    query = 'site:twitter.com "world cup 2026" live stream'
    urls = search_google(query, num=15)
    return [u for u in urls if 'twitter.com' in u]

def get_official_broadcasters():
    """Fetch official broadcaster list from FIFA (example)."""
    # FIFA broadcasters page
    official_url = "https://www.fifa.com/fifaplus/en/watch/broadcasters"
    try:
        resp = requests.get(official_url, headers=get_headers(), timeout=15)
        if resp.status_code == 200:
            # Parse for broadcaster links
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Extract all external links (could be broadcaster sites)
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http') and 'fifa.com' not in href:
                    links.append(href)
            return links[:20]
    except:
        pass
    return []

def main():
    print("="*60)
    print("World Cup 2026 Live Stream Finder (Enhanced)")
    print("Searching for live streaming links...")
    print("="*60)
    
    all_streams = []
    
    # Method 1: Google searches with specific queries
    print("\n[1] Searching Google with targeted queries...")
    queries = [
        "world cup 2026 live stream free",
        "world cup 2026 live streaming",
        "watch world cup 2026 live online",
        "world cup 2026 live reddit",
    ]
    for q in queries:
        print(f"  Query: {q}")
        urls = search_google(q, num=10)
        for url in urls:
            # Filter out known non-stream domains
            if any(domain in url for domain in ['youtube.com', 'twitch.tv', 'facebook.com', 'fifa.com', 'espn.com', 'bbc.com', 'sky.com']):
                all_streams.append(url)
        time.sleep(1)
    
    # Method 2: Stream aggregator sites
    print("\n[2] Scanning known stream aggregator sites...")
    agg_links = search_stream_aggregators()
    all_streams.extend(agg_links)
    
    # Method 3: Reddit
    print("\n[3] Searching Reddit for stream threads...")
    reddit_links = search_reddit_streams()
    all_streams.extend(reddit_links)
    
    # Method 4: Twitter
    print("\n[4] Searching Twitter for stream links...")
    twitter_links = search_twitter_streams()
    all_streams.extend(twitter_links)
    
    # Method 5: Official broadcasters (legal)
    print("\n[5] Fetching official broadcasters...")
    official = get_official_broadcasters()
    all_streams.extend(official)
    
    # Deduplicate and filter
    unique_streams = []
    seen = set()
    for s in all_streams:
        if s not in seen:
            seen.add(s)
            unique_streams.append(s)
    
    # Filter out obviously broken or irrelevant URLs
    filtered = []
    for s in unique_streams:
        # Skip common non-stream domains
        if any(bad in s for bad in ['google.com', 'bing.com', 'yandex', 'duckduckgo']):
            continue
        filtered.append(s)
    
    # Display results
    print("\n" + "="*60)
    if filtered:
        print(f"Found {len(filtered)} potential streaming links:\n")
        for idx, link in enumerate(filtered, 1):
            print(f"{idx}. {link}")
    else:
        print("No streaming links found. Try running again later or use official broadcasters.")
    
    print("\nNote: Some links may require VPN or may be geo-restricted.")
    print("For legal streams, check local broadcasters.")

if __name__ == '__main__':
    main()
