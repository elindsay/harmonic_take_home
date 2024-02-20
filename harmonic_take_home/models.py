import time
import datetime
from neomodel import db, StructuredNode, StructuredRel, IntegerProperty, StringProperty, DateTimeProperty, BooleanProperty, RelationshipTo, UniqueProperty

class Acquisition(StructuredRel):
    parent_company_id = IntegerProperty(required=True)
    acquired_company_id = IntegerProperty(required=True)
    merged_into_parent_company = BooleanProperty(required=True)

    @classmethod
    def bulk_create(cls, company_acquisitions_data):
        #Please Note -- Person and Company have to be created for this to work
        query = """
        UNWIND $batch AS data
        MATCH (p:Company {company_id: data.parent_company_id})
        MATCH (c:Company {company_id: data.acquired_company_id})
        MERGE (p)-[a:ACQUIRED]->(c)
        SET a.merged_into_parent_company = data.merged_into_parent_company
        """
        print(db.cypher_query(query, params={"batch": company_acquisitions_data}))

class Company(StructuredNode):
    company_name = StringProperty(unique_index=True, required=True)
    headcount = IntegerProperty(required=True)
    company_id = IntegerProperty(unique_index=True, required=True)
    acquired = RelationshipTo('Company', 'ACQUIRED', model=Acquisition)

    @classmethod
    def bulk_create(cls, companies_data):
        query = """
        UNWIND $batch AS data
        CREATE (p:Company {company_name: data.company_name, headcount: data.headcount, company_id: data.company_id})
        """
        db.cypher_query(query, params={"batch": companies_data})

    def to_dict(self):
        self_dict = {
            'company_id': self.company_id,
            'company_name': self.company_name,
            'headcount': self.headcount
        }
        return self_dict

    def get_employees(self):
        query = """
        MATCH (company:Company {company_id: $company_id})
        MATCH (company)<-[e:EMPLOYED_AT]-(person:Person)
        RETURN person, e.employment_title AS employment_title
        """
        results, _ = db.cypher_query(query, params={"company_id": self.company_id})
        return [{'person': Person.inflate(row[0]), 'employment_title': row[1]} for row in results]

    def get_acquired_companies(self):
        query = """
        MATCH (parent:Company {company_id: $company_id})
        MATCH (parent)-[:ACQUIRED]->(acquired:Company)
        RETURN acquired
        """
        results, _ = db.cypher_query(query, params={"company_id": self.company_id})
        return [Company.inflate(row[0]) for row in results]

    def get_all_descendant_companies(self):
        query = """
        MATCH (parent:Company {company_id: $company_id})
        MATCH (parent)-[:ACQUIRED*1..]->(acquired:Company)
        RETURN DISTINCT acquired
        """
        results, _ = db.cypher_query(query, params={"company_id": self.company_id})
        return [Company.inflate(row[0]) for row in results]

    def get_parent_company(self):
        #Note -- we assume there is only one parent company, however,
        #there is no limitation in the codebase that requries this
        query = """
        MATCH (child:Company {company_id: $company_id})
        MATCH (child)<-[:ACQUIRED]-(parent:Company)
        RETURN parent
        """
        results, _ = db.cypher_query(query, params={"company_id": self.company_id})
        # We return the first company, instaad of a list of companies
        # Based on assumption of a maximum of one parent 
        return Company.inflate(results[0][0]) if results else None

    def get_all_ancestor_companies(self):
        query = """
        MATCH (child:Company {company_id: $company_id})
        MATCH (child)<-[:ACQUIRED*1..]-(ancestor:Company)
        RETURN ancestor
        """
        results, _ = db.cypher_query(query, params={"company_id": self.company_id})
        return [Company.inflate(row[0]) for row in results]


def to_timestamp(date_str):
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    timestamp = int(time.mktime(dt.timetuple()))
    return timestamp

