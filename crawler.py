import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
import hashlib

class WebCrawler:
    def __init__(self, start_url, max_depth=1, output_dir='crawled_content_pt2'):
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

    def extract_text_content(self, soup):
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    def save_content(self, url, content):
        file_name = self.get_file_name(url)
        file_path = os.path.join(self.output_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><body><pre>{content}</pre></body></html>")
        
        print(f"Saved: {file_path}")

    def crawl(self, url, depth=0):
        if depth > self.max_depth or not self.is_valid_url(url):
            return

        print(f"Crawling: {url} (Depth: {depth})")

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
                self.visited.add(url)
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract and save the content
                extracted_content = self.extract_text_content(soup)
                self.save_content(url, extracted_content)
                
                # Find all links on the page
                links = soup.find_all('a', href=True)
                for link in links:
                    next_url = urljoin(url, link['href'])
                    if next_url not in self.visited:
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