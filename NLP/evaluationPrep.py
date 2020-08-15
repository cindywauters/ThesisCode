import sys
from gensim.models.keyedvectors import KeyedVectors
import mysql.connector
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
import nltk
from nltk.stem import WordNetLemmatizer 
import re
import time
import operator
from sshtunnel import SSHTunnelForwarder

#This fine is for preparing the data needed for the evaluation
#It matches ten Stack Overflow per issue from the test database and puts it into the correct column for later use
load_dotenv()

#connect to issue db
mydb_issues = mysql.connector.connect(
  host=os.getenv("MYSQL_HOST"),
  user=os.getenv("MYSQL_USER"),
  passwd=os.getenv("MYSQL_PASSWORD"),
  database=os.getenv("MYSQL_DB")
)

#connect to remote server where SOTorrent db is hosted
server = SSHTunnelForwarder(
    os.getenv("SSH_HOST"),
    ssh_username=os.getenv("SSH_hostname"),
    ssh_password=os.getenv("SSH_pass"),
    remote_bind_address=("127.0.0.1", 3306)
)
server.start()

#connect to SOTorrent database
sotorrent = mysql.connector.connect(
  host="127.0.0.1",
  port=server.local_bind_port,
  user=os.getenv("sotor_user"),
  passwd=os.getenv("sotor_password"),
  database=os.getenv("sotor_db"))

cursor_sotorrent = sotorrent.cursor()
lemmatizer = WordNetLemmatizer() 
#query of the posts we search through
cursor_sotorrent.execute("SELECT Id, body, title FROM sotorrent24_01.Posts WHERE PostTypeId=1 AND score>0 AND answercount>0 AND LastActivityDate > '2019-06-01 00:00:00' AND Tags LIKE '%python%'")
#fetch 1000 at a time only, otherwise it would be too much data
posts = cursor_sotorrent.fetchmany(1000)

cursor_issues = mydb_issues.cursor()
#do only a few issues at a time and rerun to get more data
#if the data is too much and the query is too slow, the connection with the remote database tends to close off
cursor_issues.execute("SELECT real_id_issue, title, body FROM Issuestocheck LIMIT 50 OFFSET 0;");
issues = cursor_issues.fetchall();

REPLACE_BY_SPACE_RE = re.compile('[/(){}\[\]\|@,;]')
BAD_SYMBOLS_RE = re.compile('[^0-9a-z #+_]')
STOPWORDS = set(stopwords.words('english'))

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

#word embeddings from Efstathiou, V., Chatzilenas, C., Spinellis, D., 2018. "Word Embeddings for the Software Engineering Domain". In Proceedings of the 15th International Conference on Mining Software Repositories. ACM.i
word_vect = KeyedVectors.load_word2vec_format("SO_vectors_200.bin", binary=True)
start = time.time()
start_complete = time.time()
print("done fetching vectors")

#keeps dictionary of dictionaries with the results for each issue
bestmatchings = {}

#store the sentences after being cleaned into a dictionary so they don't have to be cleaned multiple times
initial_sentences = {}

for issue in issues:
    bestmatchings[issue[0]] = {}
    initial_sentences[issue[0]] = clean_text(issue[1] + " " + issue[2])

#per post we fetched from the SOTorrent database -> combine title and body and clean
#then go through all the previously fetched issues
#per issue, calculate the cosine similarity between the post and the issue
#if the cossim is bigger than any of the ones stored in the dictionary for that issue -> swap them out for the new post
#this way only the ten posts with the highest cosine similarity stay within the dictionary per post
#afterwards, fetch more SO posts from the database and repeat
while posts:
    for post in posts:
        new_text=post[1]+" "+post[2]
        new_text=clean_text(new_text)
        for issue in issues:
            initial_sentence = initial_sentences.get(issue[0])
            bestmatching = bestmatchings.get(issue[0])
            cossim = 0
            if(len(new_text) != 0 and len(initial_sentence) != 0):
                 cossim = word_vect.n_similarity(initial_sentence.split(), new_text.split())
            if(len(bestmatching) <10):
                 bestmatching[post[0]] = cossim
            elif(min(bestmatching.items(), key=operator.itemgetter(1))[1] < cossim):
                del bestmatching[min(bestmatching.items(), key=operator.itemgetter(1))[0]]     
                bestmatching[post[0]] = cossim
    print("1000 done in ", time.time() - start)
    start = time.time()
    posts = cursor_sotorrent.fetchmany(1000)

sotorrent.close()
server.stop()

#Sort the dictionary per issue so that the posts with the highest results will be first (this returns a list)
#per issue -> save the new information (the list) in the database for easy access later on
for issue in issues:
    bestmatch = sorted(bestmatchings.get(issue[0]).items(), key=lambda x: x[1], reverse=True) #sorted(bestmatchings.get(issue[0]).keys())
    cursor_issues.execute("UPDATE Issuestocheck SET Results = \"" + str(bestmatch) + " \" WHERE Real_id_issue =" + str(issue[0]) + ";")
    mydb_issues.commit()

print("time elapsed for fetching and cleaning: ", time.time() - start_complete)
print(initial_sentences)
print("\n")
print(bestmatchings)
sotorrent.close()
server.stop()
