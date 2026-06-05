"""
Portfolio content scraper
Extracts text and images from Google Sites, GitHub Pages, and GitHub repositories
"""
import base64
import re
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

            # Detect private/restricted Google Sites pages before evaluation.
            # If Google redirects to a sign-in page, the portfolio is not publicly accessible.
            final_url = response.url.lower()
            page_text = response.text.lower()

            if (
                "accounts.google.com" in final_url
                or "signin" in final_url
                or "use your google account" in page_text
                or "sign in" in page_text and "google account" in page_text
            ):
                return {
                    "url": url,
                    "platform": "restricted",
                    "text": "",
                    "images": [],
                    "links": [],
                    "structure": [],
                    "access_error": True,
                    "access_error_type": "google_sign_in_required",
                    "access_error_message": (
                        "This portfolio could not be reviewed because the submitted Google Sites "
                        "link requires a Google sign-in. The student needs to publish the site or "
                        "page so anyone with the link can view it, then resubmit."
                    )
                }

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Detect platform
            platform = self._detect_platform(url, soup)

            # Extract content based on platform
            if platform == 'google_sites':
                return self._scrape_google_sites(soup, url)
            elif platform == 'github_pages':
                return self._scrape_github_pages(soup, url)
            elif platform == 'github_repo':
                return self._scrape_github_repo(soup, url)
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
        elif 'github.com' in domain:
            return 'github_repo'
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

    def _scrape_github_repo(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Extract content from a GitHub repository page (github.com/user/repo).
        Tries the GitHub REST API first to get the rendered README, then falls
        back to scraping the HTML page directly.
        """
        content = {
            'url': url,
            'platform': 'github_repo',
            'text': '',
            'images': [],
            'links': [],
            'structure': []
        }

        # Parse user/repo from URL path
        path_parts = [p for p in urlparse(url).path.strip('/').split('/') if p]

        if len(path_parts) >= 2:
            user, repo = path_parts[0], path_parts[1]

            # Try GitHub API for README (works for all public repos, no auth needed)
            readme_text = self._fetch_github_readme(user, repo)
            if readme_text:
                content['text'] = readme_text
                content['structure'].append({'level': 'h1', 'text': f"{user}/{repo}"})
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    if src and 'avatar' not in src.lower() and 'identicon' not in src.lower():
                        content['images'].append({'src': src, 'alt': alt})
                return content

        # Fallback: scrape the rendered HTML of the GitHub repo page
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        # GitHub renders the README inside a specific container
        readme_container = (
            soup.find('div', {'data-target': 'readme-toc.content'}) or
            soup.find('article', class_='markdown-body') or
            soup.find(id='readme') or
            soup.find('div', class_='Box-body')
        )

        if readme_container:
            for heading in readme_container.find_all(['h1', 'h2', 'h3', 'h4']):
                content['structure'].append({
                    'level': heading.name,
                    'text': heading.get_text(strip=True)
                })
            text_parts = []
            for element in readme_container.find_all(['p', 'li', 'td', 'blockquote']):
                text = element.get_text(strip=True)
                if text and len(text) > 10:
                    text_parts.append(text)
            content['text'] = '\n\n'.join(text_parts)

        # Also grab the repository description shown near the top of the page
        desc_el = (
            soup.find('p', {'data-target': 'about-sidebar.description'}) or
            soup.find('p', class_='f4')
        )
        if desc_el:
            desc_text = desc_el.get_text(strip=True)
            if desc_text:
                content['text'] = desc_text + '\n\n' + content['text']

        # Images (skip GitHub UI chrome like avatars)
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src and 'avatar' not in src.lower() and 'identicon' not in src.lower():
                content['images'].append({'src': src, 'alt': alt})

        # Links
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            if href and not href.startswith('#'):
                content['links'].append({'url': href, 'text': text})

        return content

    def _fetch_github_readme(self, user: str, repo: str) -> Optional[str]:
        """
        Fetch the README for a public GitHub repo via the GitHub REST API.
        Returns plain text (markdown stripped) or None if unavailable.
        No authentication required for public repos (60 req/hour rate limit).
        """
        try:
            api_url = f"https://api.github.com/repos/{user}/{repo}/readme"
            response = self.session.get(
                api_url,
                timeout=15,
                headers={'Accept': 'application/vnd.github.v3+json'}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('encoding') == 'base64' and data.get('content'):
                    raw_bytes = base64.b64decode(data['content'])
                    raw_text = raw_bytes.decode('utf-8', errors='replace')
                    return self._strip_markdown(raw_text)
        except Exception as e:
            print(f"GitHub API error for {user}/{repo}: {e}")
        return None

    def _strip_markdown(self, text: str) -> str:
        """Convert markdown to plain text for AI evaluation."""
        # Remove fenced code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        # Remove inline code
        text = re.sub(r'`[^`]+`', '', text)
        # Remove ATX headings (keep the heading text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove bold / italic markers
        text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
        text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
        # Convert links to just their display text
        text = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', text)  # images
        text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)   # links
        # Remove HTML tags that sometimes appear in markdown
        text = re.sub(r'<[^>]+>', '', text)
        # Collapse excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