class Employment(StructuredRel):
    employment_title = StringProperty(required=True)
    start_date = DateTimeProperty()
    end_date = DateTimeProperty()

    @classmethod
    def bulk_create(cls, person_employments_data):
        #Need to clean date strings for neo4j library
        for pe in person_employments_data:
            if 'start_date' in pe and pe['start_date']:
                pe['start_date'] = to_timestamp(pe['start_date'])
            if 'end_date' in pe and pe['end_date']:
                pe['end_date'] = to_timestamp(pe['end_date'])

        #Please Note -- Person and Company have to be created for this to work
        query = """
        UNWIND $batch AS data
        MATCH (p:Person {person_id: data.person_id})
        MATCH (c:Company {company_id: data.company_id})
        MERGE (p)-[e:EMPLOYED_AT]->(c)
        SET e.employment_title = data.employment_title, e.start_date = data.start_date, e.end_date = data.end_date
        """
        db.cypher_query(query, params={"batch": person_employments_data})

    @classmethod
    def edit(cls, person_employment_data):
        print("two")
        person_id = person_employment_data['person_id']
        company_id = person_employment_data['company_id']
        start_date = to_timestamp(person_employment_data['start_date'])

        query = """
        MATCH (p:Person)-[e:EMPLOYED_AT]->(c:Company) 
        WHERE p.person_id=$person_id AND c.company_id=$company_id AND e.start_date=$start_date
        RETURN e
        """
        params = {
            'person_id': person_id,
            'company_id': company_id,
            'start_date': start_date 
            }
        results, _ = db.cypher_query(query, params=params)

        print("three")
        if results:
            employment_rel = Employment.inflate(results[0][0])
            if person_employment_data.get('employment_title'):
                employment_rel.employment_title = person_employment_data["employment_title"]
            if person_employment_data.get('end_date'):
                employment_rel.end_date = datetime.datetime.strptime(person_employment_data['end_date'],"%Y-%m-%d %H:%M:%S")
            print("four")
            return employment_rel.save()

class Person(StructuredNode):
    person_id = IntegerProperty(required=True)
    employed_at = RelationshipTo('Company', 'EMPLOYED_AT', model=Employment)

    @classmethod
    def bulk_create(cls, person_employments_data):
        person_ids = list(set(map(lambda ped: ped["person_id"], person_employments_data)))
        query = """
        UNWIND $batch AS person_id
        CREATE (p:Person {
            person_id: person_id
        })
        """
        db.cypher_query(query, params={"batch": person_ids})

    @classmethod
    def get_employees_in_companies(cls, company_ids):
        query = """
        MATCH (p:Person)-[e:EMPLOYED_AT]->(c:Company)
        WHERE c.company_id IN $company_ids
        RETURN p, c.company_name AS company_name, e.employment_title AS employment_title
        """
        results, _ = db.cypher_query(query, params={"company_ids": company_ids})
        return [{'person': Person.inflate(row[0]), 'company_name': row[1], 'employment_title': row[2]} for row in results]

    @classmethod
    def get_current_employees_in_companies(cls, company_ids):
        query = """
        MATCH (p:Person)-[e:EMPLOYED_AT]->(c:Company)
        WHERE c.company_id IN $company_ids AND e.end_date IS NULL
        RETURN p, c.company_name AS company_name, e.employment_title AS employment_title
        """
        results, _ = db.cypher_query(query, params={"company_ids": company_ids})
        return [{'person': Person.inflate(row[0]), 'company_name': row[1], 'employment_title': row[2]} for row in results]

    @classmethod
    def get_past_employees_in_companies(cls, company_ids):
        query = """
        MATCH (person:Person)-[employment:EMPLOYED_AT]->(company:Company)
        WHERE company.company_id IN $company_ids AND employment.end_date IS NOT NULL
        RETURN person, company.company_name AS company_name, employment.employment_title AS employment_title
        """
        results, _ = db.cypher_query(query, params={"company_ids": company_ids})
        return [{'person': Person.inflate(row[0]), 'company_name': row[1], 'employment_title': row[2]} for row in results]
