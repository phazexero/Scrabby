import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
import hashlib

class WebCrawler:
    def __init__(self, start_url, max_depth=3, output_dir='crawled_content'):
        self.start_url = start_url
        self.max_depth = max_depth
        self.visited = set()
        self.content_hashes = set()
        self.base_domain = urlparse(start_url).netloc
        self.output_dir = output_dir
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def is_valid_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc == self.base_domain

    def get_file_name(self, url):
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            path = 'index'
        return f"{path.replace('/', '_')}.html"

    def extract_structured_content(self, soup, base_url):
        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        # Extract title
        title = soup.title.string if soup.title else "No Title"

        # Extract body content, preserving important tags
        body = soup.body
        if body is None:
            body = soup

        # Define tags to keep
        tags_to_keep = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 'dl', 'dd', 'table', 'tr', 'th', 'td', 'a', 'span', 'pre']

        for tag in body.find_all(True):
            if tag.name not in tags_to_keep:
                tag.unwrap()

        # Update links
        for a in body.find_all('a', href=True):
            a['href'] = urljoin(base_url, a['href'])

        # Remove empty tags
        for tag in body.find_all():
            if len(tag.get_text(strip=True)) == 0 and tag.name != 'a':
                tag.extract()

        return title, body.prettify()

    def save_content(self, url, title, content):
        file_name = self.get_file_name(url)
        file_path = os.path.join(self.output_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><head><title>{title}</title></head><body>{content}</body></html>")
        
        print(f"Saved: {file_path}")

    def crawl(self, url, depth=0):
        if depth > self.max_depth or url in self.visited or not self.is_valid_url(url):
            return

        print(f"Crawling: {url} (Depth: {depth})")
        self.visited.add(url)

        try:
            response = requests.get(url)
            if response.status_code == 200:
                content = response.text
                
                # Check for duplicate content using hash
                content_hash = hashlib.md5(content.encode()).hexdigest()
                if content_hash in self.content_hashes:
                    print(f"Duplicate content found: {url}")
                    return
                
                self.content_hashes.add(content_hash)
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract and save the content
                title, extracted_content = self.extract_structured_content(soup, url)
                self.save_content(url, title, extracted_content)
                
                # Find all links on the page
                links = soup.find_all('a', href=True)
                for link in links:
                    next_url = urljoin(url, link['href'])
                    self.crawl(next_url, depth + 1)

            else:
                print(f"Failed to retrieve {url}: Status code {response.status_code}")

        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")

        time.sleep(1)  # Be polite: wait 1 second between requests

if __name__ == "__main__":
    start_url = "https://docs.nvidia.com/cuda/"
    crawler = WebCrawler(start_url)
    crawler.crawl(start_url)

print("Crawling completed.")