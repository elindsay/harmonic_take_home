# Harmonic Take Home for Emma Lindsay

This is a python/flask app, which is running with Redis for a pub/sub replicator, and Neo4J as a database. I ended up running short on time (probably took 12 hours to complete in total) and so, there's not a front end -- just an API to access the database.

**PLEASE NOTE! The database that is set in the tests (app_test.py) WILL BE WIPED! 
Some versions of Neo4J do not allow you to create multiple databases; IF YOU USE YOUR DEFAULT DATABASE IN THE TESTS, IT WILL BE ERASED!**

I have commented out the place in the tests that wipe the database, to prevent anyone doing this by accident, but the tests will fail with this commented out. Be sure to set a database you're fine being overwritten, or just don't run the tests.

Also, in the sake of full disclosure, I used ChatGPT to help with parts of this. Most especially, I used it when writing Cypher queries for the Neo4J database because I'd never written Cypher queries before; more notes on that later.

## Design
One of the requirements of this take home was to use python; I opted to use Flask to support the HTTP API becuase I had previous experience with it. 

I also decided to use Redis to mimic pub/sub behavior because I was familiar with Redis, and because it seemed a reasonable way to mimic out something more heavy-weight, like Kafka. Effectively, I use a message handler that listens for messages from Redis, and then calls create/modify operations on the models. This is implemented in the message_handler function in the `haronic_take_home/harmonic_take_home/routes.py` file.

Probably, my most controversial decision, was to use Neo4J as a database. I opted to do it because I was (possibly over) excited by the idea of a "knowledge graph" and thought it would be a good opportunity to learn about graph databases. I also thought a graph database would be helpful for traversing the company "acquired" graph. In a more traditional SQL database, this "acquired" relationship of Company A (parent) acquiring Copay B (acquired) could be modeled by a join table that relates the companies table to itself, with (say) `parent_company_id` and `acquired_company_id` as the columns in a row on the join table. However, with a join table, (to the best of my knowledge) it is not possible to do one query for all descendent companies of a company (aka, the acquisitions of the acquired company, then the acquisitions of those companies, and so on) because you don't know how deep the the graph is going to go in advance. You would have to iterate doing n queries for a graph n nodes deep.

My understanding of graph databases is they are especially designed for this use case, and it is possible to get all descendent companies in one query. In particular, in the following code from my project, this line of the cypher query: `MATCH (parent)-[:ACQUIRED*1..]->(acquired:Company)` finds all acquired companies from 1 to infinity steps away from the parent company found in the previous line. If we had used `[:ACQUIRED*1..10]`we would have found all companies within 1 to 10 steps from the parent company, and if we'd used `[:ACQUIRED*0..]` we would have found all descendants, but returned the parent company as well because it is zero steps away. 

```python
# From harmonic_take_home/harmonic_take_home/models.py file

class Company(StructuredNode):

    ## CUT FUNCTIONS

    def get_all_descendent_companies(self):
        query = """
        MATCH (parent:Company {company_id: $company_id})
        MATCH (parent)-[:ACQUIRED*1..]->(acquired:Company)
        RETURN DISTINCT acquired
        """
        results, _ = db.cypher_query(query, params={"company_id": self.company_id})
        return [Company.inflate(row[0]) for row in results]
```

Only problem was, I have never actually used a graph database before. Probably because of my background in Rails, I have a tendency to want to use ORMs to create a model layer on top of the database, and use the ORM as much as possible to abstract away the queries. Then, if there are more complex queries that the ORM can't handle, I tend to flesh those out in the underlying query language (in this case, Cypher) in functions on the model. I am, of course, open to other design patterns when working in a larger project, but if left to my own devices, I tend to find this setup to be especially easy to test, because I can just write pretty simple model tests for the most complicated parts of the code. 

Unfortunately, the current state of python ORMs for Neo4j isn't great. Py2neo was apparently the go-to for a number of years, but it is no longer being maintained, so people have switched over to neomodel, which is still somewhat immature. (Or, I just couldn't find how to do many of the things I wanted to do using it; it was a 10 hour project, so I didn't get super in depth learning a new library.) 

In the end, I actually ended up thinking Neo4J was pretty cool, but there were some obstacles:
* The initial python ORM I used (py2neo) was no longer being supported, so ended up replacing it with a newer one (neomodel) which is still pretty new. 
* Many of the features I wanted weren't available in neomodel, so I ended up having to drop down into Cypher queries anyway, eliminating some of the usefullnes of an ORM.
* The only real benefit of the graph database was the acquisition chain of companies; things like the person_employment relationships could be adequately represented by a SQL Join because they were only ever 1 layer deep. And, in the end, not many of the acquisition graphs ended up being that large, so it was probably not worth the effort to use a less common database.

