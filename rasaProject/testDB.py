from typedb.client import *
id_exam = 'IALP'
studentAnswer = {1:'22', 2:'2'}


for i in range(len(studentAnswer)):
    #print(len(studentAnswer))
    pass
mappingLanguage = {
    'francais': ['francais','français','fr','france','french'],
    'english': ['english','anglais','en','england', 'eng']
}

slot_value = 'english'
language = 'english'
langDim = 'e'

#print(mappingLanguage.items())

#if str(slot_value) in str(mappingLanguage.items()):
    #print('ok')

def queryAllDatabase():
    exams = []
    with TypeDB.core_client("localhost:1729") as client:
        tempExams = client.databases().all()
        for exam in tempExams:
                    exams.append(str(exam))
                    print(exam)
        return exams

import random

def getRandomInList(listed):
    return listed[random.randint(0,(len(listed)-1))]

def queryAllValues():
    with TypeDB.core_client("localhost:1729") as client:
        with client.session("IALP", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa values, has identifier $i; get $i;'
                answer_iterator = read_transaction.query().match(query)
                res = []
                for answer in answer_iterator:
                    res.append(answer.get('i').get_value())
                
                return res

def getOnlyNumberValues(value):
    return ''.join(filter(str.isdigit, value))
    
def queryExplicationDB(questionNumber, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session("IALP", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa values, has identifier $i, has explication-text $q; {$i = "values'
                query += f'{questionNumber}{langDim}'
                query += '";}; get $q;'
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return str(res)

def queryQuestionNamePointDB(questionNumber, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x (values: $v,weight: $w,category: $c) isa question, has identifier $i, has id-weight $q; {$i = "question'
                query += f'{questionNumber}{langDim}'
                query += '";}; get $q;'
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return str(res)

def queryQuestionComplexityDB(questionNumber, langDim):

    weightID = queryQuestionNamePointDB(questionNumber, langDim)

    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa weight, has identifier $i, has complexity $q; {$i = "'
                query += f'{weightID}'
                query += '";}; get $q;'
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return int(res)

def queryQuestionThemeDB(questionNumber, langDim):

    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa category, has identifier $i, has theme $q; {$i = "category'
                query += f'{questionNumber}{langDim}'
                query += '";}; get $q;'
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return res

def queryAllNumberDB(lang):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa values, has identifier $q, has language $i; {$i = "'
                query += f'{lang}'
                query += '";}; get $q;'
                answer_iterator = read_transaction.query().match(query)
                res = []
                for answer in answer_iterator:
                    temp = answer.get('q').get_value()
                    res.append(''.join(filter(str.isdigit, temp)))
                return res

def randomQuestion():
    random = getOnlyNumberValues(getRandomInList(queryAllValues()))
    while random in askedQuestions:
        random = getOnlyNumberValues(getRandomInList(queryAllValues()))
    askedQuestions.append(str(random))
    return str(random)

nestedDataDict = {}

def createNestedDataDict(lang, langDim):
    allNumber = queryAllNumberDB(lang)
    for i in allNumber:
        nestedDataDict[i] = {
            'complexity': queryQuestionComplexityDB(i, langDim),
            'theme': queryQuestionThemeDB(i, langDim)
        }

createNestedDataDict('english', 'e')
#print(nestedDataDict)

currentTheme = 'programming-language'
currentComplexity = 2
lastAnswerResult = True
askedQuestions = ['3', '2', '1', '10', '11', '12', '9', '7', '8']

def getQuestionPerfectMatch():
    res = []
    for i in nestedDataDict:
        if i not in askedQuestions:
            if lastAnswerResult == True:
                if nestedDataDict[i]['complexity'] >= currentComplexity and nestedDataDict[i]['theme'] == currentTheme:
                    tempDict = {i: nestedDataDict[i]}
                    res.append(tempDict)
            elif lastAnswerResult == False:
                if nestedDataDict[i]['complexity'] <= currentComplexity and nestedDataDict[i]['theme'] == currentTheme:
                    tempDict = {i: nestedDataDict[i]}
                    res.append(tempDict)
    return res

def getQuestionWorstMatch():
    res = []
    for i in nestedDataDict:
        if i not in askedQuestions:
            if lastAnswerResult == True:
                if nestedDataDict[i]['complexity'] >= currentComplexity:
                    tempDict = {i: nestedDataDict[i]}
                    res.append(tempDict)
            elif lastAnswerResult == False:
                if nestedDataDict[i]['complexity'] <= currentComplexity:
                    tempDict = {i: nestedDataDict[i]}
                    res.append(tempDict)
    return res

def getBestMatch(arrayNestedDict):
    tempForRandom = []
    complex = None
    for i in arrayNestedDict:
        for y in i:
            if complex == None:
                complex = i[y]['complexity']
                tempForRandom.append(i)
            elif i[y]['complexity'] > complex:
                tempForRandom = []
                tempForRandom.append(i)
                complex = i[y]['complexity']
            elif i[y]['complexity'] == complex:
                tempForRandom.append(i)
    rand = random.randint(0, len(tempForRandom)-1)
    return tempForRandom[rand]

def getNextQuestionNumber():
    perfectMatch = getQuestionPerfectMatch()
    if perfectMatch == []:
        perfectMatch = getQuestionWorstMatch()
    if perfectMatch == []:
        nextNumber = randomQuestion()
        nextComplexity = queryQuestionComplexityDB(nextNumber, langDim)
        nextTheme = queryQuestionThemeDB(nextNumber, langDim)
        return nextNumber, nextComplexity, nextTheme
    dictBestMatch = getBestMatch(perfectMatch)
    for i in dictBestMatch:
        return i, dictBestMatch[i]['complexity'], dictBestMatch[i]['theme']
        
#print(getNextQuestionNumber())

#print(queryAllNumberDB('english'))

def queryProposalDB(questionNumber, lang, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session("rasaExam", SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x (values: $v,weight: $w,category: $c) isa question, has identifier $i, has id-weight $q; {$i = "question'
                query += f'{questionNumber}{langDim}'
                query += '";}; get $q;'
                answer_iterator = read_transaction.query().match(query)
                res = []
                for answer in answer_iterator:
                    res.append(answer.get('q').get_value())
                return res

def queryImagesDB(questionNumber, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa values, has identifier $i, has images $q; {$i = "values'
                query += f'{questionNumber}{langDim}'
                query += '";}; get $q;'
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return str(res)

questionNumber = '18'
languageDim = 'f'
#print(queryQuestionThemeDB(questionNumber, languageDim))
print(queryImagesDB(questionNumber, languageDim))