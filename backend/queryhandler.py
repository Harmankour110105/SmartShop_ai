from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import logging
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from datetime import datetime
from fake_useragent import UserAgent
import ssl
import certifi

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["query"])

# Initialize UserAgent
ua = UserAgent()

# Create SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

class FlipkartScraper:
    """Simplified Flipkart scraper based on SmartShop's implementation"""
    
    def get_search_url(self, query: str) -> str:
        """Generate Flipkart search URL"""
        clean_query = query.replace(' ', '%20')
        return f"https://www.flipkart.com/search?q={clean_query}"

    def extract_price(self, price_text: str) -> float:
        """Extract price value from text"""
        try:
            # Remove currency symbol and commas, then convert to float
            price = price_text.replace('₹', '').replace(',', '').strip()
            return float(price)
        except (ValueError, AttributeError):
            return 0.0

    def parse_search_results(self, html: str) -> List[Dict]:
        """Parse Flipkart search results"""
        products = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try different container selectors
        selectors = [
            'div._1AtVbE._4ddWXP',  # Updated selector
            'div._1AtVbE',
            'div._13oc-S',
            'div._2kHMtA',
            'div._4ddWXP',
            'div._2B099V',
            'div[data-id]'  # Fallback
        ]
        
        product_containers = []
        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                product_containers = containers
                logger.info(f"Found {len(containers)} products using selector: {selector}")
                # Log the first container's HTML for debugging
                if containers:
                    logger.debug(f"First container HTML: {containers[0]}")
                break

        for idx, container in enumerate(product_containers[:10]):  # Limit to 10 results
            try:
                logger.debug(f"Processing product container {idx + 1}")
                
                # Try to find any link first - most product info is in links
                links = container.find_all('a')
                if not links:
                    logger.debug(f"No links found in container {idx + 1}")
                    continue

                # Try to find product name from link title or text
                name = None
                for link in links:
                    if link.get('title'):
                        name = link.get('title')
                        break
                    elif link.get_text(strip=True):
                        name = link.get_text(strip=True)
                        break

                if not name:
                    logger.debug(f"No name found in container {idx + 1}")
                    continue

                logger.debug(f"Found product name: {name}")

                # Try to find price - look for ₹ symbol
                price_text = None
                price_candidates = container.find_all(text=lambda t: '₹' in str(t))
                if price_candidates:
                    price_text = price_candidates[0]
                    logger.debug(f"Found price text: {price_text}")

                if not price_text:
                    logger.debug(f"No price found in container {idx + 1}")
                    continue

                price = self.extract_price(price_text)
                if price == 0:
                    logger.debug(f"Invalid price (0) for container {idx + 1}")
                    continue

                # Get product URL from the first link
                url = 'https://www.flipkart.com' + links[0].get('href', '')

                # Try to find image - look for any img tag
                image_url = None
                img_tag = container.find('img')
                if img_tag:
                    image_url = img_tag.get('src')

                products.append({
                    "product": name,
                    "price": price,
                    "platform": "Flipkart",
                    "delivery": 30,
                    "url": url,
                    "image_url": image_url
                })
                logger.info(f"Successfully parsed product: {name} from Flipkart")

            except Exception as e:
                logger.error(f"Error parsing Flipkart product container {idx + 1}: {str(e)}")
                logger.debug(f"Problematic container HTML: {container}")
                continue

        return products

