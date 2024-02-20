from flask import Flask, Response, jsonify, request
import json
from neomodel import UniqueProperty
from harmonic_take_home import app, redis_conn
from harmonic_take_home.models import Company, Person, Employment, Acquisition

#Note, this is to start connection to the redis stream
@app.route('/stream')
def stream():
    print("STARTING STREAM")
    return Response(redis_subscriber(), mimetype="text/event-stream")

@app.route('/companies')
def companies():
    companies = Company.nodes.all()
    company_data = [company.to_dict() for company in companies]
    return jsonify(company_data)

@app.route('/company/<company_id>')
def company(company_id):
    # NOTE - we run up to 5 queries in this API call
    # It would be better to push these all into one query
    # But I am running out of time
    company = Company.nodes.get(company_id=int(company_id))
    company_data = {'company': company.to_dict() }

    if request.args.get('parent', False):
        parent = company.get_parent_company()
        company_data['parent'] = parent and parent.to_dict()
    if request.args.get('ancestors', False):
        ancestors = company.get_all_ancestor_companies()
        company_data['ancestors'] = [ancestor.to_dict() for ancestor in ancestors]
    if request.args.get('acquisitions', False):
        acquisitions = company.get_acquired_companies()
        company_data['acquisitions'] = [acquisition.to_dict() for acquisition in acquisitions]
    if request.args.get('descendants', False):
        descendants = company.get_all_descendant_companies()
        company_data['descendants'] = [descendant.to_dict() for descendant in descendant]

    return jsonify(company_data)

@app.route('/people')
def people():
    if request.args.get('company_ids', False):
        company_ids = json.loads(request.args.get('company_ids', False))
        if request.args.get('past', False):
            if request.args.get('present', False):
                people = Person.get_employees_in_companies(company_ids)
            else:
                people = Person.get_past_employees_in_companies(company_ids)
        elif request.args.get('present', False):
            people = Person.get_current_employees_in_companies(company_ids)
        else:
            people = Person.get_employees_in_companies(company_ids)
        people_data = [{'person_id': person['person'].person_id, 'company_name': person['company_name'], 'employment_title': person['employment_title']} for person in people]
    else:
        people = Person.nodes.all()
        people_data = [{'person_id': person.person_id} for person in people]
    return jsonify(people_data)

@app.route('/')
def index():
    return "Flask app running with Redis Pub/Sub."

def redis_subscriber():
    pubsub = redis_conn.pubsub()
    pubsub.subscribe('flask_channel')

    for message in pubsub.listen():
        if message['type'] == 'message':
            message_handler(message['data'])

def message_handler(message):
    restored_data = json.loads(message)
    data_type = restored_data['type']

    match data_type:
        case "companies":
            try:
                Company.bulk_create(restored_data["data"])
            except Exception as e:
                print(e)
        case "person_employments":
            try:
                Person.bulk_create(restored_data["data"])
                Employment.bulk_create(restored_data["data"])
            except Exception as e:
                print(e)
        case "person_employments_edit":
            try:
                Employment.edit(restored_data["data"])
            except Exception as e:
                print(e)
        case "company_acquisitions":
            try:
                Acquisition.bulk_create(restored_data["data"])
            except Exception as e:
                print(e)
        case _:
            print("Unknown type passed to message handler")
    

