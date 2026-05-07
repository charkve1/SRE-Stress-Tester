# Advanced SRE Load Testing & Observability Engine

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-FF4B4B?style=for-the-badge&logo=streamlit)
![aiohttp](https://img.shields.io/badge/aiohttp-3.9.0-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-Educational-yellow?style=for-the-badge)

###  High-Performance Infrastructure Resilience Testing Framework

This repository contains a professional-grade **System Reliability Engineering (SRE)** tool engineered to discover the **"Safe Operating Envelope"** of web services and backend infrastructure. By leveraging high-density, heterogeneous traffic simulation, it empowers engineers to map exact degradation points and test the true limits of connection pooling, load balancers, and auto-scaling logic.

---

## ⚠️ LEGAL DISCLAIMER & ETHICAL WARNING

> **CRITICAL NOTICE:** This software is published strictly for **educational research** and **authorized security auditing**.
> 
> Due to its highly optimized asynchronous architecture, connection stressor modules, and proxy rotation capabilities, this tool generates massive volumetric traffic. If misused, it can easily function as a **Distributed Denial of Service (DDoS)** weapon.
>
> **The author assumes ABSOLUTELY NO LIABILITY for any unauthorized, malicious, or illegal use of this software.** Any damage, service disruption, or legal consequences resulting from its deployment are solely the responsibility of the end-user. By cloning, downloading, or running this code, you explicitly agree to deploy it **ONLY on infrastructure you own or have explicit, documented authorization to test.**

---

## System Architecture & Core Modules

This engine bypasses standard synthetic traffic filters by dynamically mimicking real-world browser behavior and utilizing advanced concurrency controls.

### 1. Asynchronous Networking Core (`aiohttp` & `asyncio`)
Built to sustain thousands of concurrent connections with minimal CPU overhead.
* **Handshake Storm Mode:** Forces full TCP handshakes on every request to stress-test server connection limits.
* **Persistence Analysis:** Maintains long-lived, low-throughput sessions to validate keep-alive timeouts and worker pool exhaustion thresholds.

### 2. Adaptive Ramp Engine (PID-style Feedback Loop)
Unlike traditional brute-force tools, this framework intelligently scales load:
* **Latency-Aware Adjustments:** Continuously monitors P95 latency. If response times exceed acceptable thresholds (e.g., >500ms), the engine dynamically throttles concurrency to find the maximum sustainable throughput without crashing the target.
* **Breaking Point Detection:** Automatically identifies and logs the exact Requests Per Second (RPS) where HTTP 5xx errors emerge or major latency spikes occur.

### 3. High-Entropy Session Randomization
Designed to defeat edge caching and basic WAF fingerprinting:
* **Dynamic Headers:** Procedurally generates valid `User-Agent`, `Sec-Ch-Ua`, `Accept-Language`, and fetch metadata for Chrome, Firefox, Safari, and Edge.
* **Cache Busting:** Injects cryptographic nonces and timestamp query parameters to guarantee raw origin-server hits.

### 4. Advanced Proxy Health Watchdog
A robust sub-system (`proxy_scraper_checker.py`) for geo-distributed load simulation:
* **Automated Scraping & Validation:** Pulls from multiple transparent and anonymous proxy sources, verifying sub-2000ms response times.
* **Intelligent Rotation:** Implements least-recently-used (LRU) algorithms and auto-suspends degraded nodes. Handles 429/403 rate limits via exponential backoff with jitter.

---

## Real-Time Observability (Streamlit)

The framework includes a fully integrated, real-time observability dashboard for live telemetry visualization:
* **Live Latency Timeline:** Granular tracking of successful (2xx), blocked (403/429), and failed (5xx) requests.
* **Throughput Mapping:** Real-time RPS graphing with ramp sequence overlays.
* **Endpoint Complexity Analysis:** Multi-route targeting with weighted traffic distribution to identify which specific API endpoints saturate CPU/RAM first.

---

# Guide

## Enterprise Infrastructure Testing with Adaptive Intelligence

A professional-grade System Reliability Engineering (SRE) testing tool designed for **authorized infrastructure testing** and **academic research** on system resilience.

---

## Quick Start

### Installation

```bash
pip install -r requirements_advanced.txt
```

### Launch

```bash
streamlit run advanced_sre_test.py
```

Dashboard opens at: `http://localhost:8501`

---

## Key Features

### 1. Realistic Traffic Simulation

**Browser-Like Headers:**
- Rotates through 12+ real User-Agent strings (Chrome, Firefox, Safari, Edge)
- Generates complete header profiles including:
  - `Accept-Language` (regional variations)
  - `Sec-Ch-Ua` (Chrome client hints)
  - `Sec-Fetch-*` headers (fetch metadata)
  - `Accept-Encoding` (compression support)
  - `Connection: keep-alive` (persistent connections)

**Why This Matters:**
Tests how your infrastructure handles realistic browser traffic patterns, not synthetic bot traffic.

---

### 2. Advanced Proxy Management

**Health Monitoring:**
- Tracks success rate per proxy
- Detects rate limiting (429, 403 responses)
- Auto-suspends unhealthy proxies for 60 seconds
- Removes proxies after 5 consecutive failures

**Rotation Strategies:**
- **Round-Robin**: Sequential distribution
- **Random**: Stochastic load distribution
- **Weighted**: Prioritizes high-performing proxies

**SOCKS5 Support:**
```
socks5://username:password@192.168.1.100:1080
socks5://10.0.0.50:1080
```

**Proxy File Format:**
```
# HTTP/HTTPS proxies
192.168.1.100:8080
user:pass@203.0.113.10:3128

# SOCKS5 proxies
socks5://user:pass@198.51.100.20:1080
socks5://10.0.0.50:1080
```

---

### 3. Adaptive Concurrency Engine 

**How It Works:**

The system uses a feedback loop inspired by control theory:

```
Measure Latency → Compare to Target → Adjust Concurrency → Repeat
```

**Adjustment Logic:**

| Avg Latency vs Target | Action | Factor |
|----------------------|--------|--------|
| > 2x target | Aggressive reduction | 0.6x |
| > 1.5x target | Moderate reduction | 0.75x |
| > 1x target | Slight reduction | 0.9x |
| < 0.5x target | Increase | 1.3x |
| < 0.7x target | Slight increase | 1.15x |
| Within target | Maintain | 1.0x |

**Example Scenario:**

```
Initial: 100 concurrent, Target: 500ms

Request 1-50: Avg latency 200ms → Increase to 130
Request 51-100: Avg latency 450ms → Maintain at 130
Request 101-150: Avg latency 800ms → Reduce to 97
Request 151-200: Avg latency 300ms → Increase to 126
```

**Configuration:**
- `Target Latency`: Set your acceptable latency threshold (default: 500ms)
- `Adjustment Interval`: How often to recalibrate (default: every 50 requests)
- `Min/Max Concurrency`: Safety bounds (default: 10-1000)

**Why This Is Powerful:**
- Finds your infrastructure's "sweet spot" automatically
- Prevents overwhelming the system during testing
- Identifies the maximum sustainable throughput
- Simulates real-world traffic patterns (not just brute force)

---

### 4. Connection Pool Analysis

**What It Tracks:**
- New connections created
- Connections reused (keep-alive effectiveness)
- Connections closed
- Active connections at any time
- Connection reuse ratio

**Keep-Alive Configuration:**
- `keepalive_timeout`: 30 seconds
- Connection pooling enabled
- Automatic cleanup of stale connections

**Interpreting Results:**

```
High Reuse Ratio (>0.7): Good connection pooling
Low Reuse Ratio (<0.3): Connection churn, potential bottleneck
```

---

### 5. Cache Behavior Analysis

**Automatic Detection:**
- Monitors `X-Cache` headers
- Tracks cache hits vs misses
- Helps identify caching effectiveness under load

**Cache Busting Mode:**
- Adds `Cache-Control: no-cache` headers
- Forces origin server responses
- Tests backend performance without cache assistance

**Use Case:**
Compare test runs with and without cache busting to understand:
- CDN effectiveness
- Cache hit ratio under load
- Origin server capacity

---

### 6. Real-Time Monitoring Dashboard

**Live Metrics Display:**

1. **Response Time Timeline**
   - Green dots: Successful requests (2xx/3xx)
   - Yellow dots: Blocked requests (403/429)
   - Red dots: Error responses (4xx/5xx)
   - Interactive hover for details

2. **RPS Graph**
   - Real-time throughput visualization
   - 1-second aggregation windows
   - Identifies throughput plateaus

3. **Metrics Dashboard**
   - Total requests & success rate
   - Average, P95, P99 latency
   - Blocked request count & rate
   - Current throughput (RPS)

4. **Proxy Statistics** (if using proxies)
   - Healthy/unhealthy proxy count
   - Rate-limited proxies
   - Active proxy pool size

---

## Testing Methodology

### Phase 1: Baseline Assessment

**Goal:** Understand normal performance

```
Configuration:
- Requests: 100
- Concurrency: 10
- Adaptive: ON
- Target Latency: 500ms
- Proxies: OFF

What to observe:
- Baseline latency (P50, P95, P99)
- Success rate (should be ~100%)
- Connection reuse ratio
```

### Phase 2: Load Scaling

**Goal:** Find optimal throughput

```
Configuration:
- Requests: 1000
- Concurrency: 100
- Adaptive: ON
- Target Latency: 500ms

What to observe:
- How concurrency adjusts automatically
- Point where latency exceeds target
- Maximum sustainable RPS
```

### Phase 3: Stress Testing

**Goal:** Identify breaking points

```
Configuration:
- Requests: 5000
- Concurrency: 500
- Adaptive: ON
- Target Latency: 1000ms (relaxed)

What to observe:
- Error rate increases
- Throughput plateaus
- Connection pool exhaustion
- Timeout frequency
```

### Phase 4: Distributed Testing

**Goal:** Test with realistic geographic distribution

```
Configuration:
- Requests: 2000
- Concurrency: 200
- Proxies: 10+ proxies loaded
- Rotation: Weighted

What to observe:
- Proxy health degradation
- Rate limiting behavior
- Geographic latency differences
- Load balancer effectiveness
```

### Phase 5: Cache Analysis

**Goal:** Understand caching behavior

```
Test A (With Cache):
- Cache Busting: OFF
- Observe cache hit ratio

Test B (Without Cache):
- Cache Busting: ON
- Compare to Test A
- Calculate origin server load
```

---

## Key Metrics Explained

### Latency Percentiles

**P50 (Median):**
- 50% of requests are faster than this
- Represents "typical" user experience

**P95:**
- 95% of requests are faster than this
- SLA compliance target for most services

**P99:**
- 99% of requests are faster than this
- Critical for understanding tail latency
- Important for user retention

### Success Rate

```
Success Rate = (2xx + 3xx responses) / Total Requests × 100
```

**Benchmarks:**
- >99%: Excellent
- 95-99%: Good, monitor closely
- 90-95%: Warning, investigate errors
- <90%: Critical, system struggling

### Block Rate

```
Block Rate = (403 + 429 responses) / Total Requests × 100
```

**What It Tells You:**
- WAF/Rate limiter effectiveness
- Whether your infrastructure is protecting itself
- Proxy IP reputation issues

### Throughput (RPS)

```
RPS = Total Requests / Test Duration
```

**Interpretation:**
- Plateau = maximum capacity reached
- Drops = system rejecting connections
- Spikes = batch completion patterns

---

## Interpreting Results

### Healthy System Indicators

✅ Success rate >95%  
✅ P95 latency < target  
✅ Stable RPS (no dramatic drops)  
✅ Low error rate  
✅ Good connection reuse (>0.5)  
✅ Adaptive concurrency stabilizes  

### Warning Signs

⚠️ Success rate declining  
⚠️ P95/P99 spiking above target  
⚠️ Block rate increasing  
⚠️ RPS plateau or dropping  
⚠️ Timeout errors increasing  
⚠️ Connection reuse dropping  

### Critical Issues

❌ Success rate <80%  
❌ Massive timeout spike  
❌ RPS dropped to near zero  
❌ All proxies rate-limited  
❌ Connection pool exhausted  

---

## 💡 Pro Tips for Academic Research

### 1. Document Everything

```
Test Configuration:
- Date/Time
- Infrastructure state
- Network conditions
- Test parameters

Results:
- All metrics
- Observations
- Anomalies
```

### 2. Run Comparative Tests

```
Test Series:
A. Baseline (low load)
B. Medium load
C. High load
D. With proxies
E. Without proxies
F. With cache
G. Without cache

Compare metrics across all tests
```

### 3. Identify Patterns

Look for:
- **Latency curves**: How does latency grow with concurrency?
- **Throughput ceilings**: Where does RPS stop increasing?
- **Error thresholds**: At what load do errors spike?
- **Recovery time**: How quickly does system recover?

### 4. Statistical Analysis

Export results to CSV/JSON for:
- Time-series analysis
- Correlation studies
- Regression testing
- Capacity modeling

---

## Troubleshooting

### Connection Refused

**Cause:** Target server not reachable  
**Fix:** 
- Verify server is running
- Check firewall rules
- Confirm correct port

### All Requests Timing Out

**Cause:** Server overwhelmed or network issue  
**Fix:**
- Reduce concurrency
- Increase timeout
- Check network connectivity

### Proxies Not Working

**Cause:** Invalid proxy or authentication issue  
**Fix:**
- Test proxies individually
- Verify format (ip:port or user:pass@ip:port)
- Check SOCKS5 syntax

### Adaptive Not Adjusting

**Cause:** Target latency too high/low  
**Fix:**
- Adjust target latency slider
- Check adjustment interval
- Monitor latency values in real-time

---

## Academic Use Cases

### 1. Load Balancer Effectiveness

```
Test: Compare single server vs load-balanced setup
Metrics: Latency distribution, error rates, throughput
Analysis: Variance reduction, capacity increase
```

### 2. CDN Performance

```
Test: With/without cache busting
Metrics: Cache hit ratio, origin load, latency
Analysis: CDN offload percentage, cost savings
```

### 3. Auto-Scaling Behavior

```
Test: Gradual load increase with adaptive mode
Metrics: Response time, scaling triggers, lag time
Analysis: Scaling effectiveness, prediction accuracy
```

### 4. Rate Limiter Tuning

```
Test: Various concurrency levels
Metrics: Block rate, legitimate request impact
Analysis: Optimal rate limit thresholds
```

### 5. Database Connection Pooling

```
Test: High concurrency with keep-alive
Metrics: Connection reuse, timeout rates
Analysis: Pool size optimization
```

---

## Responsible Use Guidelines

### DO:
✅ Test only infrastructure you own or have written authorization  
✅ Document all tests and results  
✅ Monitor system health during tests  
✅ Stop immediately if unintended impact occurs  
✅ Use results to improve infrastructure  
✅ Share findings with team/stakeholders  

### DON'T:
❌ Test third-party services without permission  
❌ Run tests during production peak hours  
❌ Ignore system warnings or alerts  
❌ Use results to attack or harm systems  
❌ Skip documentation  
❌ Forget to clean up test data  

---

## 📈 Advanced Analytics

### Export for Further Analysis

```python
# Export results
import json

with open('results.json', 'w') as f:
    json.dump(results_data, f, indent=2)

# Import to pandas for analysis
import pandas as pd
df = pd.read_csv('results.csv')

# Time series analysis
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)
df['latency'].resample('1s').mean().plot()
```

### Integration with Monitoring

- **Grafana**: Import JSON data for dashboards
- **Prometheus**: Export metrics for alerting
- **ELK Stack**: Analyze logs for patterns
- **Custom Scripts**: Build analysis pipelines

---

## Summary

This tool provides:

1. **Realistic Testing**: Browser-like traffic, not synthetic bots
2. **Intelligent Adaptation**: Automatic concurrency optimization
3. **Comprehensive Monitoring**: Real-time metrics and visualization
4. **Proxy Management**: Health-checked, weighted rotation
5. **Professional Analysis**: Export-ready data for research
6. **Safety Features**: Bounded concurrency, timeout protection

**Built for:** SRE teams, academic researchers, infrastructure engineers  
**Purpose:** Improve system resilience through controlled testing  
**Ethics:** Authorized testing only, responsible use mandatory  

---

**Version**: 4.0 Professional  
**Last Updated**: 2026  
**Dependencies**: Streamlit, aiohttp, Plotly, Pandas  
**License**: For authorized testing and academic research

# proxy checker

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

Good Luck!