class AmazonScraper:
    """Simplified Amazon scraper"""
    
    def get_search_url(self, query: str) -> str:
        """Generate Amazon search URL"""
        clean_query = query.replace(' ', '+')
        return f"https://www.amazon.in/s?k={clean_query}"

    def extract_price(self, price_text: str) -> float:
        """Extract price value from text"""
        try:
            # Handle different price formats
            price = price_text.replace('₹', '').replace(',', '').strip()
            if '.' in price:  # Handle decimal prices
                price = price.split('.')[0]
            return float(price)
        except (ValueError, AttributeError):
            return 0.0

    def parse_search_results(self, html: str) -> List[Dict]:
        """Parse Amazon search results"""
        products = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try different container selectors
        selectors = [
            'div.s-result-item[data-component-type="s-search-result"]',
            'div.sg-col-4-of-12.s-result-item',
            'div.sg-col-4-of-16.s-result-item',
            'div.s-asin'
        ]
        
        product_containers = []
        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                product_containers = containers
                logger.info(f"Found {len(containers)} products using selector: {selector}")
                if containers:
                    logger.debug(f"First container HTML: {containers[0]}")
                break

        for idx, container in enumerate(product_containers[:10]):
            try:
                logger.debug(f"Processing Amazon product container {idx + 1}")

                # Skip sponsored products
                if container.get('data-component-type') == "sp-sponsored-result":
                    logger.debug("Skipping sponsored product")
                    continue

                # Try to find product name from h2 tags first
                name = None
                h2_tag = container.find('h2')
                if h2_tag:
                    name = h2_tag.get_text(strip=True)
                
                if not name:
                    # Try finding any span with product text
                    spans = container.find_all('span', class_=lambda x: x and ('a-text-normal' in x or 'a-color-base' in x))
                    for span in spans:
                        if span.get_text(strip=True):
                            name = span.get_text(strip=True)
                            break

                if not name:
                    logger.debug(f"No name found in container {idx + 1}")
                    continue

                logger.debug(f"Found product name: {name}")

                # Try to find price - look for ₹ symbol first
                price_text = None
                price_candidates = container.find_all(text=lambda t: '₹' in str(t))
                if price_candidates:
                    price_text = price_candidates[0]
                    logger.debug(f"Found price text: {price_text}")

                if not price_text:
                    # Try finding price in span tags
                    price_spans = container.find_all('span', class_=lambda x: x and ('a-price' in x or 'a-color-price' in x))
                    for span in price_spans:
                        if '₹' in span.get_text():
                            price_text = span.get_text()
                            break

                if not price_text:
                    logger.debug(f"No price found in container {idx + 1}")
                    continue

                price = self.extract_price(price_text)
                if price == 0:
                    logger.debug(f"Invalid price (0) for container {idx + 1}")
                    continue

                # Get product URL
                url_tag = container.find('a', class_=lambda x: x and ('a-link-normal' in x))
                if not url_tag:
                    url_tag = container.find('a')
                
                if not url_tag:
                    logger.debug(f"No URL found in container {idx + 1}")
                    continue

                url = 'https://www.amazon.in' + url_tag.get('href', '')

                # Try to find image
                image_url = None
                img_tag = container.find('img')
                if img_tag:
                    image_url = img_tag.get('src')

                products.append({
                    "product": name,
                    "price": price,
                    "platform": "Amazon",
                    "delivery": 35,
                    "url": url,
                    "image_url": image_url
                })
                logger.info(f"Successfully parsed product: {name} from Amazon")

            except Exception as e:
                logger.error(f"Error parsing Amazon product container {idx + 1}: {str(e)}")
                logger.debug(f"Problematic container HTML: {container}")
                continue

        return products

class MeeshoScraper:
    """Simplified Meesho scraper"""
    
    def get_search_url(self, query: str) -> str:
        """Generate Meesho search URL"""
        clean_query = query.replace(' ', '-')
        return f"https://www.meesho.com/search?q={clean_query}"

    def extract_price(self, price_text: str) -> float:
        """Extract price value from text"""
        try:
            # Handle different price formats
            price = price_text.replace('₹', '').replace(',', '').strip()
            if 'from' in price.lower():
                price = price.lower().split('from')[-1].strip()
            if '.' in price:  # Handle decimal prices
                price = price.split('.')[0]
            return float(price)
        except (ValueError, AttributeError):
            return 0.0

    def parse_search_results(self, html: str) -> List[Dict]:
        """Parse Meesho search results"""
        products = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try different container selectors
        selectors = [
            'div[data-testid="product-container"]',  # Most common
            'div.ProductList__GridCol-sc-8lnc8o-0',
            'div.NewProductCard__Base',
            'div.ShopCard__StyledCard'  # New selector
        ]
        
        product_containers = []
        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                product_containers = containers
                logger.info(f"Found {len(containers)} products using selector: {selector}")
                break

        for container in product_containers[:10]:  # Limit to 10 results
            try:
                # Extract product name - try multiple selectors
                name_selectors = [
                    'p[data-testid="product-name"]',  # Most common
                    'p.Text__StyledText-sc-oo0kvp-0',
                    'p.NewProductCard__ProductTitle_Desktop',
                    'div.NewProductCard__ProductName',
                    'p.ShopCard__ProductName'  # New selector
                ]
                name_element = None
                for selector in name_selectors:
                    name_element = container.select_one(selector)
                    if name_element:
                        logger.debug(f"Found name using selector: {selector}")
                        break
                
                if not name_element:
                    logger.debug("No name element found, skipping product")
                    continue
                name = name_element.get_text(strip=True)

                # Extract price - try multiple selectors
                price_selectors = [
                    'h5[data-testid="product-price"]',  # Most common
                    'h5.Text__StyledText-sc-oo0kvp-0',
                    'div.NewProductCard__PriceRow',
                    'h4.NewProductCard__DiscountedPriceText',
                    'p.ShopCard__PriceParagraph'  # New selector
                ]
                price_element = None
                for selector in price_selectors:
                    price_element = container.select_one(selector)
                    if price_element:
                        logger.debug(f"Found price using selector: {selector}")
                        break
                
                if not price_element:
                    logger.debug("No price element found, skipping product")
                    continue
                price = self.extract_price(price_element.get_text(strip=True))

                # Extract product URL - try multiple selectors
                url_selectors = [
                    'a[data-testid="product-link"]',  # Most common
                    'a.NewProductCard__Anchor',
                    'a.ShopCard__StyledAnchor'  # New selector
                ]
                url_element = None
                for selector in url_selectors:
                    url_element = container.select_one(selector)
                    if url_element:
                        logger.debug(f"Found URL using selector: {selector}")
                        break
                
                if not url_element:
                    logger.debug("No URL element found, skipping product")
                    continue
                url = 'https://www.meesho.com' + url_element.get('href', '')

                # Extract image URL - try multiple selectors
                img_selectors = [
                    'img[data-testid="product-image"]',  # Most common
                    'img.NewProductCard__Image',
                    'img.ShopCard__Image'  # New selector
                ]
                img_element = None
                for selector in img_selectors:
                    img_element = container.select_one(selector)
                    if img_element:
                        logger.debug(f"Found image using selector: {selector}")
                        break
                
                image_url = img_element.get('src') if img_element else None

                products.append({
                    "product": name,
                    "price": price,
                    "platform": "Meesho",
                    "delivery": 40,  # Default delivery estimate
                    "url": url,
                    "image_url": image_url
                })
                logger.info(f"Successfully parsed product: {name} from Meesho")

            except Exception as e:
                logger.error(f"Error parsing Meesho product container: {str(e)}")
                continue

        return products

