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

    '''Takes in a dictionary of word:frequency pairs, outputs the 64bit integer fingerprint'''
    weighted_vector = [0]*64
    fingerprint = [0]*64

    for word, freq in word_frequencies.items():

        #Hash and cast it to a 64 bit integer
        word_hash = hash(word) & 0xFFFFFFFFFFFFFFFF

        #Modifying the weighted vector by the words hash multiplied by its frequency
        for i in range(64):
            if (word_hash >> i) & 1:
                weighted_vector[i] += freq
            else:
                weighted_vector[i] -= freq

    #Mapping positive to 1 and negative to 0 in the resultant vector
    for i in range(64):
        if weighted_vector[i] > 0:
            fingerprint[i] = 1

    #Returning 64bit int using the vector from previous step
    res = 0
    for i in range(64):
        if fingerprint[i] == 1:
            res += 2 ** i

    return res

def getHammingDistance(a, b):
    '''Takes in two integers, returns the number of different bits between the two'''
    res = a ^ b
    return bin(res).count('1')