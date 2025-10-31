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


class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()
        self.lock = threading.RLock()
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
                self.save[urlhash] = (url, False)
                self.save.sync()
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

    def get_last_time_domain_hit(self, domainName) -> bool:
        if domainName not in self.delays:
            return True
        change = datetime.now() - self.delays[domainName]
        return change < timedelta(seconds=.5)

    def get_tbd_at(self, index):
        with self.lock:
            try:
                return self.to_be_downloaded.pop(index)
            except IndexError:
                return None
            
    def get_valid_url(self):
        print(len(self.to_be_downloaded))
        with self.lock:
            while len(self.to_be_downloaded) != 0:
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
                time.sleep(.1)
            