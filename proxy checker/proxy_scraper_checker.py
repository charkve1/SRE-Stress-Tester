"""
High-Performance Asynchronous Proxy Scraper and Checker
Scrapes proxies from multiple sources, validates them, and saves fast working proxies.
"""

import asyncio
import aiohttp
import re
from typing import List, Set, Tuple
from tqdm import tqdm
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProxyScraper:
    """Asynchronous proxy scraper that collects from multiple sources."""
    
    def __init__(self):
        self.proxies: Set[str] = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def scrape_all(self) -> Set[str]:
        """Scrape proxies from all sources concurrently."""
        logger.info("Starting proxy scraping from multiple sources...")
        
        tasks = [
            self.scrape_proxyscrape(),
            self.scrape_free_proxy_list(),
            self.scrape_github_proxy_list(),
            self.scrape_openproxy_space(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scraping error: {result}")
            elif isinstance(result, set):
                self.proxies.update(result)
        
        logger.info(f"Total unique proxies scraped: {len(self.proxies)}")
        return self.proxies
    
    async def scrape_proxyscrape(self) -> Set[str]:
        """Scrape from ProxyScrape."""
        proxies = set()
        urls = [
            'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=all&timeout=5000&country=all&ssl=all&anonymity=all',
            'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all'
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            text = await response.text()
                            found = self._extract_proxies(text)
                            proxies.update(found)
                            logger.info(f"ProxyScrape: {len(found)} proxies found")
                except Exception as e:
                    logger.error(f"ProxyScrape error: {e}")
        
        return proxies
    
    async def scrape_free_proxy_list(self) -> Set[str]:
        """Scrape from Free-Proxy-List websites."""
        proxies = set()
        urls = [
            'https://free-proxy-list.net/',
            'https://www.us-proxy.org/',
            'https://www.sslproxies.org/'
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), headers=self.headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            # Extract IP:Port pattern from the HTML
                            found = self._extract_proxies_from_html(html)
                            proxies.update(found)
                            logger.info(f"Free-Proxy-List ({url}): {len(found)} proxies found")
                except Exception as e:
                    logger.error(f"Free-Proxy-List error ({url}): {e}")
        
        return proxies
    
    async def scrape_github_proxy_list(self) -> Set[str]:
        """Scrape from GitHub proxy lists."""
        proxies = set()
        urls = [
            'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt',
            'https://raw.githubusercontent.com/shiftytr/proxy-list/master/proxy.txt',
            'https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt',
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            text = await response.text()
                            found = self._extract_proxies(text)
                            proxies.update(found)
                            logger.info(f"GitHub ({url.split('/')[-1]}): {len(found)} proxies found")
                except Exception as e:
                    logger.error(f"GitHub error ({url}): {e}")
        
        return proxies
    
    async def scrape_openproxy_space(self) -> Set[str]:
        """Scrape from openproxy.space."""
        proxies = set()
        urls = [
            'https://openproxy.space/list/http.txt',
            'https://openproxy.space/list/socks4.txt',
            'https://openproxy.space/list/socks5.txt',
        ]
        
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            text = await response.text()
                            found = self._extract_proxies(text)
                            proxies.update(found)
                            logger.info(f"OpenProxy ({url.split('/')[-1]}): {len(found)} proxies found")
                except Exception as e:
                    logger.error(f"OpenProxy error ({url}): {e}")
        
        return proxies
    
    def _extract_proxies(self, text: str) -> Set[str]:
        """Extract IP:Port from text content."""
        pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
        found = set(re.findall(pattern, text))
        return found
    
    def _extract_proxies_from_html(self, html: str) -> Set[str]:
        """Extract IP:Port from HTML content."""
        # Look for patterns like IP:Port in table cells
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>\s*<td[^>]*>(\d{2,5})'
        matches = re.findall(pattern, html)
        proxies = {f"{ip}:{port}" for ip, port in matches}
        
        # Also try simple pattern as fallback
        if not proxies:
            proxies = self._extract_proxies(html)
        
        return proxies


class ProxyChecker:
    """Asynchronous proxy checker with speed validation."""
    
    def __init__(self, max_concurrent: int = 100, timeout: int = 5, max_response_time: float = 2.0):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_response_time = max_response_time  # 2 seconds = 2000ms
        self.working_proxies: List[Tuple[str, float]] = []  # (proxy, response_time)
        self.test_url = 'http://httpbin.org/ip'
    
    async def check_all(self, proxies: Set[str]) -> List[Tuple[str, float]]:
        """Check all proxies concurrently with semaphore."""
        logger.info(f"Starting proxy check for {len(proxies)} proxies...")
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for proxy in proxies:
                task = asyncio.create_task(
                    self._check_proxy(session, proxy, semaphore)
                )
                tasks.append(task)
            
            # Use tqdm for progress tracking
            for coro in tqdm(
                asyncio.as_completed(tasks),
                total=len(tasks),
                desc="Checking proxies",
                unit="proxy"
            ):
                await coro
        
        logger.info(f"Found {len(self.working_proxies)} working proxies")
        return self.working_proxies
    
    async def _check_proxy(self, session: aiohttp.ClientSession, proxy: str, semaphore: asyncio.Semaphore):
        """Check a single proxy."""
        async with semaphore:
            try:
                proxy_url = f'http://{proxy}'
                connector = aiohttp.TCPConnector(limit=1)
                
                async with aiohttp.ClientSession(connector=connector) as proxy_session:
                    start_time = asyncio.get_event_loop().time()
                    
                    async with proxy_session.get(
                        self.test_url,
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        end_time = asyncio.get_event_loop().time()
                        response_time = (end_time - start_time) * 1000  # Convert to ms
                        
                        if response.status == 200:
                            await response.text()  # Read response body
                            
                            # Only save if response time is under threshold
                            if response_time <= self.max_response_time * 1000:
                                self.working_proxies.append((proxy, response_time))
                                
            except Exception:
                # Silently ignore failed proxies
                pass


class ProxyManager:
    """Main manager that orchestrates scraping and checking."""
    
    def __init__(self, output_file: str = 'verified_proxies.txt'):
        self.scraper = ProxyScraper()
        self.checker = ProxyChecker(max_concurrent=100, timeout=5, max_response_time=2.0)
        self.output_file = output_file
    
    async def run(self):
        """Execute the full pipeline: scrape -> check -> save."""
        start_time = datetime.now()
        
        print("="*60)
        print("HIGH-PERFORMANCE PROXY SCRAPER & CHECKER")
        print("="*60)
        print()
        
        # Step 1: Scrape proxies
        print("[Phase 1] Scraping proxies from multiple sources...")
        proxies = await self.scraper.scrape_all()
        
        if not proxies:
            logger.error("No proxies scraped. Exiting.")
            return
        
        print(f"\n[Total Scraped] {len(proxies)} unique proxies")
        print()
        
        # Step 2: Check proxies
        print("[Phase 2] Checking proxy speed and functionality...")
        working_proxies = await self.checker.check_all(proxies)
        
        print(f"\n[Found Working] {len(working_proxies)} fast proxies (<2000ms)")
        print()
        
        # Step 3: Save results
        print("[Phase 3] Saving verified proxies...")
        await self._save_proxies(working_proxies)
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        print()
        print("="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total Scraped:    {len(proxies)}")
        print(f"Working & Fast:   {len(working_proxies)}")
        print(f"Success Rate:     {(len(working_proxies)/len(proxies)*100):.2f}%")
        print(f"Time Elapsed:     {elapsed:.2f}s")
        print(f"Output File:      {self.output_file}")
        print("="*60)
    
    async def _save_proxies(self, working_proxies: List[Tuple[str, float]]):
        """Save working proxies to file."""
        # Sort by response time (fastest first)
        working_proxies.sort(key=lambda x: x[1])
        
        with open(self.output_file, 'w') as f:
            for proxy, response_time in working_proxies:
                f.write(f"{proxy}\n")  # ip:port format
        
        # Also save detailed info to JSON for reference
        detailed_file = self.output_file.replace('.txt', '_detailed.json')
        detailed_data = [
            {
                'proxy': proxy,
                'response_time_ms': round(response_time, 2),
                'speed_category': 'Elite' if response_time < 500 else 'Fast' if response_time < 1000 else 'Medium'
            }
            for proxy, response_time in working_proxies
        ]
        
        with open(detailed_file, 'w') as f:
            json.dump(detailed_data, f, indent=2)
        
        logger.info(f"Saved {len(working_proxies)} proxies to {self.output_file}")
        logger.info(f"Detailed info saved to {detailed_file}")


async def main():
    """Main entry point."""
    manager = ProxyManager(output_file='verified_proxies.txt')
    await manager.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
