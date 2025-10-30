import re
import sys
import requests
from bs4 import BeautifulSoup
from helper import stopwords, getFingerprint, getHammingDistance

def get_page_fingerprint(url):
    """
    Downloads the page, extracts text, tokenizes words, and returns its SimHash fingerprint.
    """
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"[ERROR] Failed to fetch {url} (status {resp.status_code})")
            return None

        soup = BeautifulSoup(resp.text, "lxml")
        text = soup.get_text(separator=' ')

        # tokenize, lowercase, and filter
        tokens = re.split(r'[^a-zA-Z0-9]+', text.lower())
        tokens = [t for t in tokens if t and t not in stopwords]

        # count word frequencies
        local_word_frequencies = {}
        for token in tokens:
            local_word_frequencies[token] = local_word_frequencies.get(token, 0) + 1

        # generate fingerprint using your existing function
        fingerprint = getFingerprint(local_word_frequencies)
        return fingerprint

    except Exception as e:
        print(f"[ERROR] Failed to process {url}: {e}")
        return None


def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_fingerprints.py <url1> <url2>")
        sys.exit(1)

    url1, url2 = sys.argv[1], sys.argv[2]

    f1 = get_page_fingerprint(url1)
    f2 = get_page_fingerprint(url2)

    if f1 is None or f2 is None:
        print("Could not compute fingerprints for one or both URLs.")
        sys.exit(1)

    print(f"\nFingerprint 1: {f1}")
    print(f"Fingerprint 2: {f2}")

    distance = getHammingDistance(f1, f2)
    print(f"\nHamming Distance: {distance}")

    if distance <= 8:
        print("Similar/Duplicates")
    else:
        print("Distinct")


if __name__ == "__main__":
    main()
