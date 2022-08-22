from typedb.client import *

studentAnswer = {1:'22', 2:'2'}

for i in range(len(studentAnswer)):
    #print(len(studentAnswer))
    pass
mappingLanguage = {
    'francais': ['francais','français','fr','france','french'],
    'english': ['english','anglais','en','england', 'eng']
}

slot_value = 'english'

#print(mappingLanguage.items())

#if str(slot_value) in str(mappingLanguage.items()):
    #print('ok')

def queryExplicationDB(questionNumber, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session("IALP", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa values, has identifier $i, has explication-text $q; {$i = "values'
                query += f'{questionNumber}{langDim}'
                query += '";}; get $q;'
                print(query)
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return str(res)

def queryQuestionNamePointDB(questionNumber, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session("rasaExam", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x (values: $v,weight: $w,category: $c) isa question, has identifier $i, has id-weight $q; {$i = "question'
                query += f'{questionNumber}{langDim}'
                query += '";}; get $q;'
                print(query)
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return str(res)

def queryQuestionPointDB(questionNumber, langDim):

    weightID = queryQuestionNamePointDB(questionNumber, langDim)

    with TypeDB.core_client("localhost:1729") as client:
        with client.session("rasaExam", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa weight, has identifier $i, has point $q; {$i = "'
                query += f'{weightID}'
                query += '";}; get $q;'
                print(query)
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return int(res)

def queryProposalDB(questionNumber, lang, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session("rasaExam", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x (values: $v,weight: $w,category: $c) isa question, has identifier $i, has id-weight $q; {$i = "question'
                query += f'{questionNumber}{langDim}'
                query += '";}; get $q;'
                print(query)
                answer_iterator = read_transaction.query().match(query)
                res = []
                for answer in answer_iterator:
                    res.append(answer.get('q').get_value())
                    print(res[0])
                return res

print(queryExplicationDB('2','f'))


def test1():
    with TypeDB.core_client("localhost:1729") as client:
        with client.session("rasaExam", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa category, has identifier $i, has question-type $a; {$i = "category'
                query += f'1'
                query += '";}; get $a;'
                print(query)
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('a').get_value()
                    print(res)


def test2():
    with TypeDB.core_client("localhost:1729") as client:
        with client.session("rasaExam", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                answer_iterator = read_transaction.query().match("match $x isa question, has identifier $i; get $i;")

                for answer in answer_iterator:
                    #object_methods = [method_name for method_name in dir(object) if callable(getattr(object, method_name))]
                    #print(object_methods)
                    print(answer.get('i').get_value())
                    print(vars(answer.get('i')))
                    print(type(answer.get('i')))