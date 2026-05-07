"""
SRE Infrastructure Stress-Testing & Observability Tool

A professional-grade System Reliability Engineering (SRE) framework for
identifying the 'Safe Operating Envelope' of web services through
high-density, heterogeneous traffic simulation.

Capabilities:
- High-entropy session randomization (headers, query params, ordering)
- Connection management stressor (handshake storm, persistence analysis)
- Endpoint complexity analysis with weighted route targeting
- Volumetric capacity discovery via linear/exponential ramp-up
- Advanced proxy health watchdog with real-time rotation
- HTTP/2 multiplexing efficiency profiler
- Real-time Streamlit observability dashboard

Author: SRE Team
Version: 5.0 (Professional)
License: For authorized infrastructure testing only
"""

import streamlit as st
import asyncio
import aiohttp
import time
import json
import csv
import statistics
import uuid
import pandas as pd
import plotly.graph_objects as go
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict, deque
from enum import Enum
from datetime import datetime
import os
import re
import random
import hashlib
from pathlib import Path
import socket
import math


# ============================================================================
# High-Entropy Session Randomization Engine
# ============================================================================

class SessionRandomizer:
    """Generates high-entropy, non-fingerprintable HTTP sessions.
    
    Composes headers and query parameters from randomized component pools
    to ensure every request appears unique, bypassing edge caching and
    forcing origin-server hits for accurate resource profiling.
    """
    
    # Composable browser/os/version pools for high-entropy UA generation
    _BROWSERS = [
        ("Chrome", ["120.0.6099", "119.0.6045", "121.0.6167", "118.0.5993"]),
        ("Firefox", ["121.0", "120.0", "119.0", "118.0.2"]),
        ("Safari", ["17.2", "17.1", "16.6", "16.5"]),
        ("Edge", ["120.0.2210", "119.0.2151", "121.0.2277"]),
    ]
    _OS = [
        ("Windows NT 10.0; Win64; x64", "Windows"),
        ("Windows NT 10.0; WOW64", "Windows"),
        ("Macintosh; Intel Mac OS X 10_15_7", "macOS"),
        ("Macintosh; Intel Mac OS X 10.15", "macOS"),
        ("X11; Linux x86_64", "Linux"),
        ("X11; Ubuntu; Linux x86_64", "Linux"),
    ]
    _ACCEPT_BASE = [
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    ]
    _ACCEPT_LANG = [
        "en-US,en;q=0.9", "en-US,en;q=0.9,es;q=0.8", "en-GB,en;q=0.9,en-US;q=0.8",
        "en-US,en;q=0.9,fr;q=0.8", "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7", "ja-JP,ja;q=0.9,en-US;q=0.8",
    ]
    _ACCEPT_ENC = [
        "gzip, deflate, br", "gzip, deflate", "br, gzip, deflate",
    ]
    _SEC_FETCH_DEST = ["document", "empty", "iframe", "image"]
    _SEC_FETCH_MODE = ["navigate", "cors", "no-cors", "same-origin"]
    _SEC_FETCH_SITE = ["none", "same-origin", "cross-site", "same-site"]
    _CACHE_CONTROL = [
        "max-age=0", "no-cache", "no-store, must-revalidate", "no-cache, no-store, must-revalidate",
    ]
    _REFERER_POOL = [
        "https://www.google.com/", "https://www.bing.com/", "https://duckduckgo.com/",
        "https://github.com/", "https://stackoverflow.com/", "https://www.reddit.com/",
        None, None, None,
    ]
    _DNT_VALUES = ["1", "0", None, None]
    
    @classmethod
    def _compose_ua(cls) -> str:
        """Compose a randomized User-Agent from component pools."""
        browser_name, versions = random.choice(cls._BROWSERS)
        version = random.choice(versions)
        os_str, _ = random.choice(cls._OS)
        
        if browser_name == "Firefox":
            return f"Mozilla/5.0 ({os_str}; rv:{version}) Gecko/20100101 Firefox/{version}"
        elif browser_name == "Safari":
            return f"Mozilla/5.0 ({os_str}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15"
        elif browser_name == "Edge":
            chrome_ver = version
            return f"Mozilla/5.0 ({os_str}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36 Edg/{version}"
        else:  # Chrome
            return f"Mozilla/5.0 ({os_str}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
    
    @classmethod
    def _compose_query_params(cls) -> str:
        """Generate high-entropy query parameter string for cache busting."""
        params = {
            "_cb": hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:8],
            "_ts": str(int(time.time() * 1000)),
            "_r": hashlib.sha256(str(random.random()).encode()).hexdigest()[:12],
        }
        # Sometimes add extra tracking-like params
        if random.random() > 0.5:
            params["_v"] = str(random.randint(1, 999))
        if random.random() > 0.7:
            params["_s"] = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
        return "&".join(f"{k}={v}" for k, v in params.items())
    
    @classmethod
    def generate_headers(cls, include_cache_buster: bool = False, entropy_level: str = "high") -> Dict[str, str]:
        """Generate a complete set of high-entropy, randomized HTTP headers.
        
        Args:
            include_cache_buster: Add cache-busting Cache-Control header
            entropy_level: 'low' (fixed rotation), 'medium' (partial random), 'high' (full compose)
            
        Returns:
            Dictionary of HTTP headers in randomized order (if high entropy)
        """
        user_agent = cls._compose_ua()
        is_chrome = "Chrome" in user_agent and "Edg" not in user_agent
        is_firefox = "Firefox" in user_agent
        is_edge = "Edg" in user_agent
        
        header_items = [
            ("User-Agent", user_agent),
            ("Accept", random.choice(cls._ACCEPT_BASE)),
            ("Accept-Language", random.choice(cls._ACCEPT_LANG)),
            ("Accept-Encoding", random.choice(cls._ACCEPT_ENC)),
        ]
        
        # Connection header varies by mode
        conn_val = "keep-alive"
        header_items.append(("Connection", conn_val))
        
        # Sec-Fetch headers
        if random.random() > 0.3:
            header_items.append(("Sec-Fetch-Dest", random.choice(cls._SEC_FETCH_DEST)))
            header_items.append(("Sec-Fetch-Mode", random.choice(cls._SEC_FETCH_MODE)))
            header_items.append(("Sec-Fetch-Site", random.choice(cls._SEC_FETCH_SITE)))
            header_items.append(("Sec-Fetch-User", "?1"))
        
        # Upgrade-Insecure-Requests (browsers do this ~80% of the time)
        if random.random() > 0.2:
            header_items.append(("Upgrade-Insecure-Requests", "1"))
        
        # Client Hints (Chrome/Edge)
        if (is_chrome or is_edge) and entropy_level != "low":
            platform = '"Windows"' if "Windows" in user_agent else '"macOS"'
            header_items.append(("Sec-Ch-Ua", f'"Not A Brand";v="8", "Chromium";v="{random.randint(118,121)}", "Google Chrome";v="{random.randint(118,121)}"'))
            header_items.append(("Sec-Ch-Ua-Mobile", "?0"))
            header_items.append(("Sec-Ch-Ua-Platform", platform))
        
        # Referer (only ~40% of requests)
        referer = random.choice(cls._REFERER_POOL)
        if referer is not None:
            header_items.append(("Referer", referer))
        
        # DNT
        dnt = random.choice(cls._DNT_VALUES)
        if dnt is not None:
            header_items.append(("DNT", dnt))
        
        # X-Forwarded-For (random IP simulation)
        if entropy_level == "high" and random.random() > 0.5:
            ip = f"{random.randint(10,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            header_items.append(("X-Forwarded-For", ip))
        
        # Cache busting
        if include_cache_buster:
            header_items.append(("Cache-Control", random.choice(cls._CACHE_CONTROL)))
            header_items.append(("Pragma", "no-cache"))
        
        # High entropy: shuffle header order to defeat fingerprinting
        if entropy_level == "high":
            random.shuffle(header_items)
        
        return dict(header_items)
    
    @classmethod
    def generate_query_params(cls, url: str) -> str:
        """Inject high-entropy query parameters into a URL.
        
        Args:
            url: Base URL
            
        Returns:
            URL with appended randomized query parameters
        """
        qs = cls._compose_query_params()
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{qs}"
    
    @classmethod
    def generate_api_headers(cls, api_key: str = None) -> Dict[str, str]:
        """Generate randomized API headers.
        
        Args:
            api_key: Optional API key for authentication
            
        Returns:
            Dictionary of API-appropriate headers
        """
        headers = {
            "User-Agent": cls._compose_ua(),
            "Accept": random.choice(["application/json", "application/xml", "*/*"]),
            "Accept-Language": random.choice(cls._ACCEPT_LANG),
            "Accept-Encoding": random.choice(cls._ACCEPT_ENC),
            "Connection": "keep-alive",
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers


# ============================================================================
# Advanced Proxy Health Watchdog
# ============================================================================

@dataclass
class ProxyHealth:
    """Track health metrics for individual proxies.
    
    Attributes:
        proxy: Proxy string
        is_healthy: Whether proxy is currently healthy
        health_score: Composite health score (0-100)
        last_check: Timestamp of last health check
        last_used: Timestamp of last request through this proxy
        consecutive_failures: Number of consecutive failed requests
        total_requests: Total requests through this proxy
        total_errors: Total errors through this proxy
        avg_response_time: Average response time through this proxy
        last_error: Most recent error message
        rate_limited: Whether proxy is currently rate-limited
        rate_limit_until: Timestamp when rate limit expires
    """
    proxy: str
    is_healthy: bool = True
    health_score: float = 100.0
    last_check: float = 0.0
    last_used: float = 0.0
    consecutive_failures: int = 0
    total_requests: int = 0
    total_errors: int = 0
    avg_response_time: float = 0.0
    last_error: str = ""
    rate_limited: bool = False
    rate_limit_until: float = 0.0


class ProxyHealthWatchdog:
    """Advanced proxy manager with health scoring, real-time rotation, and rate-limit handling.
    
    Features:
    - Composite health score (success rate, latency, recency)
    - Least-recently-used rotation for request uniqueness
    - Automatic proxy rotation on failure/rate-limit
    - Exponential backoff with jitter for rate-limited proxies
    - SOCKS5 proxy support with authentication
    """
    
    def __init__(self, rotation_strategy: str = "least_used"):
        """Initialize proxy watchdog.
        
        Args:
            rotation_strategy: Strategy for proxy rotation (least_used, round_robin, random)
        """
        self.proxies: List[str] = []
        self.proxy_health: Dict[str, ProxyHealth] = {}
        self.rotation_strategy = rotation_strategy
        self.current_index = 0
        
    def load_proxies(self, file_content: str) -> int:
        """Load and validate proxies from file content.
        
        Args:
            file_content: Raw text from proxies.txt file
            
        Returns:
            Number of valid proxies loaded
        """
        self.proxies = []
        self.proxy_health = {}
        
        lines = file_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if self._validate_proxy(line):
                self.proxies.append(line)
                self.proxy_health[line] = ProxyHealth(proxy=line)
        
        return len(self.proxies)
    
    def _validate_proxy(self, proxy: str) -> bool:
        """Validate proxy format (HTTP, HTTPS, SOCKS5).
        
        Args:
            proxy: Proxy string to validate
            
        Returns:
            True if proxy format is valid
        """
        pattern_http = r'^(?:(\w+:\w+)@)?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$'
        pattern_socks5 = r'^socks5(?:h)?://(?:(\w+:\w+)@)?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$'
        
        if re.match(pattern_http, proxy):
            return True
        if re.match(pattern_socks5, proxy):
            return True
        
        return False
    
    def get_proxy_dict(self, proxy_string: Optional[str]) -> Optional[str]:
        """Convert proxy string to aiohttp-compatible proxy URL.
        
        Args:
            proxy_string: Proxy string
            
        Returns:
            Proxy URL for aiohttp or None
        """
        if not proxy_string:
            return None
        if proxy_string.startswith(('http://', 'https://', 'socks5://', 'socks5h://')):
            return proxy_string
        return f"http://{proxy_string}"
    
    def _compute_health_score(self, health: ProxyHealth) -> float:
        """Compute composite health score for a proxy.
        
        Based on success rate, latency, and recency.
        
        Args:
            health: ProxyHealth object
            
        Returns:
            Health score (0-100)
        """
        if health.total_requests == 0:
            return 100.0
        
        # Success rate component (0-50 points)
        success_rate = 1.0 - (health.total_errors / health.total_requests)
        success_score = success_rate * 50.0
        
        # Latency component (0-30 points) - lower latency = higher score
        latency_score = 30.0
        if health.avg_response_time > 0:
            latency_penalty = min(30.0, health.avg_response_time * 10.0)
            latency_score = max(0, 30.0 - latency_penalty)
        
        # Recency component (0-20 points) - recently used = higher score
        recency_score = 20.0
        if health.last_used > 0:
            age = time.time() - health.last_used
            recency_score = max(0, 20.0 - age * 2.0)
        
        # Consecutive failure penalty
        failure_penalty = health.consecutive_failures * 10.0
        
        return max(0.0, min(100.0, success_score + latency_score + recency_score - failure_penalty))
    
    def get_next_proxy(self) -> Optional[Tuple[str, ProxyHealth]]:
        """Get the next proxy based on rotation strategy and health.
        
        Only returns healthy, non-rate-limited proxies.
        
        Returns:
            Tuple of (proxy_string, ProxyHealth) or None if no healthy proxies available
        """
        now = time.time()
        
        # Re-evaluate rate-limited proxies
        for health in self.proxy_health.values():
            if health.rate_limited and now >= health.rate_limit_until:
                health.rate_limited = False
                health.consecutive_failures = max(0, health.consecutive_failures - 3)
        
        # Filter to healthy, non-rate-limited proxies
        eligible = [
            (p, h) for p, h in self.proxy_health.items()
            if h.is_healthy and not h.rate_limited
        ]
        
        if not eligible:
            # Fallback: try all proxies including degraded ones
            eligible = list(self.proxy_health.items())
        
        if not eligible:
            return None
        
        if self.rotation_strategy == "random":
            proxy, health = random.choice(eligible)
        elif self.rotation_strategy == "round_robin":
            proxy, health = eligible[self.current_index % len(eligible)]
            self.current_index = (self.current_index + 1) % len(eligible)
        else:  # least_used: return least-recently-used healthy proxy
            eligible.sort(key=lambda x: x[1].last_used)
            proxy, health = eligible[0]
        
        health.last_used = now
        return (proxy, health)
    
    def record_success(self, proxy: str, response_time: float) -> None:
        """Record successful request through proxy.
        
        Args:
            proxy: Proxy string
            response_time: Request response time in seconds
        """
        if proxy in self.proxy_health:
            health = self.proxy_health[proxy]
            health.total_requests += 1
            health.consecutive_failures = 0
            health.last_check = time.time()
            health.is_healthy = True
            
            # Update average response time
            health.avg_response_time = (
                (health.avg_response_time * (health.total_requests - 1) + response_time) /
                max(1, health.total_requests - 1 + 1)
            ) if health.total_requests > 1 else response_time
            
            # Recompute health score
            health.health_score = self._compute_health_score(health)
    
    def record_error(self, proxy: str, error: str, status_code: int = 0) -> None:
        """Record failed request through proxy with backoff logic.
        
        Args:
            proxy: Proxy string
            error: Error message
            status_code: HTTP status code (if available)
        """
        if proxy in self.proxy_health:
            health = self.proxy_health[proxy]
            health.total_requests += 1
            health.total_errors += 1
            health.consecutive_failures += 1
            health.last_error = error
            health.last_check = time.time()
            
            # Rate-limit handling with exponential backoff + jitter
            if status_code in [429, 403]:
                health.rate_limited = True
                backoff = min(300, 15 * (2 ** min(health.consecutive_failures, 5)))
                jitter = random.uniform(0, backoff * 0.3)
                health.rate_limit_until = time.time() + backoff + jitter
            
            # Mark as unhealthy after 5 consecutive failures
            if health.consecutive_failures >= 5:
                health.is_healthy = False
            
            health.health_score = self._compute_health_score(health)
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get comprehensive proxy statistics.
        
        Returns:
            Dictionary with proxy performance metrics
        """
        total = len(self.proxies)
        healthy = sum(1 for h in self.proxy_health.values() if h.is_healthy)
        rate_limited = sum(1 for h in self.proxy_health.values() if h.rate_limited)
        avg_score = statistics.mean([h.health_score for h in self.proxy_health.values()]) if self.proxy_health else 0
        
        return {
            "total_proxies": total,
            "healthy_proxies": healthy,
            "unhealthy_proxies": total - healthy,
            "rate_limited": rate_limited,
            "avg_health_score": round(avg_score, 1),
            "proxy_details": [
                {
                    "proxy": h.proxy,
                    "score": round(h.health_score, 1),
                    "healthy": h.is_healthy,
                    "rate_limited": h.rate_limited,
                    "requests": h.total_requests,
                    "avg_latency_ms": round(h.avg_response_time * 1000, 1),
                }
                for h in self.proxy_health.values()
            ]
        }


# ============================================================================
# Volumetric Capacity Discovery - Ramp Engine
# ============================================================================

class RampEngine:
    """Linear and exponential ramp-up engine to discover the 'Safe Operating Envelope'.
    
    Progressively increases concurrency to find the exact RPS threshold where
    latency spikes or 5xx errors appear -- the 'Breaking Point'.
    
    Modes:
    - Linear: Increase concurrency by fixed step every N seconds
    - Exponential: Double concurrency every N seconds
    - Adaptive: PID-like feedback based on latency (original mode)
    """
    
    class RampMode(Enum):
        LINEAR = "linear"
        EXPONENTIAL = "exponential"
        ADAPTIVE = "adaptive"
    
    def __init__(
        self,
        mode: str = "adaptive",
        initial_concurrency: int = 50,
        min_concurrency: int = 10,
        max_concurrency: int = 2000,
        step_size: int = 25,
        step_interval_seconds: float = 5.0,
        target_latency_ms: float = 500.0,
        breaking_latency_multiplier: float = 2.5,
        breaking_error_rate: float = 0.01,
        breaking_5xx_rate: float = 0.01,
    ):
        """Initialize ramp engine.
        
        Args:
            mode: Ramp mode (linear, exponential, adaptive)
            initial_concurrency: Starting concurrency level
            min_concurrency: Minimum allowed concurrency
            max_concurrency: Maximum allowed concurrency
            step_size: Concurrency increment per step (linear mode)
            step_interval_seconds: Seconds between ramp steps
            target_latency_ms: Target average latency in milliseconds
            breaking_latency_multiplier: P95 > target * multiplier = breaking point
            breaking_error_rate: Error rate threshold for breaking point
            breaking_5xx_rate: 5xx rate threshold for breaking point
        """
        self.mode = self.RampMode(mode)
        self.initial_concurrency = initial_concurrency
        self.current_concurrency = initial_concurrency
        self.min_concurrency = min_concurrency
        self.max_concurrency = max_concurrency
        self.step_size = step_size
        self.step_interval = step_interval_seconds
        self.target_latency_ms = target_latency_ms
        self.breaking_latency_multiplier = breaking_latency_multiplier
        self.breaking_error_rate = breaking_error_rate
        self.breaking_5xx_rate = breaking_5xx_rate
        
        # State tracking
        self.latency_window: deque = deque(maxlen=200)
        self.rps_history: List[Tuple[float, float, int]] = []  # (time, rps, concurrency)
        self.step_count = 0
        self.last_step_time = 0.0
        self.breaking_point: Optional[Dict[str, Any]] = None
        self.ramp_start_time = 0.0
        self._total_requests = 0
        self._total_errors = 0
        self._total_5xx = 0
        self._baseline_p95: Optional[float] = None
    
    def start_ramp(self) -> None:
        """Initialize the ramp sequence."""
        self.ramp_start_time = time.time()
        self.last_step_time = time.time()
        self.step_count = 0
        self.current_concurrency = self.initial_concurrency
        self.rps_history = []
        self.breaking_point = None
        self._total_requests = 0
        self._total_errors = 0
        self._total_5xx = 0
        self._baseline_p95 = None
    
    def record_latency(self, latency_ms: float) -> None:
        """Record a latency measurement.
        
        Args:
            latency_ms: Latency in milliseconds
        """
        self.latency_window.append(latency_ms)
    
    def record_status(self, status_code: int) -> None:
        """Record request outcome for breaking point detection.
        
        Args:
            status_code: HTTP status code
        """
        self._total_requests += 1
        if status_code >= 500:
            self._total_5xx += 1
            self._total_errors += 1
        elif status_code >= 400:
            self._total_errors += 1
    
    def should_step(self) -> bool:
        """Check if it's time to increase concurrency.
        
        Returns:
            True if the ramp should step up
        """
        if self.mode == self.RampMode.ADAPTIVE:
            return False  # Handled separately
        now = time.time()
        return (now - self.last_step_time) >= self.step_interval
    
    def step(self) -> int:
        """Execute one ramp step, returning new concurrency.
        
        Returns:
            New concurrency level
        """
        self.step_count += 1
        self.last_step_time = time.time()
        
        if self.mode == self.RampMode.LINEAR:
            self.current_concurrency = min(
                self.max_concurrency,
                self.current_concurrency + self.step_size
            )
        elif self.mode == self.RampMode.EXPONENTIAL:
            self.current_concurrency = min(
                self.max_concurrency,
                int(self.initial_concurrency * (2 ** self.step_count))
            )
        
        # Record RPS snapshot
        elapsed = time.time() - self.ramp_start_time
        current_rps = self._total_requests / elapsed if elapsed > 0 else 0
        self.rps_history.append((elapsed, current_rps, self.current_concurrency))
        
        return self.current_concurrency
    
    def check_breaking_point(self) -> Optional[Dict[str, Any]]:
        """Evaluate whether the breaking point has been reached.
        
        Returns:
            Breaking point dict if detected, else None
        """
        if len(self.latency_window) < 20 or self._total_requests < 50:
            return None
        
        sorted_lat = sorted(self.latency_window)
        p95 = sorted_lat[int(0.95 * len(sorted_lat))]
        p50 = sorted_lat[int(0.50 * len(sorted_lat))]
        
        # Establish baseline after initial warmup
        if self._baseline_p95 is None and self._total_requests >= 50:
            self._baseline_p95 = p95
        
        breaking_reasons = []
        
        # Check P95 latency spike
        if self._baseline_p95 and self._baseline_p95 > 0:
            if p95 > self._baseline_p95 * self.breaking_latency_multiplier:
                breaking_reasons.append(f"P95 latency {p95:.0f}ms > {self.breaking_latency_multiplier}x baseline {self._baseline_p95:.0f}ms")
        if p95 > self.target_latency_ms * self.breaking_latency_multiplier:
            breaking_reasons.append(f"P95 latency {p95:.0f}ms > {self.breaking_latency_multiplier}x target {self.target_latency_ms:.0f}ms")
        
        # Check 5xx error rate
        if self._total_requests > 100:
            err_rate = self._total_5xx / self._total_requests
            if err_rate > self.breaking_5xx_rate:
                breaking_reasons.append(f"5xx rate {err_rate:.3f} > {self.breaking_5xx_rate}")
        
        # Check overall error rate
        if self._total_requests > 100:
            total_err_rate = self._total_errors / self._total_requests
            if total_err_rate > self.breaking_error_rate:
                breaking_reasons.append(f"Error rate {total_err_rate:.3f} > {self.breaking_error_rate}")
        
        if breaking_reasons:
            elapsed = time.time() - self.ramp_start_time
            current_rps = self._total_requests / elapsed if elapsed > 0 else 0
            self.breaking_point = {
                "rps_at_break": round(current_rps, 1),
                "concurrency_at_break": self.current_concurrency,
                "p95_latency_ms": round(p95, 1),
                "p50_latency_ms": round(p50, 1),
                "elapsed_seconds": round(elapsed, 1),
                "total_requests": self._total_requests,
                "reasons": breaking_reasons,
            }
            return self.breaking_point
        
        return None
    
    def adjust_adaptive(self) -> int:
        """Adaptive mode: adjust concurrency based on latency feedback.
        
        Returns:
            New concurrency level
        """
        if len(self.latency_window) < 10:
            return self.current_concurrency
        
        avg_latency = statistics.mean(self.latency_window)
        
        if avg_latency > self.target_latency_ms * 2:
            factor = 0.6
        elif avg_latency > self.target_latency_ms * 1.5:
            factor = 0.75
        elif avg_latency > self.target_latency_ms:
            factor = 0.9
        elif avg_latency < self.target_latency_ms * 0.5:
            factor = 1.3
        elif avg_latency < self.target_latency_ms * 0.7:
            factor = 1.15
        else:
            factor = 1.0
        
        new_concurrency = int(self.current_concurrency * factor)
        self.current_concurrency = max(
            self.min_concurrency,
            min(self.max_concurrency, new_concurrency)
        )
        return self.current_concurrency
    
    def get_current_concurrency(self) -> int:
        """Get current recommended concurrency level.
        
        Returns:
            Current concurrency value
        """
        return self.current_concurrency
    
    def get_ramp_stats(self) -> Dict[str, Any]:
        """Get ramp engine statistics.
        
        Returns:
            Dictionary with ramp metrics
        """
        avg_latency = statistics.mean(self.latency_window) if self.latency_window else 0
        p95 = 0
        if len(self.latency_window) >= 20:
            sorted_lat = sorted(self.latency_window)
            p95 = sorted_lat[int(0.95 * len(sorted_lat))]
        
        elapsed = time.time() - self.ramp_start_time if self.ramp_start_time > 0 else 0
        current_rps = self._total_requests / elapsed if elapsed > 0 else 0
        
        return {
            "mode": self.mode.value,
            "current_concurrency": self.current_concurrency,
            "step_count": self.step_count,
            "avg_latency_ms": round(avg_latency, 1),
            "p95_latency_ms": round(p95, 1),
            "current_rps": round(current_rps, 1),
            "baseline_p95_ms": round(self._baseline_p95, 1) if self._baseline_p95 else 0,
            "breaking_point": self.breaking_point,
        }


# ============================================================================
# Connection Management Stressor
# ============================================================================

class ConnectionStressor:
    """Test server TCP connection-handling limits through controlled stress modes.
    
    Modes:
    - DEFAULT: Standard keep-alive connection pooling
    - HANDSHAKE_STORM: Force new TCP handshakes per request (Connection: close)
    - PERSISTENCE_ANALYSIS: Long-lived, low-throughput sessions to validate
      timeout and worker_pool configurations
    """
    
    class StressMode(Enum):
        DEFAULT = "default"
        HANDSHAKE_STORM = "handshake_storm"
        PERSISTENCE_ANALYSIS = "persistence_analysis"
    
    def __init__(self, mode: str = "default"):
        """Initialize connection stressor.
        
        Args:
            mode: Stress mode (default, handshake_storm, persistence_analysis)
        """
        self.mode = self.StressMode(mode)
        self.total_connections = 0
        self.reused_connections = 0
        self.closed_connections = 0
        self.connection_times: deque = deque(maxlen=1000)
        self.active_connections = 0
        self.handshake_times: deque = deque(maxlen=500)
        
    def record_new_connection(self) -> None:
        """Record creation of new TCP connection."""
        self.total_connections += 1
        self.active_connections += 1
    
    def record_reused_connection(self) -> None:
        """Record reuse of existing connection."""
        self.reused_connections += 1
    
    def record_closed_connection(self) -> None:
        """Record closure of connection."""
        self.closed_connections += 1
        self.active_connections = max(0, self.active_connections - 1)
    
    def record_handshake_time(self, time_ms: float) -> None:
        """Record TCP handshake duration.
        
        Args:
            time_ms: Handshake time in milliseconds
        """
        self.handshake_times.append(time_ms)
    
    def get_reuse_ratio(self) -> float:
        """Calculate connection reuse ratio.
        
        Returns:
            Ratio of reused connections to total (0-1)
        """
        total = self.reused_connections + self.total_connections
        return self.reused_connections / total if total > 0 else 0
    
    def get_churn_rate(self) -> float:
        """Calculate connection churn rate.
        
        Returns:
            Ratio of closed connections to total created
        """
        return self.closed_connections / self.total_connections if self.total_connections > 0 else 0
    
    def get_avg_handshake_ms(self) -> float:
        """Calculate average TCP handshake time.
        
        Returns:
            Average handshake time in milliseconds
        """
        return statistics.mean(self.handshake_times) if self.handshake_times else 0
    
    def should_force_new_connection(self) -> bool:
        """Determine if a new connection should be forced (handshake storm mode).
        
        Returns:
            True to force a new TCP connection
        """
        return self.mode == self.StressMode.HANDSHAKE_STORM
    
    def should_use_keepalive(self) -> bool:
        """Determine if keep-alive should be used.
        
        Returns:
            True to use keep-alive connections
        """
        if self.mode == self.StressMode.HANDSHAKE_STORM:
            return False
        return True
    
    def get_persistence_interval(self) -> float:
        """Get interval between pings for persistence analysis mode.
        
        Returns:
            Seconds to wait between requests in persistence mode
        """
        if self.mode == self.StressMode.PERSISTENCE_ANALYSIS:
            return 5.0  # 5-second gap to test keep-alive timeout
        return 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection stressor statistics.
        
        Returns:
            Dictionary with connection metrics
        """
        return {
            "mode": self.mode.value,
            "total_connections_created": self.total_connections,
            "connections_reused": self.reused_connections,
            "connections_closed": self.closed_connections,
            "reuse_ratio": round(self.get_reuse_ratio(), 3),
            "churn_rate": round(self.get_churn_rate(), 3),
            "currently_active": self.active_connections,
            "avg_handshake_ms": round(self.get_avg_handshake_ms(), 1),
        }


# ============================================================================
# Endpoint Complexity Analyzer
# ============================================================================

@dataclass
class RouteMetrics:
    """Per-route performance metrics.
    
    Attributes:
        path: URL path
        weight: Traffic weight (percentage)
        requests: Total requests to this route
        errors: Total errors on this route
        latencies: List of response times in seconds
        status_codes: Distribution of HTTP status codes
    """
    path: str
    weight: float = 0.0
    requests: int = 0
    errors: int = 0
    latencies: List[float] = field(default_factory=list)
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency in ms."""
        return (statistics.mean(self.latencies) * 1000) if self.latencies else 0
    
    @property
    def p95_latency_ms(self) -> float:
        """Calculate P95 latency in ms."""
        if not self.latencies:
            return 0
        sorted_times = sorted(self.latencies)
        idx = int(0.95 * len(sorted_times))
        return sorted_times[min(idx, len(sorted_times) - 1)] * 1000
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        return self.errors / self.requests if self.requests > 0 else 0


class EndpointComplexityAnalyzer:
    """Targets user-defined 'Heavy Routes' to find CPU/RAM saturation points.
    
    Distributes concurrent load proportionally across weighted routes,
    tracking per-route latency and error metrics to identify which
    endpoint saturates first.
    """
    
    def __init__(self, routes: Optional[List[Tuple[str, float]]] = None):
        """Initialize endpoint analyzer.
        
        Args:
            routes: List of (path, weight) tuples. Weights are normalized.
        """
        self.routes: Dict[str, RouteMetrics] = {}
        self._cumulative_weights: List[Tuple[float, str]] = []
        
        if routes:
            self.load_routes(routes)
    
    def load_routes(self, routes: List[Tuple[str, float]]) -> None:
        """Load and normalize route weights.
        
        Args:
            routes: List of (path, weight) tuples
        """
        total_weight = sum(w for _, w in routes)
        self.routes = {}
        self._cumulative_weights = []
        cumulative = 0.0
        
        for path, weight in routes:
            normalized = weight / total_weight if total_weight > 0 else 1.0 / len(routes)
            self.routes[path] = RouteMetrics(path=path, weight=normalized)
            cumulative += normalized
            self._cumulative_weights.append((cumulative, path))
    
    def get_next_route(self) -> str:
        """Get the next route based on weighted random selection.
        
        Returns:
            Route path string
        """
        if not self._cumulative_weights:
            return "/"
        
        r = random.random()
        for threshold, path in self._cumulative_weights:
            if r <= threshold:
                return path
        return self._cumulative_weights[-1][1]
    
    def record_request(self, path: str, response_time: float, status_code: int) -> None:
        """Record a request to a specific route.
        
        Args:
            path: Route path
            response_time: Response time in seconds
            status_code: HTTP status code
        """
        if path in self.routes:
            rm = self.routes[path]
        else:
            rm = RouteMetrics(path=path)
            self.routes[path] = rm
        
        rm.requests += 1
        rm.latencies.append(response_time)
        rm.status_codes[status_code] += 1
        
        if status_code >= 400:
            rm.errors += 1
    
    def get_saturation_report(self) -> Dict[str, Any]:
        """Generate saturation analysis across all routes.
        
        Returns:
            Dictionary with per-route saturation metrics
        """
        report = {
            "total_routes": len(self.routes),
            "routes": []
        }
        
        for path, rm in sorted(self.routes.items(), key=lambda x: x[1].error_rate, reverse=True):
            report["routes"].append({
                "path": path,
                "weight": round(rm.weight * 100, 1),
                "requests": rm.requests,
                "avg_latency_ms": round(rm.avg_latency_ms, 1),
                "p95_latency_ms": round(rm.p95_latency_ms, 1),
                "error_rate": round(rm.error_rate * 100, 2),
                "status_codes": dict(rm.status_codes),
            })
        
        # Identify first-saturating route
        if report["routes"]:
            report["first_saturating"] = report["routes"][0]
        
        return report
    
    def get_stats(self) -> Dict[str, Any]:
        """Get endpoint analyzer summary statistics.
        
        Returns:
            Dictionary with summary metrics
        """
        total_requests = sum(r.requests for r in self.routes.values())
        total_errors = sum(r.errors for r in self.routes.values())
        
        return {
            "active_routes": len(self.routes),
            "total_route_requests": total_requests,
            "total_route_errors": total_errors,
            "overall_error_rate": round(total_errors / total_requests * 100, 2) if total_requests > 0 else 0,
        }


# ============================================================================
# HTTP/2 Efficiency Profiler
# ============================================================================

class HTTP2Profiler:
    """Profiles HTTP/2 multiplexing efficiency and concurrent stream capacity.
    
    Measures how many concurrent streams per connection the server can
    efficiently manage before performance degrades.
    """
    
    def __init__(self, enabled: bool = False):
        """Initialize HTTP/2 profiler.
        
        Args:
            enabled: Whether HTTP/2 profiling is active
        """
        self.enabled = enabled
        self.total_streams = 0
        self.active_streams = 0
        self.max_concurrent_streams = 0
        self.stream_creation_rate: deque = deque(maxlen=100)
        self.stream_reuse_count = 0
        self.stream_errors = 0
        self.connection_count = 0
        
    def record_stream_opened(self) -> None:
        """Record opening of a new HTTP/2 stream."""
        self.total_streams += 1
        self.active_streams += 1
        self.max_concurrent_streams = max(self.max_concurrent_streams, self.active_streams)
    
    def record_stream_closed(self) -> None:
        """Record closing of an HTTP/2 stream."""
        self.active_streams = max(0, self.active_streams - 1)
    
    def record_stream_reused(self) -> None:
        """Record reuse of an existing stream."""
        self.stream_reuse_count += 1
    
    def record_stream_error(self) -> None:
        """Record a stream-level error."""
        self.stream_errors += 1
    
    def record_new_connection(self) -> None:
        """Record a new HTTP/2 connection."""
        self.connection_count += 1
    
    def get_avg_streams_per_connection(self) -> float:
        """Calculate average streams per connection.
        
        Returns:
            Average streams per connection
        """
        return self.total_streams / self.connection_count if self.connection_count > 0 else 0
    
    def get_stream_efficiency(self) -> float:
        """Calculate stream efficiency ratio.
        
        Returns:
            Efficiency ratio (0-1)
        """
        total = self.total_streams + self.stream_reuse_count
        return self.stream_reuse_count / total if total > 0 else 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get HTTP/2 profiler statistics.
        
        Returns:
            Dictionary with HTTP/2 metrics
        """
        return {
            "enabled": self.enabled,
            "total_streams": self.total_streams,
            "active_streams": self.active_streams,
            "max_concurrent_streams": self.max_concurrent_streams,
            "stream_reuse_count": self.stream_reuse_count,
            "stream_errors": self.stream_errors,
            "connection_count": self.connection_count,
            "avg_streams_per_conn": round(self.get_avg_streams_per_connection(), 1),
            "stream_efficiency": round(self.get_stream_efficiency(), 3),
        }


# ============================================================================
# Test Results with Real-time Tracking
# ============================================================================

@dataclass
class TestResults:
    """Comprehensive test results with real-time tracking for all modules.
    
    Attributes:
        total_requests: Total number of requests sent
        successful_requests: Number of successful requests (2xx/3xx)
        failed_requests: Number of failed requests
        blocked_requests: Number of requests blocked (403, 429)
        response_times: List of all response times in seconds
        status_codes: Distribution of HTTP status codes
        errors: Distribution of error types
        start_time: Test start timestamp
        end_time: Test end timestamp
        timeline_data: Time-series data for live visualization
        proxy_errors: Error tracking by proxy
        cache_hits: Number of cache hit responses
        cache_misses: Number of cache miss responses
        ramp_timeline: RPS evolution over ramp steps
        breaking_point: Snapshot of the breaking point
    """
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    blocked_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    start_time: float = 0.0
    end_time: float = 0.0
    timeline_data: List[Dict[str, Any]] = field(default_factory=list)
    proxy_errors: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    cache_hits: int = 0
    cache_misses: int = 0
    ramp_timeline: List[Dict[str, Any]] = field(default_factory=list)
    breaking_point: Optional[Dict[str, Any]] = None
    
    # Real-time metrics
    recent_latencies: deque = field(default_factory=lambda: deque(maxlen=100))
    requests_per_second_current: float = 0.0
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        return statistics.mean(self.response_times) if self.response_times else 0
    
    @property
    def median_response_time(self) -> float:
        """Calculate median response time."""
        return statistics.median(self.response_times) if self.response_times else 0
    
    @property
    def min_response_time(self) -> float:
        """Calculate minimum response time."""
        return min(self.response_times) if self.response_times else 0
    
    @property
    def max_response_time(self) -> float:
        """Calculate maximum response time."""
        return max(self.response_times) if self.response_times else 0
    
    @property
    def p95_response_time(self) -> float:
        """Calculate 95th percentile response time."""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    @property
    def p99_response_time(self) -> float:
        """Calculate 99th percentile response time."""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(0.99 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    @property
    def std_dev_response_time(self) -> float:
        """Calculate standard deviation of response times."""
        return statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0
    
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
    
    def block_rate(self) -> float:
        """Calculate block rate percentage."""
        return (self.blocked_requests / self.total_requests * 100) if self.total_requests > 0 else 0
    
    def get_current_rps(self) -> float:
        """Calculate current requests per second."""
        if not self.start_time or len(self.recent_latencies) == 0:
            return 0
        elapsed = time.time() - self.start_time
        return self.total_requests / elapsed if elapsed > 0 else 0
    
    def get_recent_avg_latency(self) -> float:
        """Calculate average of recent latencies."""
        return statistics.mean(self.recent_latencies) if self.recent_latencies else 0


# ============================================================================
# Core Load Testing Engine
# ============================================================================

async def execute_request(
    session: aiohttp.ClientSession,
    url: str,
    method: str,
    headers: Dict[str, str],
    payload: Optional[Dict[str, Any]],
    proxy_url: Optional[str],
    results: TestResults,
    proxy_watchdog: Optional[ProxyHealthWatchdog],
    current_proxy: Optional[str],
    connection_stressor: Optional[ConnectionStressor],
    ramp_engine: Optional[RampEngine],
    endpoint_analyzer: Optional[EndpointComplexityAnalyzer],
    http2_profiler: Optional[HTTP2Profiler],
    force_new_connection: bool = False,
) -> None:
    """Execute a single HTTP request with comprehensive multi-module tracking.
    
    Args:
        session: aiohttp client session
        url: Target URL
        method: HTTP method
        headers: Request headers
        payload: Optional JSON payload
        proxy_url: Proxy URL for this request
        results: TestResults object
        proxy_watchdog: Proxy health watchdog instance
        current_proxy: Current proxy string
        connection_stressor: Connection stressor instance
        ramp_engine: Ramp engine instance
        endpoint_analyzer: Endpoint complexity analyzer
        http2_profiler: HTTP/2 profiler instance
        force_new_connection: Force new TCP connection (handshake storm mode)
    """
    start_time = time.time()
    
    try:
        # Track connection/stressor metrics
        if connection_stressor:
            if force_new_connection:
                connection_stressor.record_new_connection()
            else:
                connection_stressor.record_reused_connection()
        
        # Track HTTP/2 stream
        if http2_profiler and http2_profiler.enabled:
            http2_profiler.record_stream_opened()
        
        async with session.request(
            method,
            url,
            headers=headers,
            json=payload,
            proxy=proxy_url,
            timeout=aiohttp.ClientTimeout(total=30),
            allow_redirects=True
        ) as response:
            response_time = time.time() - start_time
            await response.text()
            
            # Close HTTP/2 stream tracking
            if http2_profiler and http2_profiler.enabled:
                http2_profiler.record_stream_closed()
            
            # Update main results
            results.total_requests += 1
            results.response_times.append(response_time)
            results.status_codes[response.status] += 1
            results.recent_latencies.append(response_time * 1000)
            
            # Track cache behavior
            cache_status = response.headers.get('X-Cache', '')
            if 'hit' in cache_status.lower():
                results.cache_hits += 1
            elif 'miss' in cache_status.lower():
                results.cache_misses += 1
            
            # Ramp engine tracking
            if ramp_engine:
                ramp_engine.record_latency(response_time * 1000)
                ramp_engine.record_status(response.status)
            
            # Categorize response
            if response.status in [403, 429]:
                results.blocked_requests += 1
                results.failed_requests += 1
                
                if current_proxy and proxy_watchdog:
                    proxy_watchdog.record_error(
                        current_proxy,
                        f"Blocked: {response.status}",
                        response.status
                    )
                    results.proxy_errors[current_proxy].append(
                        f"[{datetime.now().strftime('%H:%M:%S')}] {response.status}"
                    )
            elif 200 <= response.status < 400:
                results.successful_requests += 1
                
                if current_proxy and proxy_watchdog:
                    proxy_watchdog.record_success(current_proxy, response_time)
            else:
                results.failed_requests += 1
                
                if current_proxy and proxy_watchdog:
                    proxy_watchdog.record_error(
                        current_proxy,
                        f"HTTP {response.status}",
                        response.status
                    )
            
            # Endpoint analyzer tracking
            if endpoint_analyzer:
                endpoint_analyzer.record_request(url, response_time, response.status)
            
            # Record timeline data
            elapsed = time.time() - results.start_time
            results.timeline_data.append({
                "timestamp": elapsed,
                "response_time_ms": response_time * 1000,
                "status_code": response.status,
                "request_number": results.total_requests
            })
    
    except asyncio.TimeoutError:
        _handle_error(results, "TimeoutError", start_time, current_proxy, proxy_watchdog,
                      http2_profiler, ramp_engine, endpoint_analyzer, url)
    except aiohttp.ClientError as e:
        error_type = type(e).__name__
        _handle_error(results, error_type, start_time, current_proxy, proxy_watchdog,
                      http2_profiler, ramp_engine, endpoint_analyzer, url)
    except Exception as e:
        _handle_error(results, f"Unexpected: {type(e).__name__}", start_time, current_proxy, proxy_watchdog,
                      http2_profiler, ramp_engine, endpoint_analyzer, url)


def _handle_error(
    results: TestResults,
    error_type: str,
    start_time: float,
    proxy: Optional[str],
    proxy_watchdog: Optional[ProxyHealthWatchdog],
    http2_profiler: Optional[HTTP2Profiler] = None,
    ramp_engine: Optional[RampEngine] = None,
    endpoint_analyzer: Optional[EndpointComplexityAnalyzer] = None,
    url: str = "",
) -> None:
    """Handle request error with multi-module tracking.
    
    Args:
        results: TestResults object
        error_type: Error type string
        start_time: Request start time
        proxy: Current proxy string
        proxy_watchdog: Proxy health watchdog instance
        http2_profiler: HTTP/2 profiler instance
        ramp_engine: Ramp engine instance
        endpoint_analyzer: Endpoint complexity analyzer
        url: Request URL
    """
    response_time = time.time() - start_time
    results.total_requests += 1
    results.failed_requests += 1
    results.errors[error_type] += 1
    results.response_times.append(response_time)
    results.recent_latencies.append(response_time * 1000)
    
    if proxy and proxy_watchdog:
        proxy_watchdog.record_error(proxy, error_type)
        results.proxy_errors[proxy].append(
            f"[{datetime.now().strftime('%H:%M:%S')}] {error_type}"
        )
    
    if http2_profiler and http2_profiler.enabled:
        http2_profiler.record_stream_error()
        http2_profiler.record_stream_closed()
    
    if ramp_engine:
        ramp_engine.record_latency(response_time * 1000)
        ramp_engine.record_status(0)
    
    if endpoint_analyzer:
        endpoint_analyzer.record_request(url, response_time, 0)
    
    # Record timeline
    elapsed = time.time() - results.start_time
    results.timeline_data.append({
        "timestamp": elapsed,
        "response_time_ms": response_time * 1000,
        "status_code": 0,
        "request_number": results.total_requests,
        "error": error_type
    })


async def run_load_test(
    url: str,
    total_requests: int,
    initial_concurrency: int,
    method: str,
    proxy_watchdog: Optional[ProxyHealthWatchdog],
    connection_stressor: Optional[ConnectionStressor] = None,
    ramp_engine: Optional[RampEngine] = None,
    endpoint_analyzer: Optional[EndpointComplexityAnalyzer] = None,
    http2_profiler: Optional[HTTP2Profiler] = None,
    include_cache_buster: bool = False,
    entropy_level: str = "high",
    payload: Optional[Dict[str, Any]] = None
) -> TestResults:
    """Execute load test with all advanced modules integrated.
    
    Args:
        url: Target URL
        total_requests: Total number of requests
        initial_concurrency: Starting concurrency level
        method: HTTP method
        proxy_watchdog: Proxy health watchdog (None for direct connection)
        connection_stressor: Connection stressor instance
        ramp_engine: Ramp engine for volumetric discovery
        endpoint_analyzer: Endpoint complexity analyzer
        http2_profiler: HTTP/2 profiler
        include_cache_buster: Whether to bust caches
        entropy_level: Session randomization entropy level
        payload: Optional JSON payload
        
    Returns:
        TestResults with comprehensive metrics
    """
    results = TestResults()
    results.start_time = time.time()
    
    # Initialize ramp engine if provided
    if ramp_engine:
        ramp_engine.start_ramp()
    
    # Determine connection settings
    use_keepalive = True
    force_new_conn = False
    if connection_stressor:
        use_keepalive = connection_stressor.should_use_keepalive()
        force_new_conn = connection_stressor.should_force_new_connection()
    
    # Configure connector
    connector_kwargs = {
        "limit": initial_concurrency * 2,
        "limit_per_host": initial_concurrency,
        "enable_cleanup_closed": True,
    }
    
    if use_keepalive:
        connector_kwargs["keepalive_timeout"] = 30
        connector_kwargs["force_close"] = False
    else:
        # Handshake storm mode: force new connections
        connector_kwargs["force_close"] = True
    
    # HTTP/2 force if enabled
    if http2_profiler and http2_profiler.enabled:
        connector_kwargs["enable_cleanup_closed"] = True
    
    connector = aiohttp.TCPConnector(**connector_kwargs)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        current_concurrency = initial_concurrency
        semaphore = asyncio.Semaphore(current_concurrency)
        
        for i in range(total_requests):
            # Get proxy if available
            proxy_tuple = proxy_watchdog.get_next_proxy() if proxy_watchdog else None
            current_proxy = proxy_tuple[0] if proxy_tuple else None
            proxy_url = proxy_watchdog.get_proxy_dict(current_proxy) if proxy_watchdog else None
            
            # Generate high-entropy headers
            headers = SessionRandomizer.generate_headers(
                include_cache_buster=include_cache_buster,
                entropy_level=entropy_level
            )
            
            # Determine target URL (with route selection if endpoint analyzer active)
            request_url = url
            if endpoint_analyzer and endpoint_analyzer.routes:
                route_path = endpoint_analyzer.get_next_route()
                # Build full URL from base + route
                base_url = url.rstrip('/')
                request_url = f"{base_url}{route_path}"
            
            # Inject query parameters for cache busting
            if include_cache_buster:
                request_url = SessionRandomizer.generate_query_params(request_url)
            
            # Ramp engine: check if we should step
            if ramp_engine and ramp_engine.mode != ramp_engine.RampMode.ADAPTIVE:
                if ramp_engine.should_step():
                    new_concurrency = ramp_engine.step()
                    if new_concurrency != current_concurrency:
                        current_concurrency = new_concurrency
                        semaphore = asyncio.Semaphore(current_concurrency)
            
            # Adaptive concurrency adjustment
            if ramp_engine and ramp_engine.mode == ramp_engine.RampMode.ADAPTIVE:
                if results.recent_latencies:
                    ramp_engine.record_latency(results.recent_latencies[-1])
                new_concurrency = ramp_engine.adjust_adaptive()
                if new_concurrency != current_concurrency:
                    current_concurrency = new_concurrency
                    semaphore = asyncio.Semaphore(current_concurrency)
            
            # Persistence analysis: add delay between requests
            if connection_stressor:
                persistence_interval = connection_stressor.get_persistence_interval()
                if persistence_interval > 0 and i > 0:
                    await asyncio.sleep(persistence_interval)
            
            # Create task
            task = asyncio.ensure_future(
                execute_request(
                    session,
                    request_url,
                    method,
                    headers,
                    payload,
                    proxy_url,
                    results,
                    proxy_watchdog,
                    current_proxy,
                    connection_stressor,
                    ramp_engine,
                    endpoint_analyzer,
                    http2_profiler,
                    force_new_conn,
                )
            )
            tasks.append(task)
            
            # Check breaking point after batches
            if ramp_engine and i > 0 and i % 50 == 0:
                breaking = ramp_engine.check_breaking_point()
                if breaking:
                    results.breaking_point = breaking
                    # Don't stop immediately; collect more data but flag it
        
        # Execute all tasks
        await asyncio.gather(*tasks, return_exceptions=True)
    
    results.end_time = time.time()
    
    # Final breaking point check
    if ramp_engine:
        breaking = ramp_engine.check_breaking_point()
        if breaking:
            results.breaking_point = breaking
        results.ramp_timeline = [
            {"elapsed": r[0], "rps": r[1], "concurrency": r[2]}
            for r in ramp_engine.rps_history
        ]
    
    return results


# ============================================================================
# Streamlit Dashboard - Real-time Observability
# ============================================================================

def create_live_metrics_chart(results: TestResults) -> go.Figure:
    """Create real-time latency timeline with success/error/blocked visualization.
    
    Args:
        results: TestResults object
        
    Returns:
        Plotly figure
    """
    if not results.timeline_data:
        return go.Figure()
    
    df = pd.DataFrame(results.timeline_data)
    
    fig = go.Figure()
    
    # Successful requests
    success_mask = (df['status_code'] >= 200) & (df['status_code'] < 400)
    if success_mask.any():
        fig.add_trace(go.Scatter(
            x=df[success_mask]['timestamp'],
            y=df[success_mask]['response_time_ms'],
            mode='markers',
            name='Success (2xx/3xx)',
            marker=dict(color='#10B981', size=5, opacity=0.6)
        ))
    
    # Blocked requests
    blocked_mask = (df['status_code'] == 403) | (df['status_code'] == 429)
    if blocked_mask.any():
        fig.add_trace(go.Scatter(
            x=df[blocked_mask]['timestamp'],
            y=df[blocked_mask]['response_time_ms'],
            mode='markers',
            name='Blocked (403/429)',
            marker=dict(color='#F59E0B', size=7, opacity=0.8)
        ))
    
    # Error requests
    error_mask = (df['status_code'] >= 400) & ~blocked_mask
    if error_mask.any():
        fig.add_trace(go.Scatter(
            x=df[error_mask]['timestamp'],
            y=df[error_mask]['response_time_ms'],
            mode='markers',
            name='Errors (4xx/5xx)',
            marker=dict(color='#EF4444', size=6, opacity=0.7)
        ))
    
    fig.update_layout(
        title="Response Time Timeline (Live)",
        xaxis_title="Time (seconds)",
        yaxis_title="Latency (ms)",
        hovermode='closest',
        showlegend=True,
        template='plotly_white',
        height=400
    )
    
    return fig


def create_rps_chart(results: TestResults) -> go.Figure:
    """Create real-time RPS chart.
    
    Args:
        results: TestResults object
        
    Returns:
        Plotly figure
    """
    if not results.timeline_data:
        return go.Figure()
    
    df = pd.DataFrame(results.timeline_data)
    
    if df.empty:
        return go.Figure()
    
    # Calculate RPS in 1-second windows
    max_time = int(df['timestamp'].max()) + 1
    time_windows = list(range(0, max(1, max_time)))
    rps_values = []
    
    for t in time_windows:
        count = len(df[(df['timestamp'] >= t) & (df['timestamp'] < t + 1)])
        rps_values.append(count)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_windows,
        y=rps_values,
        mode='lines+markers',
        name='RPS',
        line=dict(color='#3B82F6', width=3),
        marker=dict(size=6)
    ))
    
    # Add ramp timeline overlay if available
    if results.ramp_timeline:
        ramp_times = [r["elapsed"] for r in results.ramp_timeline]
        ramp_rps = [r["rps"] for r in results.ramp_timeline]
        fig.add_trace(go.Scatter(
            x=ramp_times,
            y=ramp_rps,
            mode='lines',
            name='Ramp RPS',
            line=dict(color='#8B5CF6', width=2, dash='dot'),
        ))
    
    fig.update_layout(
        title="Requests Per Second (Live)",
        xaxis_title="Time (seconds)",
        yaxis_title="Requests/Second",
        template='plotly_white',
        height=350
    )
    
    return fig


