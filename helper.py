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

def getFingerprint(word_frequencies):

    weighted_vector = [0]*64
    fingerprint = [0]*64

    for word, freq in word_frequencies.items():

        word_hash = hash(word) & 0xFFFFFFFFFFFFFFFF

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

    return res



# def customHash(word):
#     '''Hashes the word into a 64 bit hash'''
#     large_prime = 16908799
#     result = 0
#     for c in word:
#         result = (127 * result + ord(c)) % large_prime
    
#     result &= 0xFFFFFFFFFFFFFFFF

#     return result 

def getHammingDistance(a, b):
    res = a ^ b
    return bin(res).count('1')