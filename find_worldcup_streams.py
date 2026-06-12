#!/usr/bin/env python3
"""
World Cup 2026 Live Stream Finder
Searches for live streaming links for the 2026 FIFA World Cup matches.
Uses web scraping and search engine queries to find publicly available streams.
"""

import argparse
import re
import sys
import time
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

# Try to import google search module (optional)
try:
    from googlesearch import search
except ImportError:
    search = None

# User-Agent rotation to avoid blocking
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
]


def get_headers():
    """Return headers with random User-Agent."""
    import random
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }


def search_google(query, num_results=10):
    """
    Perform Google search and return list of result URLs.
    Falls back to a simple fetch if googlesearch module is not available.
    """
    if search:
        try:
            return list(search(query, num_results=num_results, user_agent=get_headers()['User-Agent']))
        except Exception as e:
            print(f"Google search error: {e}", file=sys.stderr)
            return []
    else:
        # Fallback: use a custom Google search using requests (less reliable)
        return google_search_fallback(query, num_results)


def google_search_fallback(query, num_results=10):
    """Fallback Google search using requests and parsing HTML (basic)."""
    url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/url?q='):
                match = re.search(r'/url\?q=(https?://[^&]+)', href)
                if match:
                    link = match.group(1)
                    if not any(skip in link for skip in ['google.com', 'youtube.com']):
                        links.append(link)
            if len(links) >= num_results:
                break
        return links
    except Exception as e:
        print(f"Fallback search error: {e}", file=sys.stderr)
        return []


def extract_links_from_page(url, keywords=None):
    """
    Extract all hyperlinks from a page, optionally filtering by keywords.
    Returns list of unique absolute URLs.
    """
    try:
        resp = requests.get(url, headers=get_headers(), timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href.startswith('/'):
                # Convert relative to absolute
                from urllib.parse import urljoin
                href = urljoin(url, href)
            if href.startswith('http') and '#' not in href:
                if keywords:
                    if any(k.lower() in href.lower() or (a.text and k.lower() in a.text.lower()) for k in keywords):
                        links.add(href)
                else:
                    links.add(href)
        return list(links)
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return []


def find_streams_for_match(team1, team2=None, date=None):
    """
    Search for streaming links for a specific match.
    """
    if team2:
        query = f"{team1} vs {team2} World Cup 2026 live stream"
    else:
        query = f"{team1} World Cup 2026 live stream"
    if date:
        query += f" {date}"
    
    print(f"Searching for: {query}")
    urls = search_google(query, num_results=15)
    
    streaming_links = []
    # Known streaming site patterns
    stream_patterns = re.compile(r'stream|live|watch|tv|football|soccer', re.I)
    
    for url in urls:
        if stream_patterns.search(url):
            # Optionally fetch page to find embedded links
            streaming_links.append(url)
    
    return streaming_links


def find_official_broadcasters():
    """
    Fetch official broadcasters list from FIFA website (example).
    """
    url = "https://www.fifa.com/fifaplus/en/watch/broadcasters"
    print(f"Fetching official broadcasters from {url}")
    try:
        resp = requests.get(url, headers=get_headers(), timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # This is a generic extraction; actual structure may differ
        broadcasters = []
        # Look for elements containing broadcaster info
        for elem in soup.find_all(['a', 'div'], text=True):
            text = elem.get_text(strip=True)
            if 'broadcaster' in text.lower() or 'channel' in text.lower():
                if elem.name == 'a' and elem.get('href'):
                    broadcasters.append(elem['href'])
        return broadcasters
    except Exception as e:
        print(f"Error fetching official broadcasters: {e}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser(description='Find World Cup 2026 live stream links.')
    parser.add_argument('--team', help='Team name to search for')
    parser.add_argument('--opponent', help='Opponent team name (optional)')
    parser.add_argument('--date', help='Match date (YYYY-MM-DD)')
    parser.add_argument('--official', action='store_true', help='Get official broadcasters list')
    parser.add_argument('--num', type=int, default=10, help='Number of results to return')
    args = parser.parse_args()
    
    if args.official:
        links = find_official_broadcasters()
        if links:
            print("\nOfficial broadcasters / streaming sources:")
            for link in links:
                print(f"  {link}")
        else:
            print("No official broadcaster links found.")
        return
    
    if not args.team:
        print("Error: Please provide a team name using --team, or use --official flag.")
        sys.exit(1)
    
    streams = find_streams_for_match(args.team, args.opponent, args.date)
    
    if streams:
        print(f"\nFound {len(streams)} potential streaming links:")
        for idx, link in enumerate(streams[:args.num], 1):
            print(f"{idx}. {link}")
    else:
        print("No streaming links found. Try a different search or use --official for legal broadcasters.")
    
    # Additional: suggest using official broadcasters
    print("\nTip: For legal streams, check official broadcasters with --official flag.")


if __name__ == '__main__':
    main()
