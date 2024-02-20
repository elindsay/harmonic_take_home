import redis
import json
import time
import datetime
import random

redis_conn = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

new_people = []

# Company Ids for LinkedIn, Microsoft and Lynda
company_ids = [3278851,3205143, 2001628]
# Random Job Titles
job_titles = [
    'Chief Chatter',
    'Digital Overlord',
    'Wizard of Light Bulb Moments',
    'Dream Alchemist',
    'Retail Jedi',
    'Wizard of Want',
    'Marketing Rockstar',
    'Happiness Advocate',
    'Brand Warrior',
    'Chief of Unicorn Division',
    'Head Cheese',
    'Idea Brewer',
    'Conversation Architect',
    'Chief Thought Provoker',
    'Digital Dynamo',
    'Innovation Sherpa',
    'Social Media Trailblazer',
    'Content Wizard',
    'Full Stack Magician',
    'Global Talent Acquisition Ninja'
]
start_time = time.time()

def current_timestamp():
    timestamp_obj = datetime.datetime.fromtimestamp(time.time())
    return timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")

while(time.time() - start_time < 30):
    time.sleep(random.random())

    person_employment_data = {
		"company_id": company_ids[random.randint(0,2)],
		"person_id": random.randint(1000000, 9999999),
		"employment_title": job_titles[random.randint(0, 19)],
		"start_date": current_timestamp()
	}
    print(person_employment_data)
    new_people.append(person_employment_data)
    person_employments_create_data = {
        "type": "person_employments",
        "data": [person_employment_data]
    }

    stringified_data = json.dumps(person_employments_create_data)
    redis_conn.publish('flask_channel', stringified_data)


while(len(new_people) > 0):
    person_employment_data = new_people.pop(random.randint(0, len(new_people) -1))
    print("About to fire:")
    print(person_employment_data)
    person_employment_data['end_date'] = current_timestamp()

    person_employments_create_data = {
        "type": "person_employments_edit",
        "data": person_employment_data
    }

    stringified_data = json.dumps(person_employments_create_data)
    redis_conn.publish('flask_channel', stringified_data)
    time.sleep(random.random())