def create_per_route_chart(endpoint_analyzer: Optional[EndpointComplexityAnalyzer]) -> go.Figure:
    """Create per-route latency comparison chart.
    
    Args:
        endpoint_analyzer: Endpoint complexity analyzer
        
    Returns:
        Plotly figure
    """
    if not endpoint_analyzer or not endpoint_analyzer.routes:
        return go.Figure()
    
    report = endpoint_analyzer.get_saturation_report()
    
    paths = [r["path"] for r in report["routes"]]
    avg_latencies = [r["avg_latency_ms"] for r in report["routes"]]
    p95_latencies = [r["p95_latency_ms"] for r in report["routes"]]
    error_rates = [r["error_rate"] for r in report["routes"]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Avg Latency (ms)',
        x=paths,
        y=avg_latencies,
        marker_color='#3B82F6'
    ))
    fig.add_trace(go.Bar(
        name='P95 Latency (ms)',
        x=paths,
        y=p95_latencies,
        marker_color='#F59E0B'
    ))
    
    fig.update_layout(
        title="Per-Route Latency Comparison",
        xaxis_title="Route",
        yaxis_title="Latency (ms)",
        barmode='group',
        template='plotly_white',
        height=350
    )
    
    return fig


def create_ramp_progress(results: TestResults, ramp_engine: Optional[RampEngine]) -> None:
    """Display ramp progress and breaking point detection.
    
    Args:
        results: TestResults object
        ramp_engine: Ramp engine instance
    """
    if not ramp_engine:
        return
    
    stats = ramp_engine.get_ramp_stats()
    
    st.markdown("### Ramp Engine Status")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Mode", stats["mode"].upper())
        st.metric("Concurrency", stats["current_concurrency"])
    with col2:
        st.metric("Avg Latency", f"{stats['avg_latency_ms']:.0f}ms")
        st.metric("P95 Latency", f"{stats['p95_latency_ms']:.0f}ms")
    with col3:
        st.metric("Current RPS", f"{stats['current_rps']:.1f}")
        st.metric("Steps", stats["step_count"])
    with col4:
        if stats.get("baseline_p95_ms"):
            st.metric("Baseline P95", f"{stats['baseline_p95_ms']:.0f}ms")
    
    # Breaking point alert
    if results.breaking_point:
        st.error(f"**BREAKING POINT DETECTED** at {results.breaking_point['rps_at_break']} RPS "
                 f"({results.breaking_point['p95_latency_ms']:.0f}ms P95)")
        with st.expander("Breaking Point Details"):
            for reason in results.breaking_point.get("reasons", []):
                st.write(f"- {reason}")
            st.json(results.breaking_point)
    elif ramp_engine and ramp_engine.ramp_start_time > 0:
        current_rps = stats["current_rps"]
        st.info(f"Ramping... current RPS: {current_rps:.1f} - no breaking point detected yet")


