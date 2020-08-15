from nltk.corpus import stopwords
from bs4 import BeautifulSoup
import nltk
from nltk.stem import WordNetLemmatizer 
import re

REPLACE_BY_SPACE_RE = re.compile('[/(){}\[\]\|@,;]')
BAD_SYMBOLS_RE = re.compile('[^0-9a-z #+_]')
STOPWORDS = set(stopwords.words('english'))

word_vect = KeyedVectors.load_word2vec_format("SO_vectors_200.bin", binary=True) 

def clean_text(text):
    soup = BeautifulSoup(text, "lxml")
    codeblocks = soup.findAll('code')
    for match in codeblocks:
        match.decompose()
    text = str(soup)
    text = BeautifulSoup(text, "lxml").text # HTML decoding
    text = text.lower() # lowercase text
    text = REPLACE_BY_SPACE_RE.sub(' ', text) # replace REPLACE_BY_SPACE_RE symbols by space in text
    text = BAD_SYMBOLS_RE.sub('', text) # delete symbols which are in BAD_SYMBOLS_RE from text
    text = ' '.join(word for word in text.split() if word not in STOPWORDS) # delete stopwors from text
    text = ' '.join(word for word in text.split() if word in word_vect.vocab) # delete non embedded words
    return text