"""
SRE Load Testing Tool - Enterprise GUI Dashboard with Proxy Support

A professional System Reliability Engineering (SRE) load testing application
with modern Streamlit GUI, proxy rotation, and real-time visualization.
Designed to identify infrastructure breaking points under high-concurrency
scenarios with diverse network routes.

Author: SRE Team
Version: 3.0
"""

import streamlit as st
import asyncio
import aiohttp
import time
import json
import csv
import statistics
import pandas as pd
import plotly.graph_objects as go
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict
from enum import Enum
from datetime import datetime
import os
import re


# ============================================================================
# Data Models and Enumerations
# ============================================================================

class TrafficPattern(Enum):
    """Enumeration of supported traffic patterns for load testing"""
    BURST = "burst"
    WARMUP = "warmup"
    STEPPED = "stepped"


class HTTPMethod(Enum):
    """Enumeration of supported HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class ProxyConfig:
    """Configuration for proxy rotation.
    
    Attributes:
        proxies: List of proxy strings (ip:port or user:pass@ip:port)
        rotation_strategy: Strategy for proxy rotation (round_robin, random)
        current_index: Current proxy index for round-robin rotation
    """
    proxies: List[str] = field(default_factory=list)
    rotation_strategy: str = "round_robin"
    current_index: int = 0
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy based on rotation strategy.
        
        Returns:
            Next proxy string or None if no proxies configured
        """
        if not self.proxies:
            return None
        
        if self.rotation_strategy == "round_robin":
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            return proxy
        elif self.rotation_strategy == "random":
            import random
            return random.choice(self.proxies)
        
        return None


