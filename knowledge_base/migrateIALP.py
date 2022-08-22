#from typedb.client import TypeDB, SessionType, TransactionType
from typedb.client import *
import csv

def build_banking_graph(inputs):
        with TypeDB.core_client("localhost:1729") as client:
            with client.session('IALP', SessionType.DATA) as session:
                for input in inputs:
                    print("Loading from [" + input["data_path"] + "] into Grakn ...")
                    load_data_into_grakn(input, session)


def load_data_into_grakn(input, session):
    items = parse_data_to_dictionaries(input)

    for item in items:
        with session.transaction(TransactionType.WRITE) as transaction:
            graql_insert_query = input["template"](item)
            transaction.query().insert(graql_insert_query)
            transaction.commit()

    print(f"Inserted {str(len(items))} items from [{input['data_path']}] into Grakn.")


def values_template(values):
    graql_insert_query = "insert $values isa values"
    graql_insert_query += ', has identifier "' + values["identifier"] + '"'
    graql_insert_query += ', has false-answer-text "' + values["false-answer-text"] + '"'
    graql_insert_query += ', has question-text "' + values["question-text"] + '"'
    graql_insert_query += ', has answer-text "' + values["answer-text"] + '"'
    graql_insert_query += ', has language "' + values["language"] + '"'
    graql_insert_query += ";"
    return graql_insert_query

def weight_template(weight):
    graql_insert_query = "insert $weight isa weight"
    graql_insert_query += ', has identifier "' + weight["identifier"] + '"'
    graql_insert_query += ', has point ' + weight["point"]
    graql_insert_query += ', has complexity ' + weight["complexity"]
    graql_insert_query += ', has importance ' + weight["importance"] 
    graql_insert_query += ";"
    print(graql_insert_query)
    return graql_insert_query

def category_template(category):
    graql_insert_query = "insert $category isa category"
    graql_insert_query += ', has identifier "' + category["identifier"] + '"'
    graql_insert_query += ', has question-type "' + category["question-type"] + '"'
    graql_insert_query += ', has theme "' + category["theme"] + '"'
    graql_insert_query += ";"
    return graql_insert_query


def question_template(question):
    graql_insert_query = (
        'match $values isa values, has identifier "' + question["id-values"] + '";'
    )
    graql_insert_query += (
        ' $weight isa weight, has identifier "' + question["id-weight"] + '";'
    )
    graql_insert_query += (
        ' $category isa category, has identifier "' + question["id-category"] + '";'
    )
    graql_insert_query += " insert $question(values: $values, weight: $weight, category: $category) isa question; "
    graql_insert_query += '$question has identifier "' + question["identifier"] + '";'
    graql_insert_query += '$question has id-values "' + question["id-values"] + '";'
    graql_insert_query += '$question has id-weight "' + question["id-weight"] + '";'
    graql_insert_query += '$question has id-category "' + question["id-category"] + '";'

    return graql_insert_query


def parse_data_to_dictionaries(input):
    items = []
    with open(input["data_path"] + ".csv") as data:  # 1
        for row in csv.DictReader(data, skipinitialspace=True):
            item = {key: value for key, value in row.items()}
            items.append(item)  # 2
    return items


if __name__ == "__main__":
    inputs = [
        {"data_path": "./IALP/weight", "template": weight_template},
        {"data_path": "./IALP/category", "template": category_template},
        {"data_path": "./IALP/values", "template": values_template},
        {"data_path": "./IALP/question", "template": question_template,},
    ]

    build_banking_graph(inputs)
