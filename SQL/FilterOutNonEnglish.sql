select DISTINCT title, body, first_SO_post_mentioned 
from issue_info 
where title NOT regexp '[^ -~]' AND first_SO_post_mentioned IS NOT NULL;