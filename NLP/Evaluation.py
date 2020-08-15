import json
import statistics
import mysql.connector
import re
import sys
from gensim.models.keyedvectors import KeyedVectors
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
import nltk
from nltk.stem import WordNetLemmatizer 
import re
import time
import operator
from sshtunnel import SSHTunnelForwarder
import matplotlib as mpl 

# in this file, a number of ways to evaluate the data are shown
# agg backend is used to create plot as a .png file
mpl.use('agg')

import matplotlib.pyplot as plt 

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

cursor_issues = mydb_issues.cursor()
cursor_issues.execute("SELECT real_id_issue, first_so_post_mentioned, Results, title, body FROM Issuestocheck;")
posts = cursor_issues.fetchall()
amount_in_top_3 = 0
amount_in_top_5 = 0
amount_in_top_10 = 0
total_found = 0
found_pairs = []

#to see how many in each top 
for post in posts:
    different_values = re.split(r"\)", post[2])
    for i, string in enumerate(different_values):
        key_values = string.replace("(", "").replace("[", "").replace(",", "").replace(")", "").replace("]", "").split()
        if(key_values and int(key_values[0]) == post[1]):
            if(i < 3):
                amount_in_top_3 = amount_in_top_3+1
            if(i < 5): 
                amount_in_top_5 = amount_in_top_5+1
            amount_in_top_10 = amount_in_top_10+1
            total_found = total_found+1
            found_pairs.append(post[0])

    print(amount_in_top_3)
    print(amount_in_top_5)
    print(amount_in_top_10)
print(total_found)
print(found_pairs)

#write into text file for easy access later
res_file = open(r"results.txt","w")
res_file.write("amount top 3 ")
res_file.write(str(amount_in_top_3))
res_file.write("\n amount top 5 ")
res_file.write(str(amount_in_top_5))
res_file.write("\n amount top 10 ")
res_file.write(str(amount_in_top_10))
res_file.write("\n found")
res_file.write(str(found_pairs))


all_values_found = []
#used to calculate the mean of all the textual similarities of the recommended posts (top 10)
for post in posts:
    different_values = re.split(r"\)", post[2])
    string = different_values[0]
    for i, string in enumerate(different_values): 
        key_values = string.replace("(", "").replace("[", "").replace(",", "").replace(")", "").replace("]", "").split()
        if(key_values):
            all_values_found.append(float(key_values[1]))

#print(all_values)
print(statistics.mean(all_values_found))
print(len(all_values_found))

res_file.write("\n all values of our recs \n")
res_file.write(str(all_values_found))

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

word_vect = KeyedVectors.load_word2vec_format("SO_vectors_200.bin", binary=True)

similarity_recommended = []
very_unmatching = []
#to see how similar issues are to the SO posts recommended by people
#fetch per issue the SO post that was recommended by people
#then calculate the cosine similarity of the post and the issue and put them in the list
#very_unmatching keeps all the ids of the post with a low cosine similarity
#this way we can easily check them later
for post in posts:
    cursor_sotorrent.execute("SELECT Id, body, title, ViewCount, AnswerCount, CommentCount, FavoriteCount, Score FROM sotorrent24_01.Posts WHERE Id=" + str(post[1]) + ";")
    corresponding_so_post = cursor_sotorrent.fetchone()
    so_post = corresponding_so_post[1] + " " + corresponding_so_post[2]
   # print(so_post)
    so_post = clean_text(so_post)
    issue = post[3] + " " + post[4]
    issue = clean_text(issue)
    cossim = 0
    if(len(so_post) != 0 and len(issue) != 0):
        cossim = word_vect.n_similarity(so_post.split(), issue.split())
    similarity_recommended.append(cossim)
    if(cossim < 0.4):
        very_unmatching.append(post[0])


similarity_random = []
#find similarity of random posts
cursor_sotorrent.execute("SELECT Id, body, title FROM sotorrent24_01.Posts WHERE PostTypeId=1 AND score>0 AND answercount>0 AND LastActivityDate > '2019-06-01 00:00:00' AND Tags LIKE '%python%' LIMIT " + str(len(posts)+1) + ";")
for post in posts:
    corresponding_so_post = cursor_sotorrent.fetchone()
    so_post = corresponding_so_post[1] + " " + corresponding_so_post[2]
   # print(so_post)
    so_post = clean_text(so_post)
    issue = post[3] + " " + post[4]
    issue = clean_text(issue)
    cossim = 0
    if(len(so_post) != 0 and len(issue) != 0):
        cossim = word_vect.n_similarity(so_post.split(), issue.split())
    similarity_random.append(cossim)

sotorrent.close()
server.stop()
res_file.write("\n all values of their recommended \n")
res_file.write(str(similarity_recommended))
res_file.close()

#print(similarity_recommended)
data_to_plot = [all_values_found, similarity_recommended, similarity_random]
# Create a figure instance
fig1 = plt.figure(1, figsize=(9, 6))

# Create an axes instance
ax = fig1.add_subplot(111)

# Create the boxplot
bp = ax.boxplot(data_to_plot, labels=["Bot", "People", "non-matching"])

# Save the figure
fig1.savefig('fig1.png', bbox_inches='tight')

print(statistics.mean(similarity_recommended))