async def search_platform(scraper, query: str, headers: Dict) -> List[Dict]:
    """Search a specific platform"""
    try:
        url = scraper.get_search_url(query)
        conn = aiohttp.TCPConnector(ssl=ssl_context, limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        # Add platform-specific headers
        platform_headers = headers.copy()
        if "meesho.com" in url:
            # Add more browser-like headers for Meesho
            platform_headers.update({
                "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.meesho.com/",
                "DNT": "1",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "navigate",
                "sec-fetch-dest": "document",
                "Cookie": "AMP_TOKEN=%24NOT_FOUND; _gcl_au=1.1.123456789.1234567890"
            })
            # Add a small delay for Meesho to avoid rate limiting
            await asyncio.sleep(1)
        elif "amazon.in" in url:
            platform_headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.amazon.in/",
                "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "Cookie": "session-id=123456789; i18n-prefs=INR; csm-hit=tb:s-XXXXX|1234567890"
            })
        elif "flipkart.com" in url:
            platform_headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.flipkart.com/",
                "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"'
            })

        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
            try:
                async with session.get(url, headers=platform_headers, allow_redirects=True) as response:
                    if response.status == 200:
                        html = await response.text()
                        logger.info(f"Successfully fetched data from {url}")
                        # Log the first 500 characters of HTML for debugging
                        logger.debug(f"First 500 chars of response: {html[:500]}")
                        results = scraper.parse_search_results(html)
                        logger.info(f"Successfully parsed {len(results)} products from {url}")
                        return results
                    elif response.status == 403:
                        logger.error(f"Access forbidden (403) from {url}. The site may be blocking requests.")
                        return []
                    elif response.status == 429:
                        logger.error(f"Too many requests (429) from {url}. Need to implement rate limiting.")
                        return []
                    else:
                        logger.error(f"Failed to fetch data from {url}. Status: {response.status}")
                        return []
            except asyncio.TimeoutError:
                logger.error(f"Timeout while fetching data from {url}")
                return []
            except aiohttp.ClientError as e:
                logger.error(f"Network error while fetching data from {url}: {str(e)}")
                return []
    except Exception as e:
        logger.error(f"Error searching platform: {str(e)}")
        return []

@router.post("/query")
async def handle_query(query: dict):
    """Handle search query and return results from multiple platforms"""
    try:
        # Initialize scrapers
        scrapers = {
            "flipkart": FlipkartScraper(),
            "amazon": AmazonScraper(),
            "meesho": MeeshoScraper()
        }
        
        # Use rotating user agents and enhanced headers
        headers = {
            "User-Agent": ua.random,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
        }

        # Search across platforms concurrently
        tasks = []
        for platform, scraper in scrapers.items():
            task = search_platform(scraper, query["query"], headers)
            tasks.append(task)
        
        # Wait for all searches to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        all_results = []
        for platform_results in results:
            if isinstance(platform_results, list):  # Skip any failed searches
                all_results.extend(platform_results)
            elif isinstance(platform_results, Exception):
                logger.error(f"Platform search failed with error: {str(platform_results)}")

        # Sort results by price
        all_results.sort(key=lambda x: x["price"])
        
        # Log the number of results found
        logger.info(f"Found {len(all_results)} total results across all platforms")
        
        return {"results": all_results}

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))