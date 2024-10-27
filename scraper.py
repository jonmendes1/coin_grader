

import os
import time
import random
import re
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib.parse import urljoin
import logging

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='coin_scraper.log'
        )
        self.logger = logging.getLogger('CoinScraper')
        
        # Initialize Selenium WebDriver with options
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        
        # Create data directory
        self.data_dir = "coin_data"
        os.makedirs(self.data_dir, exist_ok=True)

    def scrape_pcgs_coinfacts(self, category_urls=None):
        """
        Scrape coin data from PCGS CoinFacts
        """
        if category_urls is None:
            # Default to Morgan Dollars as an example
            category_urls = ['https://www.pcgs.com/coinfacts/category/morgan-dollars-1878-1921/744']

        coin_data = []
        
        for category_url in category_urls:
            try:
                self.driver.get(category_url)
                time.sleep(random.uniform(2, 4))  # Random delay
                
                # Wait for the coin grid to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "coin-grid"))
                )
                
                # Get all coin links
                coin_links = self.driver.find_elements(By.CSS_SELECTOR, ".coin-grid a")
                coin_urls = [link.get_attribute('href') for link in coin_links]
                
                for coin_url in coin_urls:
                    coin_info = self._scrape_pcgs_coin_detail(coin_url)
                    if coin_info:
                        coin_data.append(coin_info)
                        
            except Exception as e:
                self.logger.error(f"Error scraping category {category_url}: {str(e)}")
                
        return pd.DataFrame(coin_data)

    def _scrape_pcgs_coin_detail(self, url):
        """
        Scrape individual coin detail page from PCGS
        """
        try:
            self.driver.get(url)
            time.sleep(random.uniform(1.5, 3))  # Random delay
            
            # Wait for price guide to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "price-guide"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract basic coin info
            coin_info = {
                'url': url,
                'title': soup.select_one('h1').text.strip(),
                'year': self._extract_year(soup.select_one('h1').text.strip()),
                'denomination': soup.select_one('.denomination').text.strip() if soup.select_one('.denomination') else None,
            }
            
            # Extract grades and prices
            grades_data = []
            price_rows = soup.select('.price-guide tbody tr')
            for row in price_rows:
                cols = row.select('td')
                if len(cols) >= 2:
                    grade = cols[0].text.strip()
                    price = self._extract_price(cols[1].text.strip())
                    if grade and price:
                        grades_data.append({
                            'grade': grade,
                            'price': price
                        })
            
            # Extract images
            images = []
            img_elements = soup.select('.coin-images img')
            for img in img_elements:
                img_url = img.get('src')
                if img_url:
                    images.append(urljoin(url, img_url))
            
            coin_info['grades_data'] = grades_data
            coin_info['images'] = images
            
            return coin_info
            
        except Exception as e:
            self.logger.error(f"Error scraping coin detail {url}: {str(e)}")
            return None

    def scrape_heritage_auctions(self, search_term="Morgan Dollar", num_pages=10):
        """
        Scrape coin data from Heritage Auctions
        """
        base_url = "https://coins.ha.com/c/search.zx"
        coin_data = []
        
        for page in range(1, num_pages + 1):
            try:
                params = {
                    'saleNo': '',
                    'type': 'google-base',
                    'search': search_term,
                    'ic': '100',
                    'N': '0',
                    'Nty': '1',
                    'Ntt': search_term,
                    'Ntk': 'SI',
                    'Nu': 'QQQ',
                    'page': str(page)
                }
                
                response = requests.get(base_url, params=params, headers=self.headers)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract auction items
                items = soup.select('.item-card')
                
                for item in items:
                    item_data = self._parse_heritage_item(item)
                    if item_data:
                        coin_data.append(item_data)
                
                time.sleep(random.uniform(2, 4))  # Random delay
                
            except Exception as e:
                self.logger.error(f"Error scraping Heritage page {page}: {str(e)}")
                
        return pd.DataFrame(coin_data)

    def _parse_heritage_item(self, item_soup):
        """
        Parse individual Heritage auction item
        """
        try:
            # Extract basic info
            title = item_soup.select_one('.title').text.strip()
            image_url = item_soup.select_one('img')['src'] if item_soup.select_one('img') else None
            
            # Extract grade from title
            grade_match = re.search(r'(MS|PR|AU|XF|VF|F|VG|G|AG|P|FR)-?(\d+)', title)
            if grade_match:
                grade_prefix = grade_match.group(1)
                grade_number = int(grade_match.group(2))
                grade = f"{grade_prefix}-{grade_number}"
            else:
                grade = None
            
            # Extract price
            price_elem = item_soup.select_one('.price')
            price = self._extract_price(price_elem.text) if price_elem else None
            
            return {
                'title': title,
                'grade': grade,
                'price': price,
                'image_url': image_url,
                'source': 'Heritage'
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing Heritage item: {str(e)}")
            return None

    def download_images(self, df, output_dir):
        """
        Download images from URLs in DataFrame
        """
        os.makedirs(output_dir, exist_ok=True)
        
        for idx, row in df.iterrows():
            try:
                # Handle both single image URLs and lists of URLs
                image_urls = row['image_url'] if isinstance(row['image_url'], str) else row['images'][0]
                image_urls = [image_urls] if isinstance(image_urls, str) else image_urls
                
                for img_idx, img_url in enumerate(image_urls):
                    time.sleep(random.uniform(0.5, 1.5))  # Random delay
                    
                    response = requests.get(img_url, headers=self.headers)
                    if response.status_code == 200:
                        # Create filename using coin details
                        grade = str(row.get('grade', 'unknown_grade'))
                        year = str(row.get('year', 'unknown_year'))
                        filename = f"coin_{year}_{grade}_{idx}_{img_idx}.jpg"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        self.logger.info(f"Successfully downloaded: {filename}")
                    else:
                        self.logger.warning(f"Failed to download image {img_url}: Status {response.status_code}")
                        
            except Exception as e:
                self.logger.error(f"Error downloading images for row {idx}: {str(e)}")

    def _extract_year(self, title):
        """Extract year from coin title"""
        year_match = re.search(r'\b(17|18|19|20)\d{2}\b', title)
        return int(year_match.group()) if year_match else None

    def _extract_price(self, price_text):
        """Extract numerical price from price text"""
        price_match = re.search(r'[\$]?([\d,]+(?:\.\d{2})?)', price_text)
        if price_match:
            return float(price_match.group(1).replace(',', ''))
        return None

    def save_data(self, df, filename):
        """Save scraped data to CSV"""
        filepath = os.path.join(self.data_dir, filename)
        df.to_csv(filepath, index=False)
        self.logger.info(f"Data saved to {filepath}")

    def close(self):
        """Close the Selenium WebDriver"""
        self.driver.quit()

def main():
    # Initialize scraper
    scraper = WebScraper()
    
    try:
        # Scrape data from both sources
        pcgs_data = scraper.scrape_pcgs_coinfacts()
        heritage_data = scraper.scrape_heritage_auctions()
        
        # Combine and save data
        all_data = pd.concat([pcgs_data, heritage_data], ignore_index=True)
        scraper.save_data(all_data, 'coin_data.csv')
        
        # Download images
        scraper.download_images(all_data, "coin_images")
        
    finally:
        # Clean up
        scraper.close()

if __name__ == "__main__":
    main()

