# 🔬 Advanced SRE Load Testing & Observability Engine

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-FF4B4B?style=for-the-badge&logo=streamlit)
![aiohttp](https://img.shields.io/badge/aiohttp-3.9.0-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-Educational-yellow?style=for-the-badge)

### 🚀 High-Performance Infrastructure Resilience Testing Framework

This repository contains a professional-grade **System Reliability Engineering (SRE)** tool engineered to discover the **"Safe Operating Envelope"** of web services and backend infrastructure. By leveraging high-density, heterogeneous traffic simulation, it empowers engineers to map exact degradation points and test the true limits of connection pooling, load balancers, and auto-scaling logic.

---

## ⚠️ LEGAL DISCLAIMER & ETHICAL WARNING

> **CRITICAL NOTICE:** This software is published strictly for **educational research** and **authorized security auditing**.
> 
> Due to its highly optimized asynchronous architecture, connection stressor modules, and proxy rotation capabilities, this tool generates massive volumetric traffic. If misused, it can easily function as a **Distributed Denial of Service (DDoS)** weapon.
>
> **The author assumes ABSOLUTELY NO LIABILITY for any unauthorized, malicious, or illegal use of this software.** Any damage, service disruption, or legal consequences resulting from its deployment are solely the responsibility of the end-user. By cloning, downloading, or running this code, you explicitly agree to deploy it **ONLY on infrastructure you own or have explicit, documented authorization to test.**

---

## 🧠 System Architecture & Core Modules

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

## 📊 Real-Time Observability (Streamlit)

The framework includes a fully integrated, real-time observability dashboard for live telemetry visualization:
* **Live Latency Timeline:** Granular tracking of successful (2xx), blocked (403/429), and failed (5xx) requests.
* **Throughput Mapping:** Real-time RPS graphing with ramp sequence overlays.
* **Endpoint Complexity Analysis:** Multi-route targeting with weighted traffic distribution to identify which specific API endpoints saturate CPU/RAM first.

---

## 🛠️ Installation & Usage

**1. Clone the repository and navigate to the directory:**
```bash
git clone [https://github.com/charkve1/SRE-Stress-Tester.git](https://github.com/charkve1/SRE-Stress-Tester.git)
cd SRE-Stress-Tester

pip install -r requirements_advanced.txt

python "proxy checker/proxy_scraper_checker.py" (optıonal)

python -m streamlit run advanced_sre_test.py (launch)

(Configure testing parameters, concurrency limits, and upload your proxy list directly via the graphical interface)

📚 Academic & Professional Use Cases

Capacity Planning: Establishing baseline performance metrics before marketing campaigns.

CDN & Edge Optimization: Calculating cache hit ratios and origin offload percentages under heavy load.

Rate Limiter Calibration: Finding the exact threshold to drop malicious traffic without impacting legitimate human users.