I also ended up running short on time, in part because I was using a database I was unfamiliar with, and if this was a pre-Chat GPT world, I probably wouldn't have finished. As is, I ran a few hours over (I'd estimate I spent about 12 hours on this) but it seemed in the ballpark for a 10 hour project, but I did use ChatGPT to generate first drafts of most of the Cypher queries. Obviously, one of the nice things about having unit tests, is you can test the code you get to make sure ChatGTP hasn't hallucinated anything -- but, as I ran a little shorter on time, some of those tests got a little more vague. 

Also, because I was running out of time, the "streaming" section is a bit light. I actually did use the same Redis streaming pub/sub protocol for the initial database upload, so you can see it work for all models/tables, but the actual "stream_mimicker" that runs after the initial setup only does hirings and firings -- not acquisitions. 

Here's the app structure with the highlighting relevant files (things like requirements.txt omitted):

```python
/harmonic_take_home
  db_uploader.py      # This uploads the initial version of the DB
  stream_mimicker.py  # This mimics a stream input over Redis
  app_test.py         # This has the tests
  /harmonic_take_home
    __init__.py
    models.py         # This has the ORM layer and the Cypher queries
    routes.py         # This has the http routes and the connection to the Redis Pub/Sub
```

## Running the App
To run the app, there are a few prerequs. You must have Redis and neo4j installed on your machine (I installed both using Homebrew.) I was also running Python 3.11.8 -- I assume it would work with some other versions, but it won't work very old versions of Python 3. 

I also used a virtual environment to install everything in requirements.txt; I haven't tried running it on any other machines though. 

There are to TODOs you must attend to in the `__init__.py` file to setup the db -- you must make sure redis_conn is pointing to a running version of Redis on your machine, and you must make sure config.DATABASE_URL is pointing to a running neo4j database:

```python
# harmonic_take_home/harmonic_take_home/__init__.py

    # Configure Redis connection
    #TODO: uncomment below, set with Redis info. This is default setup.
    #redis_conn = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    # Neo4J Stuff
    #TODO: uncomment below, set with neo4j db you want to use. Format for default setup.
    #config.DATABASE_URL = 'bolt://user:password@localhost:7687'
```
Then, when all that is working, you can get the app started by running 

`flask run -p 5001` (Note -- specify port 5001 because on my mac, port 5000 is reserved.) 

To get the app populated, you need to:
1. Hit the URL end point http://localhost:5001/stream once after app start
2. Run `python db_uploader.py`

To mimick a stream, you need to
1. Hit http://localhost:5001/stream once after app start (if you hit it on previous step, no need to do it again)
2. Run `python stream_mimicker.py`

To run the tests, you can just run `pytest` in the root directory, but be aware, they will wipe the db set up in testing

You can then just access the rest of the API with http requests. I use the app Rapid API (used to be Paw) to test this.

Relevant requests:
* `GET http://localhost:5001/stream` -> this starts the stream to Redis. If you hit it more than once, there will be multiple subscriptions to Redis. It also times out, but the Redis part still works (tight on time, so didn't totally clean this up.)
* `GET localhost:5001/companies` -> See list of companies, returns
    * Response form: `[{company_id:, company_name:, headcount:}, ...]`  
* `GET http://localhost:5001/company/<company_id>` -> also pass in bool variables to get additional data
    * parent (true/false - optional) -> returns `{company_id:, company_name:, headcount:} for parent (assume just one parent)
    * ancestors (true/false - optional) -> returns list `[{company_id:, company_name:, headcount:}, ...]` for all ancestors
    * acquisitions (true/false - optional) -> returns list `[{company_id:, company_name:, headcount:}, ...]` for all acquisitions (aka, one step removed)
    * descendants (true/false - optional) -> returns list `[{company_id:, company_name:, headcount:}, ...]` for all descendants (aka, one or more step removed)
    * Full Response Form: `{acquisitions:[..], ancestors:[...], company:{company_id:, company_name:, headcount:},descendents:[...],"parent":{company_id:, company_name:, headcount:}`
* `GET http://localhost:5001/people` -> Return all the people that work for a collection of companies. Variables are:
  * company_ids (list of ids, e.g. [2001628, 3205143, 25894] - mandatory) -> Will return list of people at any of these companies
  * past (true/false - optional) -> Will return people who have finished their employment
  * present (true/false - optional) -> Will return people currently working at companies
  * Note: if both past present are true, or neither are set, then all employees are returned
  * Response Form: `[{company_name:,employment_title:,person_id:}, ...]`
  



    




