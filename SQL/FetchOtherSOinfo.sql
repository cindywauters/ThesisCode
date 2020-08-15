/* now fetch title, tags and id. See other notes for more explanation*/

ELECT Id, Tags, Title
FROM `sotorrent-org.2020_01_24.Posts`
WHERE Id IN (SELECT first_SO_post_mentioned FROM `gothic-venture-268213.ghissues_1.issue_IDs`);