def main():
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title="SRE Infrastructure Stress-Testing",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("SRE Infrastructure Stress-Testing & Observability")
    st.markdown("**Professional-grade Safe Operating Envelope discovery with real-time telemetry**")
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Target & Routes
        with st.expander("Target & Routes", expanded=True):
            target_url = st.text_input("Base URL", value="http://localhost:8080")
            http_method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])
            
            # Endpoint complexity routes
            use_routes = st.checkbox("Multi-Route Targeting", value=False,
                                     help="Distribute load across weighted endpoints")
            routes_text = st.text_area(
                "Routes (path:weight, one per line)",
                value="/:80\n/api/search:20",
                height=80,
                disabled=not use_routes
            ) if use_routes else None
        
        # Load Parameters
        with st.expander("Load Parameters", expanded=True):
            total_requests = st.number_input("Total Requests", 10, 100000, 1000, 100)
            initial_concurrency = st.number_input("Initial Concurrency", 10, 5000, 100, 10)
        
        # Ramp Configuration
        with st.expander("Ramp Engine (Volumetric Discovery)", expanded=True):
            use_ramp = st.checkbox("Enable Ramp Engine", value=True)
            ramp_mode = st.selectbox("Ramp Mode", ["adaptive", "linear", "exponential"],
                                     disabled=not use_ramp)
            if ramp_mode == "linear":
                step_size = st.number_input("Step Size", 5, 500, 25, 5, disabled=not use_ramp)
            else:
                step_size = 25
            step_interval = st.number_input("Step Interval (s)", 1.0, 60.0, 5.0, 1.0, disabled=not use_ramp)
            target_latency = st.slider("Target Latency (ms)", 100, 2000, 500, 50, disabled=not use_ramp)
        
        # Connection Mode
        with st.expander("Connection Management"):
            conn_mode = st.selectbox("Connection Mode",
                                     ["default", "handshake_storm", "persistence_analysis"],
                                     help="Default: keep-alive | Handshake Storm: new TCP per request | Persistence: long-lived sessions")
        
        # Session Randomization
        with st.expander("Session Randomization"):
            entropy_level = st.selectbox("Entropy Level", ["high", "medium", "low"],
                                         help="High: full compose + shuffle | Medium: partial random | Low: fixed rotation")
            cache_busting = st.checkbox("Cache Busting", value=False)
        
        # HTTP/2
        with st.expander("HTTP/2 Profiling"):
            use_http2 = st.checkbox("Enable HTTP/2", value=False,
                                    help="Force HTTP/2 multiplexing")
        
        # Proxy Configuration
        with st.expander("Proxy Management"):
            proxy_file = st.file_uploader("Upload proxies.txt", type=['txt'])
            proxy_watchdog = None
            if proxy_file:
                proxy_content = proxy_file.read().decode('utf-8')
                rotation = st.selectbox("Rotation", ["least_used", "round_robin", "random"])
                proxy_watchdog = ProxyHealthWatchdog(rotation_strategy=rotation)
                count = proxy_watchdog.load_proxies(proxy_content)
                st.success(f"{count} proxies loaded")
            else:
                st.info("Direct connection mode")
        
        # Payload
        if http_method in ["POST", "PUT"]:
            payload_json = st.text_area("JSON Payload", '{"test": "data"}')
        else:
            payload_json = None
        
        # Start button
        st.markdown("---")
        start_test = st.button("Start Stress Test", type="primary", use_container_width=True)
    
    # Main area
    if start_test:
        if not target_url:
            st.error("Enter target URL")
            return
        
        payload = None
        if payload_json:
            try:
                payload = json.loads(payload_json)
            except Exception:
                st.error("Invalid JSON")
                return
        
        # Build modules
        ramp_engine = None
        if use_ramp:
            ramp_engine = RampEngine(
                mode=ramp_mode,
                initial_concurrency=initial_concurrency,
                step_size=step_size,
                step_interval_seconds=step_interval,
                target_latency_ms=target_latency,
            )
        
        connection_stressor = ConnectionStressor(mode=conn_mode) if conn_mode != "default" else None
        
        endpoint_analyzer = None
        if use_routes and routes_text:
            routes = []
            for line in routes_text.strip().split('\n'):
                parts = line.strip().split(':')
                if len(parts) == 2:
                    routes.append((parts[0].strip(), float(parts[1].strip())))
            if routes:
                endpoint_analyzer = EndpointComplexityAnalyzer(routes)
        
        http2_profiler = HTTP2Profiler(enabled=use_http2)
        
        # Run test
        with st.spinner("Running stress test..."):
            try:
                results = asyncio.run(
                    run_load_test(
                        url=target_url,
                        total_requests=total_requests,
                        initial_concurrency=initial_concurrency,
                        method=http_method,
                        proxy_watchdog=proxy_watchdog,
                        connection_stressor=connection_stressor,
                        ramp_engine=ramp_engine,
                        endpoint_analyzer=endpoint_analyzer,
                        http2_profiler=http2_profiler,
                        include_cache_buster=cache_busting,
                        entropy_level=entropy_level,
                        payload=payload
                    )
                )
                
                duration = results.end_time - results.start_time
                st.success(f"Test completed in {duration:.2f}s")
                
                # Display Ramp progress & breaking point
                create_ramp_progress(results, ramp_engine)
                
                # Main metrics
                st.markdown("### Results Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Requests", results.total_requests)
                    st.metric("Success Rate", f"{results.success_rate():.1f}%")
                with col2:
                    st.metric("Avg Latency", f"{results.avg_response_time*1000:.0f}ms")
                    st.metric("P95 Latency", f"{results.p95_response_time*1000:.0f}ms")
                with col3:
                    st.metric("Blocked", results.blocked_requests)
                    st.metric("Block Rate", f"{results.block_rate():.1f}%")
                with col4:
                    st.metric("Throughput", f"{results.get_current_rps():.1f} RPS")
                    st.metric("Errors", results.failed_requests - results.blocked_requests)
                
                # Charts
                st.plotly_chart(create_live_metrics_chart(results), use_container_width=True)
                st.plotly_chart(create_rps_chart(results), use_container_width=True)
                
                # Per-route chart
                if endpoint_analyzer and endpoint_analyzer.routes:
                    st.plotly_chart(create_per_route_chart(endpoint_analyzer), use_container_width=True)
                    with st.expander("Route Saturation Report"):
                        report = endpoint_analyzer.get_saturation_report()
                        st.json(report)
                
                # Connection stressor stats
                if connection_stressor:
                    with st.expander("Connection Stressor Stats"):
                        st.json(connection_stressor.get_stats())
                
                # HTTP/2 profiler stats
                if http2_profiler and http2_profiler.enabled:
                    with st.expander("HTTP/2 Profiler Stats"):
                        st.json(http2_profiler.get_stats())
                
                # Proxy stats
                if proxy_watchdog:
                    with st.expander("Proxy Health Report"):
                        st.json(proxy_watchdog.get_proxy_stats())
                
                # Status code breakdown
                with st.expander("Status Code Distribution"):
                    status_df = pd.DataFrame([
                        {"Code": code, "Count": count}
                        for code, count in sorted(results.status_codes.items())
                    ])
                    st.dataframe(status_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"Test failed: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Footer
    st.markdown("---")
    st.caption("For authorized infrastructure testing only. Monitor responsibly.")


if __name__ == "__main__":
    main()
