from flask import Flask, Response, jsonify
from neomodel import config
import redis

def create_app():
    app = Flask(__name__)

    # Configure Redis connection
    #TODO: uncomment below, set with Redis info. This is default setup.
    #redis_conn = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    # Neo4J Stuff
    #TODO: uncomment below, set with neo4j db you want to use. Format for default setup.
    #config.DATABASE_URL = 'bolt://user:password@localhost:7687'
    config.AUTO_INSTALL_LABELS = True


    return app, redis_conn

app , redis_conn = create_app()

import harmonic_take_home.routes
