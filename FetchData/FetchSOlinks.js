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


function InsertSOids() {
    var sql_get_issue = 'SELECT comments_url, id_in_db FROM filtered_issue_info'; //get url of the comments
    con.query(sql_get_issue, function (err, result, fields) {
        if (err) throw err;
        for (let i = 0; i < 1000; i++) {
            //WARNING: run this file multiple times, incrementing the values of the loop
            //if the loop goes from 0 to the highest ID in the database, the GitHub API calls will fail due too many calls in a minute
            //next loop  -> for (let i = 1000; i < 2000; i++), then for (let i = 2000; i < 3000; i++) etc
            const getreq = octokit.request("GET " + result[i].comments_url); //get the comments of the issue
            const resolvedpromise = Promise.resolve(getreq);
            getreq.then(function (value) {
                for (let n = 0; n < value.data.length; n++) { //multiple comments -> loop over all
                    var body_comment = value.data[n].body;
                    if (body_comment.includes('stackoverflow.com/questions/')) { //only look at comment that mentions a SO post
                        link_SO = body_comment.match(/stackoverflow\.com\/questions\/(\d+)\//); //Find the link to the post
                        //Take id of the post out of link (element on index 1 because of /(\d+)\ in the match above) and put in db
                        var sql1 = 'UPDATE filtered_issue_info SET first_SO_post_mentioned = ' + link_SO[1] + ' WHERE id_in_db = ' + result[i].id_in_db + ';';
                        con.query(sql1, function (err, result) {
                            if (err) throw err;
                        });
                        var sql2 = 'UPDATE filtered_issue_info SET main_language = \'Python\';'; //change main language manually depending on which issues we are fetching 
                        con.query(sql2, function (err, result) {
                            if (err) throw err;
                        });
                        break; //Only look for the first mentioned SO post -> break the loop when found 
                    }
                }
            });
        }
    });
}

InsertSOids();