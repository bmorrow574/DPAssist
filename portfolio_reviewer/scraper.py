"""
Portfolio content scraper
Extracts text and images from Google Sites and GitHub Pages
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urlparse
import time


class PortfolioScraper:
    """Scrape content from student portfolio websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def scrape(self, url: str) -> Optional[Dict]:
        """
        Scrape a portfolio URL and extract content
        
        Args:
            url: Portfolio URL (Google Sites or GitHub Pages)
            
        Returns:
            Dict with 'text', 'images', 'links', 'structure'
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Detect platform
            platform = self._detect_platform(url, soup)
            
            # Extract content based on platform
            if platform == 'google_sites':
                return self._scrape_google_sites(soup, url)
            elif platform == 'github_pages':
                return self._scrape_github_pages(soup, url)
            else:
                return self._scrape_generic(soup, url)
                
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def _detect_platform(self, url: str, soup: BeautifulSoup) -> str:
        """Detect which platform the portfolio is hosted on"""
        domain = urlparse(url).netloc.lower()
        
        if 'sites.google.com' in domain:
            return 'google_sites'
        elif 'github.io' in domain:
            return 'github_pages'
        else:
            return 'generic'
    
    def _scrape_google_sites(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract content from Google Sites"""
        content = {
            'url': url,
            'platform': 'google_sites',
            'text': '',
            'images': [],
            'links': [],
            'structure': []
        }
        
        # Remove script and style tags
        for script in soup(['script', 'style', 'nav', 'footer']):
            script.decompose()
        
        # Extract text content
        # Google Sites uses specific divs for content
        main_content = soup.find('div', class_='sites-canvas-main') or soup.find('main') or soup.body
        
        if main_content:
            # Get headings for structure
            for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                content['structure'].append({
                    'level': heading.name,
                    'text': heading.get_text(strip=True)
                })
            
            # Get all text
            text_parts = []
            for element in main_content.find_all(['p', 'div', 'span', 'li', 'td', 'th']):
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Filter out very short snippets
                    text_parts.append(text)
            
            content['text'] = '\n\n'.join(text_parts)
        
        # Extract images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                content['images'].append({
                    'src': src,
                    'alt': alt
                })
        
        # Extract links
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            if href and not href.startswith('#'):
                content['links'].append({
                    'url': href,
                    'text': text
                })
        
        return content
    
    def _scrape_github_pages(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract content from GitHub Pages"""
        content = {
            'url': url,
            'platform': 'github_pages',
            'text': '',
            'images': [],
            'links': [],
            'structure': []
        }
        
        # Remove script and style tags
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # GitHub Pages often uses article, main, or div with id="content"
        main_content = (
            soup.find('article') or 
            soup.find('main') or 
            soup.find('div', id='content') or 
            soup.find('div', class_='content') or
            soup.body
        )
        
        if main_content:
            # Get headings
            for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                content['structure'].append({
                    'level': heading.name,
                    'text': heading.get_text(strip=True)
                })
            
            # Get all text
            text_parts = []
            for element in main_content.find_all(['p', 'div', 'li', 'td', 'th', 'blockquote']):
                text = element.get_text(strip=True)
                if text and len(text) > 10:
                    text_parts.append(text)
            
            content['text'] = '\n\n'.join(text_parts)
        
        # Extract images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                content['images'].append({
                    'src': src,
                    'alt': alt
                })
        
        # Extract links
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            if href and not href.startswith('#'):
                content['links'].append({
                    'url': href,
                    'text': text
                })
        
        return content
    
    def _scrape_generic(self, soup: BeautifulSoup, url: str) -> Dict:
        """Generic scraper for other platforms"""
        content = {
            'url': url,
            'platform': 'generic',
            'text': '',
            'images': [],
            'links': [],
            'structure': []
        }
        
        # Remove unwanted tags
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        main_content = soup.find('main') or soup.body
        
        if main_content:
            # Get headings
            for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                content['structure'].append({
                    'level': heading.name,
                    'text': heading.get_text(strip=True)
                })
            
            # Get text
            text_parts = []
            for element in main_content.find_all(['p', 'div', 'li', 'td', 'th']):
                text = element.get_text(strip=True)
                if text and len(text) > 10:
                    text_parts.append(text)
            
            content['text'] = '\n\n'.join(text_parts)
        
        # Extract images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                content['images'].append({
                    'src': src,
                    'alt': alt
                })
        
        # Extract links
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            if href and not href.startswith('#'):
                content['links'].append({
                    'url': href,
                    'text': text
                })
        
        return content