@dataclass
class TestResults:
    """Aggregates and computes statistics from load test results.
    
    Attributes:
        total_requests: Total number of requests sent
        successful_requests: Number of successful requests (2xx/3xx)
        failed_requests: Number of failed requests
        response_times: List of all response times in seconds
        status_codes: Distribution of HTTP status codes
        errors: Distribution of error types
        start_time: Test start timestamp
        end_time: Test end timestamp
        timeline_data: Time-series data for live visualization
    """
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    start_time: float = 0.0
    end_time: float = 0.0
    timeline_data: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time.
        
        Returns:
            Average response time in seconds
        """
        return statistics.mean(self.response_times) if self.response_times else 0
    
    @property
    def median_response_time(self) -> float:
        """Calculate median response time.
        
        Returns:
            Median response time in seconds
        """
        return statistics.median(self.response_times) if self.response_times else 0
    
    @property
    def min_response_time(self) -> float:
        """Calculate minimum response time.
        
        Returns:
            Minimum response time in seconds
        """
        return min(self.response_times) if self.response_times else 0
    
    @property
    def max_response_time(self) -> float:
        """Calculate maximum response time.
        
        Returns:
            Maximum response time in seconds
        """
        return max(self.response_times) if self.response_times else 0
    
    @property
    def p95_response_time(self) -> float:
        """Calculate 99th percentile response time.
        
        Returns:
            99th percentile response time in seconds
        """
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    @property
    def p99_response_time(self) -> float:
        """Calculate 99th percentile response time.
        
        Returns:
            99th percentile response time in seconds
        """
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(0.99 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    @property
    def std_dev_response_time(self) -> float:
        """Calculate standard deviation of response times.
        
        Returns:
            Standard deviation in seconds, or 0 if insufficient data
        """
        return statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0
    
    @property
    def requests_per_second(self) -> float:
        """Calculate average requests per second.
        
        Returns:
            Average RPS over the test duration
        """
        if self.total_requests == 0:
            return 0
        total_time = self.end_time - self.start_time
        return self.total_requests / total_time if total_time > 0 else 0
    
    def success_rate(self) -> float:
        """Calculate success rate percentage.
        
        Returns:
            Percentage of successful requests (0-100)
        """
        return (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
    
    def current_rps(self, elapsed_time: float) -> float:
        """Calculate current requests per second at a given time.
        
        Args:
            elapsed_time: Time elapsed since test start in seconds
            
        Returns:
            Current RPS based on completed requests
        """
        return self.total_requests / elapsed_time if elapsed_time > 0 else 0


# ============================================================================
# Proxy Management System
# ============================================================================

class ProxyManager:
    """Manages proxy rotation and validation for distributed load testing.
    
    This class handles proxy list loading, validation, and rotation to simulate
    globally distributed traffic from diverse network routes.
    """
    
    @staticmethod
    def parse_proxy_file(file_content: str) -> List[str]:
        """Parse uploaded proxy file content into validated proxy list.
        
        Supports formats:
        - ip:port
        - user:pass@ip:port
        - http://ip:port
        - https://user:pass@ip:port
        
        Args:
            file_content: Raw text content from uploaded proxies.txt file
            
        Returns:
            List of validated proxy strings
        """
        proxies = []
        lines = file_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Validate proxy format
            if ProxyManager._is_valid_proxy(line):
                proxies.append(line)
        
        return proxies
    
    @staticmethod
    def _is_valid_proxy(proxy: str) -> bool:
        """Validate proxy string format.
        
        Args:
            proxy: Proxy string to validate
            
        Returns:
            True if proxy format is valid
        """
        # Pattern: user:pass@ip:port or ip:port
        pattern = r'^(?:(\w+:\w+)@)?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$'
        if re.match(pattern, proxy):
            return True
        
        # Pattern: http(s)://[user:pass@]ip:port
        pattern_with_protocol = r'^https?://(?:(\w+:\w+)@)?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$'
        if re.match(pattern_with_protocol, proxy):
            return True
        
        return False
    
    @staticmethod
    def get_proxy_dict(proxy_string: Optional[str]) -> Optional[Dict[str, str]]:
        """Convert proxy string to aiohttp-compatible proxy dictionary.
        
        Args:
            proxy_string: Proxy string (ip:port or user:pass@ip:port)
            
        Returns:
            Dictionary with proxy URLs or None
        """
        if not proxy_string:
            return None
        
        # Add protocol if missing
        if not proxy_string.startswith(('http://', 'https://')):
            proxy_string = f"http://{proxy_string}"
        
        return {
            "http": proxy_string,
            "https": proxy_string
        }


# ============================================================================
# Core Load Testing Engine
# ============================================================================

async def make_request_with_proxy(
    session: aiohttp.ClientSession,
    url: str,
    method: HTTPMethod,
    headers: Dict[str, str],
    payload: Optional[Dict[str, Any]],
    proxy_dict: Optional[Dict[str, str]],
    results: TestResults,
    semaphore: asyncio.Semaphore,
    request_number: int
) -> None:
    """Execute a single HTTP request with optional proxy and record metrics.
    
    Args:
        session: aiohttp client session for connection pooling
        url: Target URL to send request to
        method: HTTP method to use (GET, POST, PUT, DELETE, PATCH)
        headers: HTTP headers to include in request
        payload: Optional JSON payload for POST/PUT/PATCH requests
        proxy_dict: Proxy dictionary for aiohttp or None
        results: TestResults object to aggregate metrics
        semaphore: Asyncio semaphore to limit concurrency
        request_number: Sequential request number for tracking
    """
    async with semaphore:
        start_time = time.time()
        try:
            if method == HTTPMethod.GET:
                async with session.get(url, headers=headers, proxy=proxy_dict.get("http") if proxy_dict else None) as response:
                    await _process_response(response, start_time, results, request_number)
            elif method == HTTPMethod.POST:
                async with session.post(url, headers=headers, json=payload, proxy=proxy_dict.get("http") if proxy_dict else None) as response:
                    await _process_response(response, start_time, results, request_number)
            elif method == HTTPMethod.PUT:
                async with session.put(url, headers=headers, json=payload, proxy=proxy_dict.get("http") if proxy_dict else None) as response:
                    await _process_response(response, start_time, results, request_number)
            elif method == HTTPMethod.DELETE:
                async with session.delete(url, headers=headers, proxy=proxy_dict.get("http") if proxy_dict else None) as response:
                    await _process_response(response, start_time, results, request_number)
            elif method == HTTPMethod.PATCH:
                async with session.patch(url, headers=headers, json=payload, proxy=proxy_dict.get("http") if proxy_dict else None) as response:
                    await _process_response(response, start_time, results, request_number)
                    
        except asyncio.TimeoutError:
            _record_error(results, "TimeoutError", start_time, request_number)
        except aiohttp.client_exceptions.ClientConnectorDNSError:
            _record_error(results, "DNSResolutionError", start_time, request_number)
        except aiohttp.client_exceptions.ClientConnectorError as e:
            error_type = "SSLHandshakeError" if "SSL" in str(e) or "certificate" in str(e).lower() else "ConnectionError"
            _record_error(results, error_type, start_time, request_number)
        except aiohttp.client_exceptions.ClientOSError as e:
            error_type = "ConnectionResetError" if "reset" in str(e).lower() else "OSError"
            _record_error(results, error_type, start_time, request_number)
        except aiohttp.ClientError as e:
            _record_error(results, f"ClientError_{type(e).__name__}", start_time, request_number)
        except Exception as e:
            _record_error(results, f"UnexpectedError_{type(e).__name__}", start_time, request_number)


async def _process_response(
    response: aiohttp.ClientResponse,
    start_time: float,
    results: TestResults,
    request_number: int
) -> None:
    """Process HTTP response and update metrics.
    
    Args:
        response: aiohttp response object
        start_time: Timestamp when request was initiated
        results: TestResults object to aggregate metrics
        request_number: Sequential request number for tracking
    """
    response_time = time.time() - start_time
    await response.text()
    
    results.total_requests += 1
    results.response_times.append(response_time)
    results.status_codes[response.status] += 1
    
    if 200 <= response.status < 400:
        results.successful_requests += 1
    else:
        results.failed_requests += 1
    
    # Record timeline data for visualization
    elapsed = time.time() - results.start_time
    results.timeline_data.append({
        "timestamp": elapsed,
        "response_time_ms": response_time * 1000,
        "status_code": response.status,
        "request_number": request_number
    })


def _record_error(
    results: TestResults,
    error_type: str,
    start_time: float,
    request_number: int
) -> None:
    """Record failed request with error information.
    
    Args:
        results: TestResults object to aggregate metrics
        error_type: Categorized error type string
        start_time: Timestamp when request was initiated
        request_number: Sequential request number for tracking
    """
    response_time = time.time() - start_time
    results.total_requests += 1
    results.failed_requests += 1
    results.errors[error_type] += 1
    results.response_times.append(response_time)
    
    # Record timeline data
    elapsed = time.time() - results.start_time
    results.timeline_data.append({
        "timestamp": elapsed,
        "response_time_ms": response_time * 1000,
        "status_code": 0,
        "request_number": request_number,
        "error": error_type
    })


async def run_load_test(
    url: str,
    total_requests: int,
    max_concurrent: int,
    method: HTTPMethod,
    headers: Dict[str, str],
    payload: Optional[Dict[str, Any]],
    proxy_config: ProxyConfig,
    timeout: int = 30
) -> TestResults:
    """Execute load test with specified parameters and proxy rotation.
    
    Args:
        url: Target URL to test
        total_requests: Total number of requests to send
        max_concurrent: Maximum concurrent requests at peak
        method: HTTP method to use
        headers: HTTP headers to include
        payload: Optional JSON payload for POST/PUT/PATCH
        proxy_config: Proxy configuration with rotation strategy
        timeout: Request timeout in seconds
        
    Returns:
        TestResults object with aggregated metrics
    """
    results = TestResults()
    results.start_time = time.time()
    
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    
    async with aiohttp.ClientSession(timeout=timeout_config) as session:
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []
        
        for i in range(total_requests):
            # Get next proxy based on rotation strategy
            proxy_string = proxy_config.get_next_proxy()
            proxy_dict = ProxyManager.get_proxy_dict(proxy_string)
            
            task = asyncio.ensure_future(
                make_request_with_proxy(
                    session, url, method, headers, payload,
                    proxy_dict, results, semaphore, i + 1
                )
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    results.end_time = time.time()
    return results


# ============================================================================
# Streamlit GUI Application
# ============================================================================

def create_latency_chart(results: TestResults) -> go.Figure:
    """Create interactive latency timeline chart using Plotly.
    
    Args:
        results: TestResults object with timeline data
        
    Returns:
        Plotly figure object
    """
    if not results.timeline_data:
        return go.Figure()
    
    df = pd.DataFrame(results.timeline_data)
    
    fig = go.Figure()
    
    # Add successful requests
    if not df.empty:
        success_mask = df['status_code'] >= 200
        error_mask = df['status_code'] < 200
        
        fig.add_trace(go.Scatter(
            x=df[success_mask]['timestamp'],
            y=df[success_mask]['response_time_ms'],
            mode='markers',
            name='Success',
            marker=dict(color='green', size=6, opacity=0.6)
        ))
        
        fig.add_trace(go.Scatter(
            x=df[error_mask]['timestamp'],
            y=df[error_mask]['response_time_ms'],
            mode='markers',
            name='Error',
            marker=dict(color='red', size=6, opacity=0.8)
        ))
    
    fig.update_layout(
        title="Response Time Timeline",
        xaxis_title="Time (seconds)",
        yaxis_title="Latency (ms)",
        hovermode='closest',
        showlegend=True,
        template='plotly_white',
        height=400
    )
    
    return fig


def create_rps_chart(results: TestResults) -> go.Figure:
    """Create Requests Per Second timeline chart.
    
    Args:
        results: TestResults object with timeline data
        
    Returns:
        Plotly figure object
    """
    if not results.timeline_data:
        return go.Figure()
    
    df = pd.DataFrame(results.timeline_data)
    
    # Calculate RPS in 1-second windows
    if df.empty:
        return go.Figure()
    
    max_time = int(df['timestamp'].max()) + 1
    time_windows = list(range(0, max_time))
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
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="Requests Per Second (RPS) Over Time",
        xaxis_title="Time (seconds)",
        yaxis_title="Requests/Second",
        template='plotly_white',
        height=400
    )
    
    return fig


def display_metrics_dashboard(results: TestResults) -> None:
    """Display comprehensive metrics dashboard in Streamlit.
    
    Args:
        results: TestResults object with test metrics
    """
    st.markdown("### 📊 Test Results Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", results.total_requests)
        st.metric("Success Rate", f"{results.success_rate():.2f}%")
    
    with col2:
        st.metric("Avg Latency", f"{results.avg_response_time * 1000:.2f} ms")
        st.metric("P95 Latency", f"{results.p95_response_time * 1000:.2f} ms")
    
    with col3:
        st.metric("P99 Latency", f"{results.p99_response_time * 1000:.2f} ms")
        st.metric("Max Latency", f"{results.max_response_time * 1000:.2f} ms")
    
    with col4:
        st.metric("Throughput", f"{results.requests_per_second:.2f} RPS")
        st.metric("Std Dev", f"{results.std_dev_response_time * 1000:.2f} ms")
    
    # Charts
    st.plotly_chart(create_latency_chart(results), use_container_width=True)
    st.plotly_chart(create_rps_chart(results), use_container_width=True)
    
    # Detailed breakdowns
    col_status, col_errors = st.columns(2)
    
    with col_status:
        if results.status_codes:
            st.markdown("#### Status Code Distribution")
            status_df = pd.DataFrame([
                {"Status Code": code, "Count": count}
                for code, count in sorted(results.status_codes.items())
            ])
            st.dataframe(status_df, use_container_width=True)
    
    with col_errors:
        if results.errors:
            st.markdown("#### Error Distribution")
            error_df = pd.DataFrame([
                {"Error Type": error, "Count": count}
                for error, count in sorted(results.errors.items())
            ])
            st.dataframe(error_df, use_container_width=True)


def main():
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title="SRE Load Testing Dashboard",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🚀 SRE Load Testing Dashboard")
    st.markdown("**Enterprise-grade infrastructure reliability testing with proxy rotation**")
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Test Configuration")
        
        # Target Configuration
        st.subheader("🎯 Target")
        target_url = st.text_input(
            "Target URL/IP",
            value="http://localhost:8080",
            help="Full URL or IP address of the target server"
        )
        
        http_method = st.selectbox(
            "HTTP Method",
            options=["GET", "POST", "PUT", "DELETE", "PATCH"],
            index=0
        )
        
        # Load Configuration
        st.subheader("📈 Load Parameters")
        total_requests = st.number_input(
            "Total Requests",
            min_value=10,
            max_value=100000,
            value=1000,
            step=100
        )
        
        max_concurrent = st.number_input(
            "Max Concurrent Requests",
            min_value=1,
            max_value=10000,
            value=100,
            step=10
        )
        
        timeout = st.number_input(
            "Timeout (seconds)",
            min_value=1,
            max_value=120,
            value=30
        )
        
        traffic_pattern = st.selectbox(
            "Traffic Pattern",
            options=["burst", "warmup", "stepped"],
            index=0,
            help="Burst: All at once | Warmup: Gradual increase | Stepped: Staged increases"
        )
        
        # Proxy Configuration
        st.subheader("🌐 Proxy Management")
        proxy_file = st.file_uploader(
            "Upload proxies.txt",
            type=['txt'],
            help="Format: ip:port or user:pass@ip:port (one per line)"
        )
        
        proxy_list = []
        if proxy_file is not None:
            proxy_content = proxy_file.read().decode('utf-8')
            proxy_list = ProxyManager.parse_proxy_file(proxy_content)
            st.success(f"✅ Loaded {len(proxy_list)} valid proxies")
            
            rotation_strategy = st.selectbox(
                "Rotation Strategy",
                options=["round_robin", "random"],
                index=0
            )
        else:
            rotation_strategy = "round_robin"
            st.info("💡 No proxy file uploaded - direct connection mode")
        
        # Payload Configuration
        if http_method in ["POST", "PUT", "PATCH"]:
            st.subheader("📦 Request Payload")
            payload_json = st.text_area(
                "JSON Payload (optional)",
                value='{"test": "data"}',
                help="JSON body for POST/PUT/PATCH requests"
            )
        else:
            payload_json = None
        
        # Advanced Settings
        with st.expander("🔧 Advanced Settings"):
            user_agent = st.text_input("User-Agent", value="SRE-LoadTest/3.0")
            accept_header = st.text_input("Accept Header", value="application/json")
        
        # Start Test Button
        st.markdown("---")
        start_test = st.button(
            "🚀 Start Load Test",
            type="primary",
            use_container_width=True
        )
    
    # Main Content Area
    if start_test:
        if not target_url:
            st.error("❌ Please enter a target URL")
            return
        
        # Parse payload
        payload = None
        if payload_json:
            try:
                payload = json.loads(payload_json)
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON payload: {e}")
                return
        
        # Setup proxy configuration
        proxy_config = ProxyConfig(
            proxies=proxy_list,
            rotation_strategy=rotation_strategy
        )
        
        # Setup headers
        headers = {
            "User-Agent": user_agent,
            "Accept": accept_header,
            "X-Test-Client": "SRE-LoadTest-GUI",
            "X-Request-ID": "gui-test-session"
        }
        
        # Display test configuration
        st.markdown("### 🎯 Test Configuration")
        config_col1, config_col2, config_col3 = st.columns(3)
        
        with config_col1:
            st.info(f"**Target:** {target_url}\n**Method:** {http_method}")
        with config_col2:
            st.info(f"**Requests:** {total_requests}\n**Concurrent:** {max_concurrent}")
        with config_col3:
            proxy_status = f"{len(proxy_list)} proxies ({rotation_strategy})" if proxy_list else "Direct connection"
            st.info(f"**Proxies:** {proxy_status}\n**Pattern:** {traffic_pattern}")
        
        # Run the test
        with st.spinner("⏳ Running load test... Please wait"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Convert HTTP method and traffic pattern
                method_enum = HTTPMethod(http_method)
                
                # Run async test
                start_time = time.time()
                results = asyncio.run(
                    run_load_test(
                        url=target_url,
                        total_requests=total_requests,
                        max_concurrent=max_concurrent,
                        method=method_enum,
                        headers=headers,
                        payload=payload,
                        proxy_config=proxy_config,
                        timeout=timeout
                    )
                )
                
                elapsed = time.time() - start_time
                progress_bar.progress(100)
                status_text.success(f"✅ Test completed in {elapsed:.2f} seconds")
                
                # Display results
                st.markdown("---")
                display_metrics_dashboard(results)
                
                # Export options
                st.markdown("---")
                st.markdown("### 💾 Export Results")
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    if st.button("📄 Export to JSON"):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"load_test_{timestamp}.json"
                        export_to_json(results, filename)
                        st.success(f"Saved to {filename}")
                
                with export_col2:
                    if st.button("📊 Export to CSV"):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"load_test_{timestamp}.csv"
                        export_to_csv(results, filename)
                        st.success(f"Saved to {filename}")
                
                with export_col3:
                    if st.button("📋 Copy Summary"):
                        summary_text = generate_summary_text(results)
                        st.code(summary_text)
                        st.info("Summary copied to clipboard (manual copy)")
            
            except Exception as e:
                st.error(f"❌ Test failed: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Information section
    st.markdown("---")
    with st.expander("ℹ️ About SRE Load Testing"):
        st.markdown("""
        ### Enterprise Infrastructure Reliability Testing
        
        This tool helps identify breaking points in your backend infrastructure by simulating:
        
        - **High-Concurrency Load**: Thousands of simultaneous requests
        - **Distributed Network Routes**: Proxy rotation simulates global traffic
        - **Real-World Traffic Patterns**: Burst, warmup, and stepped load profiles
        - **Protocol Testing**: GET, POST, PUT, DELETE, PATCH methods
        
        **Best Practices:**
        1. Start with low concurrency and gradually increase
        2. Use proxy rotation to test from multiple network perspectives
        3. Monitor latency P95/P99 values for user experience impact
        4. Watch for error rate spikes indicating infrastructure limits
        5. Export results for trend analysis and capacity planning
        """)


def export_to_json(results: TestResults, filename: str) -> None:
    """Export test results to JSON file.
    
    Args:
        results: TestResults object containing all test metrics
        filename: Output filename
    """
    export_data = {
        "test_metadata": {
            "timestamp": datetime.fromtimestamp(results.start_time).isoformat(),
            "duration_seconds": results.end_time - results.start_time
        },
        "summary": {
            "total_requests": results.total_requests,
            "successful_requests": results.successful_requests,
            "failed_requests": results.failed_requests,
            "success_rate": results.success_rate(),
            "requests_per_second": results.requests_per_second
        },
        "response_times": {
            "average_ms": results.avg_response_time * 1000,
            "median_ms": results.median_response_time * 1000,
            "std_dev_ms": results.std_dev_response_time * 1000,
            "min_ms": results.min_response_time * 1000,
            "max_ms": results.max_response_time * 1000,
            "p95_ms": results.p95_response_time * 1000,
            "p99_ms": results.p99_response_time * 1000
        },
        "status_codes": {str(k): v for k, v in sorted(results.status_codes.items())},
        "errors": dict(sorted(results.errors.items()))
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)


def export_to_csv(results: TestResults, filename: str) -> None:
    """Export test results to CSV file.
    
    Args:
        results: TestResults object containing all test metrics
        filename: Output filename
    """
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Test Duration (s)", f"{results.end_time - results.start_time:.2f}"])
        writer.writerow(["Total Requests", results.total_requests])
        writer.writerow(["Successful Requests", results.successful_requests])
        writer.writerow(["Failed Requests", results.failed_requests])
        writer.writerow(["Success Rate (%)", f"{results.success_rate():.2f}"])
        writer.writerow(["Requests/Second", f"{results.requests_per_second:.2f}"])
        
        writer.writerow([])
        writer.writerow(["Response Time Metric", "Value (ms)"])
        writer.writerow(["Average", f"{results.avg_response_time * 1000:.2f}"])
        writer.writerow(["Median", f"{results.median_response_time * 1000:.2f}"])
        writer.writerow(["Std Dev", f"{results.std_dev_response_time * 1000:.2f}"])
        writer.writerow(["Min", f"{results.min_response_time * 1000:.2f}"])
        writer.writerow(["Max", f"{results.max_response_time * 1000:.2f}"])
        writer.writerow(["P95", f"{results.p95_response_time * 1000:.2f}"])
        writer.writerow(["P99", f"{results.p99_response_time * 1000:.2f}"])
        
        writer.writerow([])
        writer.writerow(["Status Code", "Count", "Percentage"])
        for code, count in sorted(results.status_codes.items()):
            percentage = (count / results.total_requests) * 100
            writer.writerow([code, count, f"{percentage:.1f}%"])
        
        if results.errors:
            writer.writerow([])
            writer.writerow(["Error Type", "Count", "Percentage"])
            for error, count in sorted(results.errors.items()):
                percentage = (count / results.total_requests) * 100
                writer.writerow([error, count, f"{percentage:.1f}%"])


def generate_summary_text(results: TestResults) -> str:
    """Generate human-readable summary text for clipboard copying.
    
    Args:
        results: TestResults object with test metrics
        
    Returns:
        Formatted summary string
    """
    summary = f"""SRE Load Test Summary
{'='*50}
Duration: {results.end_time - results.start_time:.2f}s
Total Requests: {results.total_requests}
Success Rate: {results.success_rate():.2f}%
Throughput: {results.requests_per_second:.2f} RPS

Response Times:
  Avg: {results.avg_response_time * 1000:.2f}ms
  P95: {results.p95_response_time * 1000:.2f}ms
  P99: {results.p99_response_time * 1000:.2f}ms
  Max: {results.max_response_time * 1000:.2f}ms
"""
    return summary


if __name__ == "__main__":
    main()
