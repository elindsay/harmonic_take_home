import redis
import json
import time
import datetime

redis_conn = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

f = open("Companies.json")
companies_data = json.load(f)

companies_create_data = {
    "type": "companies",
    "data": companies_data
}

stringified_data = json.dumps(companies_create_data)
redis_conn.publish('flask_channel', stringified_data)

f = open("PersonEmployment.json")
person_employments_data = json.load(f)

person_employments_create_data = {
    "type": "person_employments",
    "data": person_employments_data
}

stringified_data = json.dumps(person_employments_create_data)
restored_data = json.loads(stringified_data)
redis_conn.publish('flask_channel', stringified_data)

f = open("CompanyAcquisition.json")
company_acquisitions_data = json.load(f)

company_acquisitions_create_data = {
    "type": "company_acquisitions",
    "data": company_acquisitions_data
}

stringified_data = json.dumps(company_acquisitions_create_data)
redis_conn.publish('flask_channel', stringified_data)

print("db_uploader finished")
