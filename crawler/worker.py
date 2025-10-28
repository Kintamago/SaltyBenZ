from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier

        self.seen_pages = set()
        self.seen_subdomains = dict()
        self.global_word_frequencies = dict()
        self.fingerprints = set()
        self.max_words = [0]

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
            scraped_urls = scraper.scraper(tbd_url, resp, self.seen_pages, self.seen_subdomains, self.global_word_frequencies, self.max_words, self.fingerprints)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
        self.summary_output()

    
    def summary_output(self):
        # Stopwords from https://www.ranks.nl/stopwords Default English stopwords list
        stopwords = {"a","about","above","after","again","against","all","am","an","and","any",
        "are","arent","as","at","be","because","been","before","being","below",
        "between","both","but","by","cant","cannot","could","couldnt","did","didnt",
        "do","does","doesnt","doing","dont","down","during","each","few","for","from",
        "further","had","hadnt","has","hasnt","have","havent","having","he","hed",
        "hell","hes","her","here","heres","hers","herself","him","himself","his",
        "how","hows","i","id","ill","im","ive","if","in","into","is","isnt","it",
        "its","its","itself","lets","me","more","most","mustnt","my","myself","no",
        "nor","not","of","off","on","once","only","or","other","ought","our","ours",
        "ourselves","out","over","own","same","shant","she","shed","shell","shes",
        "should","shouldnt","so","some","such","than","that","thats","the","their",
        "theirs","them","themselves","then","there","theres","these","they","theyd",
        "theyll","theyre","theyve","this","those","through","to","too","under",
        "until","up","very","was","wasnt","we","wed","well","were","weve","were",
        "werent","what","whats","when","whens","where","wheres","which","while","who",
        "whos","whom","why","whys","with","wont","would","wouldnt","you","youd",
        "youll","youre","youve","your","yours","yourself","yourselves"}


        # removing stopwords from word frequencies
        clean_freqs = {
            word: count
            for word, count in self.global_word_frequencies.items()
            if word not in stopwords
        }
        # can make "and word.isalpha()" if numbers are non-valid for "words"

        top_words = sorted(clean_freqs.items(), key=lambda x: x[1], reverse=True)[:50]

        total_pages = len(self.seen_pages)
        total_subdomains = len(self.seen_subdomains)
        most_visited_subdomains = sorted(
            self.seen_subdomains.items(), key=lambda x: x[1], reverse=True
            )[:10]

        # Build report lines
        lines = []
        lines.append("SUMMARY\n")
        lines.append(f"Total unique pages crawled: {total_pages}\n")
        lines.append(f"Total unique subdomains: {total_subdomains}\n")
        lines.append("Top 10 Subdomains:\n")

        for sub, count in most_visited_subdomains:
            lines.append(f"  - {sub}: {count} pages\n")

        lines.append("\nTop 50 Words (filtered):\n")

        for word, count in top_words:
            lines.append(f"  {word:<20} {count}\n")

        filename = f"worker_{self.name}_summary.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)

        self.logger.info(f"Summary written to {filename}")