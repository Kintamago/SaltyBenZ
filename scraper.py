import re
import utils
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag

allowed_domains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}


seen = set()

def scraper(url, resp):
    '''Takes in the root url, extracts all immediate hyper links from the html data from extract_next_links, '''
    links = extract_next_links(url, resp)
    # Iterates over list of links (str) and returns the string if it is valid
    return [link for link in links if is_valid(link)]



def extract_next_links(url, resp):
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
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

        #Remove all anchor tags
        for anchor in soup.find_all('a', href=True):
            #Makes an absolute URL from relative URL
            absolute_url = urljoin(resp.url, anchor['href'])

            #Remove fragments 
            defrag_url, _ = urldefrag(absolute_url)

            if defrag_url:
                links.append(defrag_url)
    except Exception as e:
        print(f"There was an error extracting from {url} : {e}")
    
    return links


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    global seen
    

    try:
        # removes anchors
        clean_url, _ = urldefrag(url)
        url = clean_url.lower()
        
        
        
        if url in seen:
            return False

        parsed = urlparse(url)
        
        if parsed.scheme not in set(["http", "https"]):
            return False

        if url.hostname not in allowed_domains:
            return False
    
        seen.add(url)

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


# Hi guys
# Run the crawler as is, see what outputs we get and compare and see what we should do
# The is valid is like a filter, filters out unwanted sites and values
# dont worry about robots.txt (assuming it alr does that)

# The way to solve multithreading is to have a centralized frontier management
# separate part of program that handles frontier, the crawlers come to this frontier for URL, the frontier uses its own logic to give out urls
# Notes I took during class while half asleep
# Ion think it should be "IR RF25 {our UCI-ID} ..."

