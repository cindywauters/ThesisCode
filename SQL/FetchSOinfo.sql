/* Google bigquery used because only one time needed. 
Fetches all posts (code and text) from SO posts mentioned in issues (here uploaded in gothic-venture-268213.ghissues_1)
SuccCount=0 for latest version*/

SELECT PostBlockTypeId, PostId, content 
FROM `sotorrent-org.2020_01_24.PostBlockVersion`
WHERE PostId IN (SELECT first_SO_post_mentioned FROM `gothic-venture-268213.ghissues_1.issue_IDs`) AND SuccCount=0;