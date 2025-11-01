import re
import utils
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag
from helper import stopwords, getFingerprint, getHammingDistance
from threading import current_thread

import threading
import time


allowed_domains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu", }

def scraper(url, resp, seen_pages, seen_subdomains, global_word_frequencies, max_words, fingerprints):
    '''Takes in the root url, extracts all immediate hyper links from the html data from extract_next_links, '''
    links = extract_next_links(url, resp, global_word_frequencies, max_words, fingerprints)
    # Iterates over list of links (str) and returns the string if it is valid
    return [link for link in links if is_valid(link, seen_pages, seen_subdomains)]

def extract_next_links(url, resp, global_word_frequencies, max_words, fingerprints):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    links = [] 

    #only valid contents (Prints error)
    if resp.status != 200: 
        print(resp.error)
        return links
    
    if not resp.raw_response or not resp.raw_response.content: #
        return links
    
    try:
        #Parse HTML content
        soup = BeautifulSoup(resp.raw_response.content, 'lxml')

        #Remove all anchor tags
        for anchor in soup.find_all('a', href=True):

            #Makes an absolute URL from relative URL
            absolute_url = urljoin(resp.url, anchor['href'])

            #Remove fragments 
            defrag_url, _ = urldefrag(absolute_url)

            if defrag_url:
                links.append(defrag_url)

        #Extracting words and frequencies (total and individually)

        local_word_frequencies = dict()

        text = soup.get_text(separator=' ')
        tokens = re.split(r'[^a-zA-Z0-9]+', text.lower())

        #Filtering out all tokens with length less than 2
        tokens = [t for t in tokens if len(t) > 2]

        for token in tokens:
            global_word_frequencies[token] = global_word_frequencies.get(token, 0) + 1

            if token not in stopwords:
                local_word_frequencies[token] = local_word_frequencies.get(token, 0) + 1

        #Fingerprinting with SimHash
        fingerprint = getFingerprint(local_word_frequencies)

        if fingerprint in fingerprints:
            print(f"Fingerprint match found for {url}, skipping")
            return []

        for element in fingerprints:
            #Hardcoded threshold if less than n elements are different, it is too similar. If too similar, the fingerprint isnt added and empty list returns
            if getHammingDistance(fingerprint, element) <= 8:
                print(f"Similar fingerprint, distance = {distance}) for {url}")
                return []

        fingerprints.add(fingerprint)

        
        # Update the longest_page_url and max_words
        if len(tokens) > max_words[0]:
            max_words[0] = len(tokens)  
            current = current_thread()                 
            if hasattr(current, 'longest_page_url'):   
                current.longest_page_url = url        

    except Exception as e:
        print(f"There was an error extracting from {url} : {e}")
    
    return links


def is_valid(url, seen_pages, seen_subdomains):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:

        url = url.lower()
        page, _ = urldefrag(url)
        parsed = urlparse(page)
        subdomain = parsed.hostname

        if page in seen_pages:
            return False

        if parsed.scheme not in {"http", "https"}:
            return False

        if subdomain:
            if not any(subdomain == d or subdomain.endswith("." + d) for d in allowed_domains):
                print(f"DROPPED {parsed}")
                return False
                
        if subdomain:
            seen_subdomains[subdomain] = seen_subdomains.get(subdomain, 0) + 1
        if page:
            seen_pages.add(page)

        path_params = parsed.path.lower()
        query_params = parsed.query.lower()
        dynamic_scripts = ['doku.php', 'events', '~eppstein']

        if any(script in path_params for script in dynamic_scripts):
            print(f"DROPPED (dynamic script with params): {url}")
            return False
            
        if any(param in query_params for param in ['ical=', 'outlook-ical=', 'google-calendar=', 'webcal=']):
            return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise


