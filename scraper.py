import re
import utils
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag

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

        #Count words and frequencies

        #Local word_frequency for individual page for simhash
        
        local_word_frequencies = dict()

        text = soup.get_text(separator=' ')
        tokens = re.split(r'[^a-zA-Z0-9]+', text.lower())
        tokens = [t for t in tokens if t]
        for token in tokens:
            global_word_frequencies[token] = global_word_frequencies.get(token, 0) + 1
            local_word_frequencies[token] = local_word_frequencies.get(token, 0) + 1

        #get finger print, add to stored set of finger prints, if it is similar (hamming distance), 
        # return empty list to not append links




        fingerprint = getFingerprint(local_word_frequencies)

        if fingerprint in fingerprints:
            return []

        for element in fingerprints:
            #Hardcoded threshold if less than 10 elements are different, it is too similar. If too similar, the fingerprint isnt added and empty list returns
            if getHammingDistance(fingerprint, element) <= 4:
                return []

        fingerprints.add(fingerprint)




        max_words[0] = max(max_words[0], len(tokens))

    except Exception as e:
        print(f"There was an error extracting from {url} : {e}")
    
    return links


def is_valid(url, seen_pages, seen_subdomains):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        # removes anchors
    
        url = url.lower()
        page, _ = urldefrag(url)
        if page in seen_pages:
            return False

        parsed = urlparse(page)

        if parsed.scheme not in {"http", "https"}:
            return False

        subdomain = parsed.hostname

        if subdomain:
            if not any(subdomain == d or subdomain.endswith("." + d) for d in allowed_domains):
                print(f"DROPPED {parsed}")
                return False
                
        if subdomain:
            seen_subdomains[subdomain] = seen_subdomains.get(subdomain, 0) + 1
        if page:
            seen_pages.add(page)
        

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

def getFingerprint(word_frequencies):

    weighted_vector = [0]*64
    fingerprint = [0]*64

    for word, freq in word_frequencies.items():
        word_hash = customHash(word)

        for i in range(64):
            if (word_hash >> i) & 1:
                weighted_vector[i] += freq
            else:
                weighted_vector[i] -= freq

    for i in range(64):
        if weighted_vector[i] > 0:
            fingerprint[i] = 1

    res = 0
    for i in range(64):
        if fingerprint[i] == 1:
            res += 2 ** i

    res &= 0xFFFFFFFFFFFFFFFF
    return res



def customHash(word):
    '''Hashes the word into a 64 bit hash'''
    large_prime = 16908799
    result = 0
    for c in word:
        result = (127 * result + ord(c)) % large_prime
    
    result &= 0xFFFFFFFFFFFFFFFF

    return result 

def getHammingDistance(a, b):
    res = a ^ b
    return bin(res).count('1')

# Hi guys
# Run the crawler as is, see what outputs we get and compare and see what we should do
# The is valid is like a filter, filters out unwanted sites and values
# dont worry about robots.txt (assuming it alr does that)

# The way to solve multithreading is to have a centralized frontier management
# separate part of program that handles frontier, the crawlers come to this frontier for URL, the frontier uses its own logic to give out urls
# Notes I took during class while half asleep
# Ion think it should be "IR RF25 {our UCI-ID} ..."

