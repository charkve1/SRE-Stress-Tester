# 🚀 SRE Load Testing Dashboard - Quick Start Guide

## Enterprise Infrastructure Reliability Testing with GUI & Proxy Support

### 📦 Installation

```bash
# Install dependencies
pip install -r requirements_gui.txt
```

### 🎯 Launch the Dashboard

```bash
streamlit run sre_load_test_gui.py
```

The dashboard will open in your browser at `http://localhost:8501`

---

## 🌟 Key Features

### ✅ Modern Streamlit GUI
- Clean, professional interface with sidebar configuration
- Real-time metrics dashboard with interactive charts
- One-click test execution and result export

### 🌐 Proxy Management System
- **Upload proxies.txt** file with proxy rotation
- Supports formats:
  - `ip:port` (simple)
  - `user:pass@ip:port` (authenticated)
  - `http://ip:port` or `https://user:pass@ip:port` (full URL)
- **Rotation Strategies**:
  - Round-robin: Sequential proxy usage
  - Random: Random proxy selection per request

### 📊 Real-time Visualization
- **Latency Timeline**: Scatter plot showing response times over test duration
- **RPS Graph**: Line chart showing requests per second in 1-second windows
- **Success/Error Markers**: Green dots for success, red for errors

### 🔧 Configuration Options
- **Target URL/IP**: Full URL or IP address
- **HTTP Methods**: GET, POST, PUT, DELETE, PATCH
- **Load Parameters**: Total requests, concurrency, timeout
- **Traffic Patterns**: Burst, Warmup, Stepped
- **JSON Payload**: For POST/PUT/PATCH requests
- **Custom Headers**: User-Agent, Accept, and more

### 💾 Export Capabilities
- **JSON**: Structured format for monitoring tools (Grafana, etc.)
- **CSV**: Spreadsheet-ready for Excel analysis
- **Summary Text**: Quick clipboard copy for reports

---

## 📋 Usage Examples

### Basic Load Test
1. Enter target URL: `http://localhost:8080`
2. Set requests: 1000, concurrency: 100
3. Click "🚀 Start Load Test"

### Distributed Traffic Test with Proxies
1. Create `proxies.txt` with your proxy list:
   ```
   192.168.1.100:8080
   10.0.0.50:3128
   user:pass@203.0.113.10:8888
   ```
2. Upload the file in the Proxy Management section
3. Select rotation strategy (round_robin or random)
4. Configure load parameters and start test

### API Endpoint Testing (POST)
1. Select HTTP Method: POST
2. Enter JSON payload: `{"username": "test", "action": "login"}`
3. Set concurrency and request count
4. Run test to evaluate API performance

---

## 🎯 Identifying Breaking Points

### Key Metrics to Monitor

1. **P95/P99 Latency Spikes**
   - Sudden increases indicate infrastructure stress
   - Target: Keep P95 < 500ms for good UX

2. **Error Rate Thresholds**
   - >5% errors: Warning zone
   - >10% errors: Critical - approaching breaking point
   - >25% errors: System failure imminent

3. **Throughput Plateau**
   - RPS stops increasing despite higher concurrency
   - Indicates connection pool or thread exhaustion

4. **Standard Deviation Growth**
   - High variance = inconsistent performance
   - Suggests resource contention or throttling

### Testing Strategy

**Phase 1: Baseline**
- 100 requests, 10 concurrent
- Establish normal performance metrics

**Phase 2: Load Increase**
- 1000 requests, 100 concurrent
- Identify initial bottlenecks

**Phase 3: Stress Test**
- 5000 requests, 500+ concurrent
- Find breaking point

**Phase 4: Distributed Load**
- Add 10+ proxies
- Test from multiple network perspectives
- Identify geographic/routing issues

---

## 📊 Interpreting Results

### Latency Chart
- **Green dots**: Successful requests
- **Red dots**: Failed requests (timeouts, errors)
- **Upward trend**: Performance degradation under load
- **Clusters of red**: System failure zones

### RPS Chart
- **Peak RPS**: Maximum throughput capacity
- **Drops**: Server rejecting connections or errors
- **Plateau**: Concurrency limit reached

### Metrics Dashboard
- **Success Rate**: Should be >95% for healthy systems
- **P95/P99**: Critical for SLA compliance
- **Std Dev**: Low = consistent, High = unpredictable

---

## 🔒 Best Practices

1. **Start Small**: Begin with low concurrency, gradually increase
2. **Monitor Resources**: Watch CPU, memory, network on target server
3. **Use Proxies**: Test from diverse network routes for realistic scenarios
4. **Export Results**: Save data for trend analysis and capacity planning
5. **Run Repeatedly**: Perform tests at different times to identify patterns
6. **Document Everything**: Note infrastructure changes between tests

---

## 🛠️ Troubleshooting

### Common Issues

**"Connection Refused" Errors**
- Verify target server is running
- Check firewall rules
- Confirm correct port number

**"Timeout" Errors**
- Increase timeout setting
- Server may be overloaded
- Check network connectivity

**Proxy Connection Failures**
- Validate proxy format in proxies.txt
- Test proxies individually first
- Ensure proxies are accessible from your network

**Streamlit Not Opening**
- Check if port 8501 is available
- Run: `streamlit run sre_load_test_gui.py --server.port 8502`

---

## 📚 Advanced Features

### Custom Headers
Add custom headers in Advanced Settings:
- Authentication tokens
- API keys
- Custom routing headers

### Traffic Patterns
- **Burst**: Sudden spike testing (DDoS simulation)
- **Warmup**: Gradual ramp-up (realistic user growth)
- **Stepped**: Incremental load increases (capacity planning)

### Export Formats
- **JSON**: Import to Grafana, Kibana, custom dashboards
- **CSV**: Excel pivot tables, trend analysis
- **Summary**: Quick reports for stakeholders

---

## 🎓 SRE Testing Methodology

### The Four Golden Signals

1. **Latency**: Time to serve requests (P50, P95, P99)
2. **Traffic**: Demand placed on system (RPS, concurrent users)
3. **Errors**: Rate of failed requests (4xx, 5xx, timeouts)
4. **Saturation**: How "full" your service is (CPU, memory, connections)

This dashboard helps you measure all four signals and identify breaking points before they impact production users.

---

## 📞 Support & Contributing

For issues or feature requests, please:
1. Check this guide first
2. Review error messages in the dashboard
3. Test with minimal configuration first
4. Document your findings and patterns

---

**Version**: 3.0  
**Last Updated**: 2026  
**Built With**: Streamlit, aiohttp, Plotly, Pandas
