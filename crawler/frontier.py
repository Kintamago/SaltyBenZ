import os
import shelve

from threading import Thread, RLock
from queue import Queue, Empty
import time 
from utils import get_logger, get_urlhash, normalize
from scraper import is_valid
import threading
from datetime import datetime, timedelta
from urllib.parse import urldefrag, urlparse

allowed_domains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu", }
class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()
        self.lock = threading.RLock()
        self.seen = set()
        self.delays = dict()
        
        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url, set(), dict()):
                with self.lock:
                    self.to_be_downloaded.append(url)
                    tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        #! THIS PART IS IMPORTANTT FOR TRHEADING< MIGHT WANNA POP OTHER INDEX
        with self.lock:
            try:
                return self.get_valid_url()
            except IndexError:
                return None
        

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        with self.lock:
            if urlhash not in self.save:
                if urlhash not in self.seen:
                    self.save[urlhash] = (url, False)
                    self.save.sync()
                    self.seen.add(url)
                    self.to_be_downloaded.append(url)
            else:
                _, completed = self.save[urlhash]
                if not completed:
                    return
    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        with self.lock:
            if urlhash not in self.save:
                self.logger.error(
                    f"Completed url {url}, but have not seen it before.")
            self.save[urlhash] = (url, True)
            self.save.sync()

    def get_base_domain(self, domain):
        parts = domain.split('.')
        # Handle cases like 'sub.example.co.uk' → 'example.co.uk'
        return '.'.join(parts[-3:]) if len(parts) >= 3 else domain

    def get_last_time_domain_hit(self, domainName) -> bool:
        
        # if any(domainName == d or domainName.endswith("." + d) for d in allowed_domains):
            # key = self.get_base_domain(domainName)

        if domainName not in self.delays:
            return True

        change = datetime.now() - self.delays[domainName]

        if change >= timedelta(seconds=0.5): 
            print(f'TIME IN MS {(change.total_seconds() * 1000):.2f}')
            return True
        else:
            return False 
        
        #return False


    def get_tbd_at(self, index):
        with self.lock:
            try:
                return self.to_be_downloaded.pop(index)
            except IndexError:
                return None
            
    def get_valid_url(self):
        print(len(self.to_be_downloaded))
        j = 0
        
            
        #debatable use here. otherwise max at 4 crawlers.
        if len(self.to_be_downloaded) == 0:
            time.sleep(1)
        while len(self.to_be_downloaded) != 0:
            if j > 100:
                print("WE COULDN't FIND A GOOD LINK TO SEARCH")
                return None
        

            i = 0
            while True:
                
                if i >= len(self.to_be_downloaded):
                    break
                url = self.to_be_downloaded[i]
                url = url.lower()
                page, _ = urldefrag(url)
                parsed = urlparse(page)
                subdomain = parsed.hostname
                if subdomain:
                    if self.get_last_time_domain_hit(subdomain):
                        self.delays[subdomain] = datetime.now()
                        return self.to_be_downloaded.pop(i)
                    else:
                        i += 1

                else:
                    print(" WE HAVE AN ERROR GETTING THE NEXT URL ")
            
            if len(self.to_be_downloaded) == 0:
                return None
            time.sleep(.05)
            j += 1
        
        