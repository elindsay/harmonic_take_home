import pytest
import json
import time
import datetime
from neomodel import db, UniqueProperty
from harmonic_take_home import create_app
from harmonic_take_home.models import Company, Person, Employment, Acquisition

from harmonic_take_home.routes import message_handler

@pytest.fixture(scope="module")
def test_app():
    app, _ = create_app()
    with app.app_context():
        yield app  # this allows for teardown or cleanup after tests run

@pytest.fixture(scope="module")
def client(test_app):
    return test_app.test_client()

## TODO
## THIS FUNCTION ERASES THE DB BEFORE EVERY TEST
## I have commented it out to prevent accidental db wipe
## However, you will need to uncomment this function 
## To get the tests to work
#@pytest.fixture(scope="function", autouse=True)
#def clear_database():
#    # Clear the database before each test
#    db.set_connection("bolt://neo4j:password@localhost:7687") ## Set this -- THIS DB WILL BE WIPED!
#    query = "MATCH (n) DETACH DELETE n"
#    db.cypher_query(query)

#DB Count Methods
def get_company_count():
    query = "MATCH (c:Company) RETURN count(c) AS company_count"
    results, meta = db.cypher_query(query)
    return results[0][0]

def get_person_count():
    query = "MATCH (p:Person) RETURN count(p) AS person_count"
    results, meta = db.cypher_query(query)
    return results[0][0]

## TEST BASIC DB SETUP WORKING
def test_company_creation_works(client):
    company_count = get_company_count()
    assert company_count == 0
    Company(company_name="Great Company", headcount=3, company_id=99).save()
    company_count = get_company_count()
    assert company_count == 1

def test_duplicate_companies_not_created(client):
    company_count = get_company_count()
    assert company_count == 0
    Company(company_name="Great Company", headcount=3, company_id=99).save()
    company_count = get_company_count()
    assert company_count == 1
    with pytest.raises(UniqueProperty) as excinfo:
        Company(company_name="Mediocre Company", headcount=3, company_id=99).save()
    with pytest.raises(UniqueProperty) as excinfo:
        Company(company_name="Great Company", headcount=3, company_id=100).save()
    company_count = get_company_count()
    assert company_count == 1


## TESTS FOR BULK CREATES
def bulk_create_companies():
    companies_data = [
	{
		"company_id": 703504,
		"company_name": "Aimco Apartment Homes",
		"headcount": 1237
	},
	{
		"company_id": 6792948,
		"company_name": "MAVRK Studio",
		"headcount": 3
	},
	{
		"company_id": 3979242,
		"company_name": "PT Sing Aji Sentosa",
		"headcount": 10
	}]
    Company.bulk_create(companies_data)

def test_companies_bulk_create(client):
    company_count = get_company_count()
    assert company_count == 0
    bulk_create_companies()
    company_count = get_company_count()
    assert company_count == 3

def bulk_create_people():
    #Note -- we only use person_id, however, we test passing this
    #all in, because that's the form the incoming data is in
    person_employments_data = [
	{
		"company_id": 703504,
		"person_id": 360027,
		"employment_title": "Vice President Of Infrastructure and Operations",
		"start_date": "2012-05-01 00:00:00",
		"end_date": "2020-06-01 00:00:00"
	},
	{
		"company_id": 6792948,
		"person_id": 360027,
		"employment_title": "Infra & Ops",
		"start_date": "2010-05-01 00:00:00",
		"end_date": "2011-06-01 00:00:00"
	},
	{
		"company_id": 6792948,
		"person_id": 3676157,
		"employment_title": "Costumer Service",
		"start_date": "2017-05-01 00:00:00",
		"end_date": "2018-02-01 00:00:00"
	}]
    Person.bulk_create(person_employments_data)

def test_people_bulk_create(client):
    person_count = get_person_count()
    assert person_count == 0
    bulk_create_people()
    # Note -- two of the data entries had same person_id,
    # so we only added 2 people of 3 entries
    person_count = get_person_count()
    assert person_count == 2

def bulk_create_employments():
    #Note, we need people and companies to exist
    #To create employments
    bulk_create_companies()
    bulk_create_people()
    person_employments_data = [
	{
		"company_id": 703504,
		"person_id": 360027,
		"employment_title": "Vice President Of Infrastructure and Operations",
		"start_date": "2012-05-01 00:00:00",
		"end_date": "2020-06-01 00:00:00"
	},
	{
		"company_id": 6792948,
		"person_id": 360027,
		"employment_title": "Infra & Ops",
		"start_date": "2010-05-01 00:00:00",
		"end_date": "2011-06-01 00:00:00"
	},
	{
		"company_id": 6792948,
		"person_id": 3676157,
		"employment_title": "Costumer Service",
		"start_date": "2017-05-01 00:00:00",
		"end_date": None
	}]
    Employment.bulk_create(person_employments_data)

