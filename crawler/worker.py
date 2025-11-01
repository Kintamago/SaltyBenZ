from threading import Thread
from helper import stopwords, getFingerprint, getHammingDistance
from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper

from .frontier import Frontier
import time

class Worker(Thread):
    def __init__(self, worker_id, config, frontier:Frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier

        self.seen_pages = set()
        self.seen_subdomains = dict()
        self.global_word_frequencies = dict()
        self.fingerprints = set()
        self.max_words = [0]
        self.longest_page_url = None
        
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp, self.frontier.seen, self.seen_subdomains, self.global_word_frequencies, self.max_words, self.fingerprints)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
        self.summary_output()

    
    def summary_output(self):

        # removing stopwords from word frequencies
        clean_freqs = {
            word: count
            for word, count in self.global_word_frequencies.items()
            if word not in stopwords
        }
        # can make "and word.isalpha()" if numbers are non-valid for "words"


        total_pages = len(self.seen_pages) #good
        total_subdomains = len(self.seen_subdomains) #good 
        all_visited_subdomains = sorted(           #good
            self.seen_subdomains.items(), key=lambda x: x[1], reverse=True
            )
        
        with self.frontier.lock:
            #chat gpt generated merging code.
            # merge word frequencies
            for w, c in self.global_word_frequencies.items():
                self.frontier.data["word_freq"][w] = (
                    self.frontier.data["word_freq"].get(w, 0) + c
                )

            # merge pages
            self.frontier.data["visited_pages"].update(self.seen_pages)

            # merge subdomains
            for sub, count in self.seen_subdomains.items():
                self.frontier.data["subdomains"][sub] = (
                    self.frontier.data["subdomains"].get(sub, 0) + count
                )

            # track global max words
            self.frontier.data["max_words"][0] = max(
                self.frontier.data["max_words"][0], self.max_words[0]
            )

