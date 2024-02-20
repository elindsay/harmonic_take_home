from flask import Flask, Response, jsonify
import redis
from neomodel import StructuredNode, StringProperty, config, UniqueProperty

from harmonic_take_home import app