def test_employments_bulk_create(client):
    bulk_create_employments()
    company = Company.nodes.get(company_id=6792948)
    assert(len(company.get_employees()) == 2)
    company = Company.nodes.get(company_id=703504)
    assert(len(company.get_employees()) == 1)
    company = Company.nodes.get(company_id=3979242)
    assert(len(company.get_employees()) == 0)

def bulk_create_acquisitions():
    bulk_create_companies()
    acquisitions_data = [
        {
            "parent_company_id": 703504,
            "acquired_company_id": 6792948,
            "merged_into_parent_company": True
        },
        {
            "parent_company_id": 3979242,
            "acquired_company_id": 703504,
            "merged_into_parent_company": False
        }]
    Acquisition.bulk_create(acquisitions_data)

def test_acquisitions_bulk_create(client):
    bulk_create_acquisitions() #Will also create companies
    company = Company.nodes.get(company_id=3979242)
    assert len(company.get_acquired_companies()) == 1
    assert len(company.get_all_descendant_companies()) == 2

#Test methods on Company
def test_company_get_employees_method(client):
    bulk_create_employments() #Initiates companies, people & employments
    company = Company.nodes.get(company_id=6792948)

    #Test Basic Functionality
    employees = company.get_employees()
    assert len(employees) == 2
    employee_ids = set(map(lambda e: e['person'].person_id, employees))
    assert employee_ids == set([360027, 3676157])

    #Test that if employee hired twice, they show up twice in get_employees
    #But, they have the same id both times
    employee = employees[0]['person']
    employee.employed_at.connect(company, {
        'employment_title': 'Chief Happiness Officer',
        'start_date': datetime.datetime.strptime('2020-01-01 00:00:00', "%Y-%m-%d %H:%M:%S"),
        'end_date': None
    })
    updated_employees = company.get_employees()
    assert len(updated_employees) == 3
    updated_ids = set(map(lambda e: e['person'].person_id, updated_employees))
    assert updated_ids == set([360027, 3676157])

def test_company_get_acquired_companies(client):
    bulk_create_acquisitions() #Will also create companies
    company = Company.nodes.get(company_id=3979242)
    acquired_companies = company.get_acquired_companies()
    assert len(acquired_companies) == 1
    acquired_company_ids = map(lambda c: c.company_id, acquired_companies)
    assert set(acquired_company_ids) == set([703504])

def test_company_get_all_descendant_companies(client):
    bulk_create_acquisitions() #Will also create companies
    company = Company.nodes.get(company_id=3979242)
    descendant_companies = company.get_all_descendant_companies()
    assert len(descendant_companies) == 2
    descendant_company_ids = map(lambda c: c.company_id, descendant_companies)
    assert set(descendant_company_ids) == set([6792948, 703504])

def test_company_get_parent_company(client):
    bulk_create_acquisitions() #Will also create companies
    company = Company.nodes.get(company_id=6792948)
    parent_company = company.get_parent_company()
    assert parent_company.company_id == 703504
    company = Company.nodes.get(company_id=3979242)
    parent_company = company.get_parent_company()
    assert parent_company == None

def test_company_get_all_ancestor_companies(client):
    bulk_create_acquisitions() #Will also create companies
    company = Company.nodes.get(company_id=6792948)
    ancestor_companies = company.get_all_ancestor_companies()
    assert len(ancestor_companies) == 2
    ancestor_company_ids = map(lambda c: c.company_id, ancestor_companies)

def test_person_get_empoloyees_in_companies(client):
    bulk_create_employments() #Creates people/companies/employments
    company = Company.nodes.get(company_id=6792948)
    assert len(Person.get_employees_in_companies([6792948, 703504])) == 3

def test_person_get_current_employees_in_companies(client):
    bulk_create_employments() #Creates people/companies/employments
    company = Company.nodes.get(company_id=6792948)
    assert len(Person.get_current_employees_in_companies([6792948, 703504])) == 1

def test_person_get_past_employees_in_companies(client):
    bulk_create_employments() #Creates people/companies/employments
    company = Company.nodes.get(company_id=6792948)
    assert len(Person.get_past_employees_in_companies([6792948, 703504])) == 2

def test_edit_employment(client):
    bulk_create_employments() #Creates people/companies/employments
    assert len(Person.get_current_employees_in_companies([6792948])) == 1
    assert len(Person.get_past_employees_in_companies([6792948])) == 1
    Employment.edit({
		"company_id": 6792948,
		"person_id": 3676157,
		"start_date": "2017-05-01 00:00:00",
		"end_date": "2023-05-01 00:00:00"
	})
    assert len(Person.get_current_employees_in_companies([6792948])) == 0
    assert len(Person.get_past_employees_in_companies([6792948])) == 2
    Employment.edit({
		"company_id": 703504,
		"person_id": 360027,
		"employment_title": "Awesome Sauces",
		"start_date": "2012-05-01 00:00:00",
	})
    assert Person.get_past_employees_in_companies([703504])[0]['employment_title'] == "Awesome Sauces"
