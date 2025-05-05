import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
from collections import deque

class GitLabScraper:
    def __init__(self, start_urls, output_file="gitlab_scraped.txt"):
        """
        Initialize the GitLab scraper.
        
        Args:
            start_urls (list): List of URLs to start scraping from
            output_file (str): Path to the output text file
        """
        self.start_urls = start_urls
        self.output_file = output_file
        self.visited_urls = set()
        self.to_visit = deque(start_urls)
        self.domain_whitelist = [
            "handbook.gitlab.com/handbook",
            "about.gitlab.com/direction"
        ]
        
        # Clear the output file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("# GitLab Content Scrape\n\n")
        
        # Add headers to mimic a browser and avoid being blocked
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
    
    def is_allowed_url(self, url):
        """Check if URL is within allowed domains."""
        parsed_url = urlparse(url)
        
        # Check if the URL belongs to any of the whitelisted domains
        for domain in self.domain_whitelist:
            if parsed_url.netloc == domain.split('/')[0] and (
                len(domain.split('/')) == 1 or  # If it's just a domain
                url.startswith(f"https://{domain}")  # If it's a path-specific rule
            ):
                return True
        
        return False
    
    def extract_text(self, soup, url):
        """Extract text content from headings and paragraphs."""
        content = []
        
        # Get the title of the page
        title = soup.title.string if soup.title else "Untitled Page"
        content.append(f"\n\n## {title.strip()}\n")
        content.append(f"URL: {url}\n")
        
        # Extract text from all headings (h1, h2, h3, etc.)
        for heading_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for heading in soup.find_all(heading_tag):
                text = heading.get_text().strip()
                if text:
                    prefix = '#' * (int(heading_tag[1]) + 2)  # Adjust heading level for markdown
                    content.append(f"{prefix} {text}\n")
        
        # Extract paragraphs
        for paragraph in soup.find_all('p'):
            text = paragraph.get_text().strip()
            if text:
                content.append(f"{text}\n\n")
        
        # Extract list items
        for ul in soup.find_all(['ul', 'ol']):
            for li in ul.find_all('li'):
                text = li.get_text().strip()
                if text:
                    content.append(f"- {text}\n")
        
        return "".join(content)
    
    def extract_links(self, soup, base_url):
        """Extract links from the soup object."""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Handle relative URLs
            full_url = urljoin(base_url, href)
            
            # Filter out fragment identifiers, query parameters, and non-HTTP schemes
            parsed = urlparse(full_url)
            if parsed.scheme in ('http', 'https') and self.is_allowed_url(full_url):
                # Normalize the URL and remove fragments
                normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                links.append(normalized_url)
        
        return links
    
    def scrape_url(self, url):
        """Scrape a single URL and return its content."""
        try:
            print(f"Scraping: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = self.extract_text(soup, url)
            links = self.extract_links(soup, url)
            
            # Add unvisited links to the queue
            for link in links:
                if link not in self.visited_urls:
                    self.to_visit.append(link)
            
            # Add the current URL to visited
            self.visited_urls.add(url)
            
            return text_content
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return f"\n\nError scraping {url}: {str(e)}\n\n"
    
    def run(self, max_pages=500):
        """
        Run the scraper.
        
        Args:
            max_pages (int): Maximum number of pages to scrape
        """
        page_count = 0
        
        while self.to_visit and page_count < max_pages:
            # Get the next URL to visit
            url = self.to_visit.popleft()
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            # Scrape the URL
            content = self.scrape_url(url)
            
            # Save the content to the output file
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(content)
            
            page_count += 1
            
            # Rate limiting to be respectful
            time.sleep(1)
            
            print(f"Progress: {page_count}/{max_pages} pages scraped. {len(self.to_visit)} pages in queue.")
        
        print(f"Scraping completed. {page_count} pages scraped.")


if __name__ == "__main__":
    # Starting URLs
    start_urls = [
        "https://handbook.gitlab.com/handbook",
        "https://about.gitlab.com/direction/"
    ]
    
    # Initialize and run the scraper
    scraper = GitLabScraper(start_urls)
    scraper.run(max_pages=500)  # Adjust max_pages as needed
    
    print(f"Content has been saved to {scraper.output_file}")