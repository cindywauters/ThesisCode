require('dotenv').config();

const { Octokit } = require("@octokit/rest");

const octokit = new Octokit({
    auth: process.env.GH_AUTH,
    userAgent: process.env.GH_AGENT,
    timeZone: 'Europe/Brussels',
    baseUrl: 'https://api.github.com',
    log: {
        debug: () => { },
        info: () => { },
        warn: console.warn,
        error: console.error
    },
    request: {
        agent: undefined,
        fetch: undefined,
        timeout: 0
    }
});

var mysql = require('mysql');

var con = mysql.createConnection({
    host: process.env.MYSQL_HOST,
    user: process.env.MYSQL_USER,
    password: process.env.MYSQL_PASSWORD,
    database: process.env.MYSQL_DB
});


const options = octokit.search.issuesAndPullRequests.endpoint.merge({
    q: 'stackoverflow.com/questions/+type:issue+language:python+in:comments+is:closed+comments:18..24',
    // change searchquery and run again for more (mainly is:open to is:closed and comments: to different values and different languages)
    // This because github only returns first 1000, so in order to get more, the searchquery will be changed and rerun
    per_page: 100,
});

octokit.paginate(options).then(issues => {
    var results = issues;
    for (let i = 0; i < issues.length; i++) { //loop over all results
        var singleresult = results[i];
        //extract data per result
        var url_issue = singleresult.html_url;
        var url_comment_issue = singleresult.comments_url;
        var id = singleresult.id;
        var title_issue = "" + singleresult.title; // + to make string
        var labels_of_issue = singleresult.labels;
        var issueLabels = ""; // empty string means no labels 

        for (var n in labels_of_issue) { //loop needed because multiple labels, loop over each one
            //to replace emoticons; code from https://stackoverflow.com/questions/10992921/how-to-remove-emoji-code-using-javascript
            issueLabels += labels_of_issue[n].name.replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g, '') + " "; 
        }

        var body_of_issue = "" + singleresult.body; //make it a string even if it's empty 

        if (body_of_issue.length > 1) { //get rid of invalid characters 
            //Needed to get rid of newlines and quotes (for easier usage in the MySQL database)
            body_of_issue = body_of_issue.replace(/(\r\n|\n|\r|[\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g, " "); //from https://stackoverflow.com/questions/784539/how-do-i-replace-all-line-breaks-in-a-string-with-br-tags and https://stackoverflow.com/questions/10992921/how-to-remove-emoji-code-using-javascript
            body_of_issue = body_of_issue.replace(/("|')/g, "");//from https://stackoverflow.com/questions/7760262/replace-both-double-and-single-quotes-in-javascript-string
        }

        if (title_issue.length > 1) { //get rid of invalid characters
            title_issue = title_issue.replace(/("|')/g, "");
            title_issue = title_issue.replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g, '');//to replace emoticons; code from https://stackoverflow.com/questions/10992921/how-to-remove-emoji-code-using-javascript
        }

        //code below from https://www.w3schools.com/nodejs/nodejs_mysql_insert.asp
        var sql = 'INSERT INTO issue_info (real_id_issue, labels, title, body, html_url, comments_url) VALUES (' + id + ', \'' + issueLabels + '\', \'' + title_issue.toString() + '\', \'' + body_of_issue + '\', \'' + url_issue + '\', \'' + url_comment_issue + '\');';
        con.query(sql, function (err, result) {
            if (err) throw err;
        });
    }
    console.log("finished loop");
    // console.log(value);
});
