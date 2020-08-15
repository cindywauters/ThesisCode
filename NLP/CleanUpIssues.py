from markdown import markdown
import mysql.connector
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

mydb_issues = mysql.connector.connect(
  host=os.getenv("MYSQL_HOST"),
  user=os.getenv("MYSQL_USER"),
  passwd=os.getenv("MYSQL_PASSWORD"),
  database=os.getenv("MYSQL_DB")
)

cursor_issues = mydb_issues.cursor()

for i in range(0, 9479):
    #this for loop loops over entire database and gets each entry's body
    #range hardcoded for now 
    #this body is often in markdown langauge. Because we want to seperate the code from the normal text, and because this is easier with HTML
    #we first use markdown to render the body with HTML tags. Then we can access the codeblocks within the body.
    #Finally, all the codeblocks get put in a seperate database, and the textblocks are written back into the database without code or the markdown langauge

  cursor_issues.execute('SELECT Body FROM filtered_issue_info WHERE id_in_db=' + str(i) + ';') #get body from database
  results = cursor_issues.fetchall()

  for x in results:
    textblock = BeautifulSoup(markdown(x[0])) #render in html

 #   print(i)

    codeblocks = textblock.find_all('code') #get list of all the data between <code></code>

    for tag in textblock.find_all('code'): #remove all the codeblocks
        tag.replaceWith('')

    if codeblocks:
        codeblocks = ' '.join(str(e.get_text()) for e in codeblocks) #make from the list a string for easier use 
  #      codeblocks = codeblocks.get_text() #remove all html tags in code


    textblock = textblock.get_text() #remove all html tags in text
  #  print(i)
  #  print(str(codeblocks))
    textblock = textblock.replace('\\','\\\\').replace('\'', '\\\'')
    querystring_insert = ""

    if codeblocks:
        querystring_insert = "INSERT INTO issue_codeblocks (content, idIssue) VALUES (\'" + str(codeblocks).replace("\\","\\\\").replace('\'', '\\\'') + "\', \'" + str(i) + "\');"
    else:
        querystring_insert = "INSERT INTO issue_codeblocks (idIssue) VALUES (\'" + str(i) + "\');"

 # print(querystring_insert)

  cursor_issues.execute(querystring_insert)
  mydb_issues.commit()

  querystring_update = "UPDATE filtered_issue_info SET body = \'" + textblock + "\' WHERE id_in_db = " + str(i) + ";"
  cursor_issues.execute(querystring_update)
  mydb_issues.commit()
  #  print(querystring_update)
 #   print("INSERT INTO issue_codeblocks (idIssue, content) VALUES (\'" + codeblocks + "\', " + str(i) + ';')
 #   print("")
