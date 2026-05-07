# High-Performance Async Proxy Scraper & Checker

A fast, asynchronous Python script that scrapes proxies from multiple public sources, validates their functionality and speed, and saves only the elite/fast working proxies.

## Features

- **Multi-Source Scraping**: Collects from 4+ sources (ProxyScrape, Free-Proxy-List, GitHub lists, OpenProxy)
- **Async Performance**: Uses aiohttp for concurrent scraping and checking (100 concurrent checks)
- **Speed Filtering**: Only saves proxies responding in under 2000ms
- **Progress Tracking**: Real-time tqdm progress bar during checking
- **Detailed Output**: Saves both simple list and detailed JSON with speed metrics
- **Smart Validation**: Tests against httpbin.org/ip for reliable verification

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python proxy_scraper_checker.py
```

## Output Files

1. **verified_proxies.txt** - Clean list of working proxies in `ip:port` format
2. **verified_proxies_detailed.json** - Detailed info including:
   - Proxy address
   - Response time (ms)
   - Speed category (Elite/Fast/Medium)

## Performance Metrics

The script displays:
- `[Total Scraped]` - Unique proxies collected
- `[Checking...]` - Real-time progress with tqdm
- `[Found Working]` - Fast, functional proxies
- Success rate and elapsed time

## Configuration

You can adjust these parameters in the `ProxyManager.__init__()` method:

- `max_concurrent`: Number of parallel checks (default: 100)
- `timeout`: Connection timeout in seconds (default: 5)
- `max_response_time`: Maximum acceptable response time in seconds (default: 2.0)

## Example Output

```
============================================================
HIGH-PERFORMANCE PROXY SCRAPER & CHECKER
============================================================

[Phase 1] Scraping proxies from multiple sources...
[Total Scraped] 1547 unique proxies

[Phase 2] Checking proxy speed and functionality...
Checking proxies: 100%|████████████| 1547/1547 [02:34<00:00, 10.04proxy/s]

[Found Working] 89 fast proxies (<2000ms)

[Phase 3] Saving verified proxies...

============================================================
SUMMARY
============================================================
Total Scraped:    1547
Working & Fast:   89
Success Rate:     5.75%
Time Elapsed:     187.43s
Output File:      verified_proxies.txt
============================================================
```

## Speed Categories

- **Elite**: < 500ms response time
- **Fast**: 500-1000ms response time
- **Medium**: 1000-2000ms response time

## Notes

- Free proxies have high turnover rates, so success rates vary
- Run during off-peak hours for better results
- Proxies are automatically deduplicated
- The script handles errors gracefully and continues even if some sources fail
