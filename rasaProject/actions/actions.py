# This files contains your custom actions which can be used to run
# custom Python code.

# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from glob import glob
import random
from typing import Any, Text, Dict, List, Union
import arrow
import dateparser
from datetime import date
import time    
#from matplotlib.pyplot import arrow
from schemma import schema
from graph_database import GraphDatabase
from typedb.client import *
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType
import pymysql.cursors

realAnswers = {}
answers = {}
idQuestions = {}
starting_time = ''
ending_time = ''
grade = 0
id_student = '0'
language = 'english'
languageDim = 'e'
id_exam = ''
exams = []
askedQuestions = []
currentComplexity = 2
currentTheme = ''
currentQuestionNumber = 0
nextQuestionNumber = 0
nestedDataDict = {}
lastAnswerResult = True
mediumComplexity = 2
instruction = {
    #en
    'TF': 'Please, answer this question with a true or false statement.',
    'MCQ': '--> Multiple choice question. Please, answer with the number of the best answer.',
    #fr
    'VF': "S'il vous plait, répondez par vrai ou faux.",
    'QCM': "--> Question à choix multiple. S'il vous plait, répondez avec le numéro de la meilleure réponse."

}

mapping = {
    1: ['first', 'one', '1', 'premier', 'un', 'premiere', 'première', 'une'],
    2: ['second', 'two', '2', 'deux', 'deuxieme', 'deuxième'],
    3: ['third', 'three', '3', 'trois', 'troisieme', 'troisième'],
    4: ['forth', 'four', '4', 'quatre', 'quatrieme', 'quatrième'],
    5: ['fifth', 'five', '5', 'cinq', 'cinquieme', 'cinquième'],
    6: ['sixth', 'six', '6', 'six', 'sixieme', 'sixième'],
    0: ['last', 'lattest', 'late', 'dernier', 'derniere', 'dernière']       
}

mappingTF = {
    'english': {
        'True': 'True',
        'False': 'False'
    },
    'francais': {
        'True': 'Vrai',
        'False': 'Faux'
    }
}

mappingLanguage = {
    'francais': ['francais','français','fr','france','french'],
    'english': ['english','anglais','en','england', 'eng']
}


mappingLanguageDim = {
    'e': 'english',
    'f': 'francais'
}

utterMultilanguage = {
    'rememberAnswer': {
        'english': 'Thank you for you answer',
        'francais': 'Merci pour votre réponse'
    },
    'badAnswer': {
        'english': "Your answer isn't recognized. Please, reformulate your answer.",
        'francais': "Votre réponse n'a pas pu être reconnu. S'il vous plait, reformulez votre réponse."
    },
    'grade': {
        'english': 'Your grade is',
        'francais': 'Votre note est'
    },
    'end': {
        'english': 'The exam is now finisehd.',
        'francais': "L'examen est maintenant terminé."
    },
    'explanation': {
        'english': 'You have answered all the questions. Do you want to see the explanation of your incorrect answers ?',
        'francais': 'Vous avez répondu à toutes les questions. Est-ce que vous souhaitez avoir des explications concernant vos réponses incorrectes ?'
    },
    'eplanationQuestion': {
        'english': 'For the question',
        'francais': 'Pour la question'
    },
    'eplanationAnswer': {
        'english': 'You said the answer was',
        'francais': 'Vous avez dit que la réponse était'
    },
    'eplanationRealAnswer': {
        'english': 'but it',
        'francais': "mais c'est"
    },
    'eplanationExplanation': {
        'english': 'Reason',
        'francais': 'Raison'
    },
    'eplanationAllCorrect': {
        'english': 'All your answers were correct',
        'francais': 'Toutes vos réponses étaient correctes'
    },
    'listExam': {
        'english': "Here's the list of all available exam",
        'francais': 'Voici la liste de tous les examens disponibles'
    }
}



def queryMySql(query):
    # Connect to the database
    connection = pymysql.connect(host='127.0.0.1',
                             #port=8889,
                             user='pma',
                             #password='admin',
                             database='examRasaBot',
                             cursorclass=pymysql.cursors.DictCursor)
    with connection:
        with connection.cursor() as cursor:
            # Create a new record
            cursor.execute(query)

        # connection is not autocommit by default. So you must commit to save
        # your changes.
        connection.commit()

#https://note.nkmk.me/en/python-dict-get-key-from-value/
def get_key_from_value(d, val):
    keys = [k for k, v in d.items() if val in v]
    if keys:
        return keys[0]
    return None

#https://appdividend.com/2022/03/15/how-to-check-if-string-is-integer-in-python/#:~:text=To%20check%20if%20a%20string,string%20are%20digits%20or%20not.
def checkInt(str):
    try:
        int(str)
        return True
    except ValueError:
        return False

def getGrade(studentAnswer, answer, langDim):
    explication = {}
    tempGrade = 0
    totalPoint = 0
    print(f'answer: {answer}')
    for n in studentAnswer:
        point = queryQuestionPointDB(n, languageDim)
        totalPoint += point
        if str(studentAnswer[n]).lower() == str(answer[n]).lower():
            tempGrade += point
        else:
            explication[n] = queryExplicationDB(str(n), langDim)
            """
    for n in range(len(studentAnswer)):
        point = queryQuestionPointDB((n), languageDim)
        totalPoint += point
        if str(studentAnswer[n]).lower() == str(answer[n]).lower():
            tempGrade += point
        else:
            explication[n+1] = queryExplicationDB(str(n+1), langDim)
            """
        print(f'studentAnswer: {studentAnswer[n]}')
        print(f'answer: {answer[n]}')
        print(f'n: {n}')
        print(f'point: {point}')
        print(f'totalPoint: {totalPoint}')
        print(f'tempGrade: {tempGrade}')
    res = ((tempGrade/totalPoint)*5)+1
    return res, explication

def getRandomInList(listed):
    return listed[random.randint(0,(len(listed)-1))]

def getMediumComplexity():
    min = None
    max = None
    res = None
    for index in nestedDataDict:
        if min == None or nestedDataDict[index]['complexity'] < min:
            min = nestedDataDict[index]['complexity']
        if max == None or nestedDataDict[index]['complexity'] > max:
            max = nestedDataDict[index]['complexity']
    res = (min+max)/2
    return int(res)

def queryAllValues():
    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa values, has identifier $i; get $i;'
                answer_iterator = read_transaction.query().match(query)
                res = []
                for answer in answer_iterator:
                    res.append(answer.get('i').get_value())
                
                return res

def getOnlyNumberValues(value):
    return ''.join(filter(str.isdigit, value))

def randomQuestion():
    random = getOnlyNumberValues(getRandomInList(queryAllValues()))
    while random in askedQuestions:
        random = getOnlyNumberValues(getRandomInList(queryAllValues()))
    return str(random)

def randomQuestionComplexity2():
    random = getOnlyNumberValues(getRandomInList(queryAllValues()))
    while nestedDataDict[str(random)]['complexity'] != mediumComplexity:
        random = getOnlyNumberValues(getRandomInList(queryAllValues()))
    return str(random)

def getQuestionPerfectMatch():
    print(nestedDataDict)
    res = []
    for i in nestedDataDict:
        if str(i) not in askedQuestions:
            if lastAnswerResult == True:
                print(i)
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
        if str(i) not in askedQuestions:
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
    if lastAnswerResult == True:
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
    else:
        for i in arrayNestedDict:
            for y in i:
                if complex == None:
                    complex = i[y]['complexity']
                    tempForRandom.append(i)
                elif i[y]['complexity'] < complex:
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
        print('not perfect --> worst')
        perfectMatch = getQuestionWorstMatch()
    if perfectMatch == []:
        print('not worst --> random')
        nextNumber = randomQuestion()
        nextComplexity = queryQuestionComplexityDB(nextNumber, languageDim)
        nextTheme = queryQuestionThemeDB(nextNumber, languageDim)
        return nextNumber, nextComplexity, nextTheme
    dictBestMatch = getBestMatch(perfectMatch)
    for i in dictBestMatch:
        return i, dictBestMatch[i]['complexity'], dictBestMatch[i]['theme']

class ActionTestDB(Action):
    def name(self) -> Text:
        return "action_testDB"
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        with TypeDB.core_client("localhost:1729") as client:
            with client.session(id_exam, SessionType.DATA) as session:
                with session.transaction(TransactionType.READ) as read_transaction:
                    answer_iterator = read_transaction.query().match("match $x isa question, has identifier $i; get $i;")
                    dispatcher.utter_message(text=f'Here are a list of all avalaible questions:')
                    for answer in answer_iterator:
                        bank = answer.get('i').get_value()
                        dispatcher.utter_message(text=f'{bank}')

class classListExam(Action):
    def name(self) -> Text:
        return "action_list_exam"
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text=f"{utterMultilanguage['listExam'][language]}")

        for exam in exams:
            dispatcher.utter_message(text=f"{exam}")
        

def queryAllDatabase():
    res = []
    with TypeDB.core_client("localhost:1729") as client:
        tempRes = client.databases().all()
        for i in tempRes:
                    res.append(str(i))
        return res

exams = queryAllDatabase()

def queryExplicationDB(questionNumber, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa values, has identifier $i, has explication-text $q; {$i = "values'
                query += f'{questionNumber}{langDim}'
                query += '";}; get $q;'
                print(query)
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return str(res)

def queryProposalDB(questionNumber, lang, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa values, has identifier $i, has proposal-answer-text $q, has language $l; {$i = "values'
                query += f'{questionNumber}{langDim}"; $l = "{lang}'
                query += '";}; get $q;'
                answer_iterator = read_transaction.query().match(query)
                res = []
                for answer in answer_iterator:
                    res.append(answer.get('q').get_value())
                return res


def queryQuestionDB(questionNumber, lang, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa values, has identifier $i, has question-text $q, has language $l; {$i = "values'
                query += f'{questionNumber}{langDim}"; $l = "{lang}'
                query += '";}; get $q;'
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return res

def queryAnswerDB(answerNumber, lang, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa values, has identifier $i, has answer-text $a, has language $l; {$i = "values'
                query += f'{answerNumber}{langDim}"; $l = "{lang}'
                query += '";}; get $a;'
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('a').get_value()
                    return res

def queryQuestionTypeDB(answerNumber, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa category, has identifier $i, has question-type $a; {$i = "category'
                query += f'{answerNumber}{langDim}'
                query += '";}; get $a;'
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('a').get_value()
                    return res

def queryQuestionNamePointDB(questionNumber, langDim):
    with TypeDB.core_client("localhost:1729") as client:
        with client.session(id_exam, SessionType.DATA) as session:
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
        with client.session(id_exam, SessionType.DATA) as session:
            with session.transaction(TransactionType.READ) as read_transaction:
                query = 'match $x isa weight, has identifier $i, has point $q; {$i = "'
                query += f'{weightID}'
                query += '";}; get $q;'
                print(query)
                answer_iterator = read_transaction.query().match(query)
                for answer in answer_iterator:
                    res = answer.get('q').get_value()
                    return int(res)

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
                print(query)
                answer_iterator = read_transaction.query().match(query)
                res = []
                for answer in answer_iterator:
                    temp = answer.get('q').get_value()
                    res.append(''.join(filter(str.isdigit, temp)))
                return res

def createNestedDataDict(lang, langDim):
    allNumber = queryAllNumberDB(lang)
    for i in allNumber:
        nestedDataDict[i] = {
            'complexity': queryQuestionComplexityDB(i, langDim),
            'theme': queryQuestionThemeDB(i, langDim)
        }

class ValidationExamForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_exam_form"
    
    async def extract_answer1(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if tracker.slots['requested_slot'] == 'answer1':
            currentIntent = tracker.latest_message['intent'].get('name')

            tempSlot = ''

            if currentIntent == 'affirm':
                tempSlot = True
            elif currentIntent == 'deny':
                tempSlot = False
            elif currentIntent == 'resolve_entity':
                tempSlot = next(tracker.get_latest_entity_values('mention'), None)

            return { 'answer1': tempSlot }
    
    async def extract_answer2(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if tracker.slots['requested_slot'] == 'answer2':
            currentIntent = tracker.latest_message['intent'].get('name')

            tempSlot = ''

            if currentIntent == 'affirm':
                tempSlot = True
            elif currentIntent == 'deny':
                tempSlot = False
            elif currentIntent == 'resolve_entity':
                tempSlot = next(tracker.get_latest_entity_values('mention'), None)

            return { 'answer2': tempSlot }

    async def extract_answer3(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if tracker.slots['requested_slot'] == 'answer3':
            currentIntent = tracker.latest_message['intent'].get('name')

            tempSlot = ''

            if currentIntent == 'affirm':
                tempSlot = True
            elif currentIntent == 'deny':
                tempSlot = False
            elif currentIntent == 'resolve_entity':
                tempSlot = next(tracker.get_latest_entity_values('mention'), None)

            return { 'answer3': tempSlot }

    async def extract_answer4(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if tracker.slots['requested_slot'] == 'answer4':
            currentIntent = tracker.latest_message['intent'].get('name')

            tempSlot = ''

            if currentIntent == 'affirm':
                tempSlot = True
            elif currentIntent == 'deny':
                tempSlot = False
            elif currentIntent == 'resolve_entity':
                tempSlot = next(tracker.get_latest_entity_values('mention'), None)

            return { 'answer4': tempSlot }

    async def extract_answer5(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if tracker.slots['requested_slot'] == 'answer5':
            currentIntent = tracker.latest_message['intent'].get('name')

            tempSlot = ''

            if currentIntent == 'affirm':
                tempSlot = True
            elif currentIntent == 'deny':
                tempSlot = False
            elif currentIntent == 'resolve_entity':
                tempSlot = next(tracker.get_latest_entity_values('mention'), None)

            return { 'answer5': tempSlot }

    async def extract_wanna_explanation(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if tracker.slots['requested_slot'] == 'wanna_explanation':
            currentIntent = tracker.latest_message['intent'].get('name')

            tempSlot = ''

            if currentIntent == 'affirm':
                tempSlot = True
            elif currentIntent == 'deny':
                tempSlot = False
            else: 
                pass

            return { 'wanna_explanation': tempSlot }
    
    def validate_id_exam(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if slot_value != None and str(slot_value).upper() in exams:
            global id_exam
            id_exam = slot_value
            dispatcher.utter_message(text=f'Thank you for giving your exam id: {slot_value}.')
            return { 'id_exam': slot_value }
        else:
            dispatcher.utter_message(text=f"Your anser isn't recognized. Please verify your the name of your exam.")
            dispatcher.utter_message(text=f"If you are in trouble finding the correct id, you can ask me the list of all available exam.")

            return { 'id_exam': None }

    def validate_language(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if slot_value != None:
            if str(slot_value) in str(mappingLanguage.items()):
                dispatcher.utter_message(text=f'Thank you for giving us your prefered language. The exam is now starting in : {slot_value}. ')
                global language
                language = get_key_from_value(mappingLanguage, str(slot_value).lower())
                global languageDim
                languageDim = get_key_from_value(mappingLanguageDim, language)
                return { 'language': slot_value }
            else:
                dispatcher.utter_message(text=f'Your anser isnt recognized. Please refer your id with only the number.')
                return { 'language': None }
        else:
            dispatcher.utter_message(text=f'Your anser isnt recognized. Please refer your id with only the number.')
            return { 'language': None }

    def validate_id_student(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if slot_value != None:
            id = slot_value
            if '-' in id:
                idStrip = id.split('-')
                id = ''.join(idStrip)
            id = str(id)
            global id_student
            id_student = id
            if checkInt(id) == True:
                dispatcher.utter_message(text=f'Thank you for giving your id: {slot_value}.')
                return { 'id_student': id }
            else: 
                dispatcher.utter_message(text=f'Your anser isnt recognized. Please refer your id with only the number.')
                return { 'id_student': None }
        else:
            dispatcher.utter_message(text=f'Your anser isnt recognized. Please refer your id with only the number.')
            return { 'id_student': None }

    def validate_answer1(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if slot_value != None:
            proposal = queryProposalDB(askedQuestions[-1], language, languageDim)
            proposalArray = proposal[0].split('*')

            currentIntent = tracker.latest_message['intent'].get('name')
            answerTemp = ''
            answer = ''
            if currentIntent == 'affirm':
                answer = mappingTF[language][str(slot_value)]
            elif currentIntent == 'deny':
                answer = mappingTF[language][str(slot_value)]
            elif currentIntent == 'resolve_entity':
                answerTemp = get_key_from_value(mapping, str(slot_value).lower())
                answer = proposalArray[answerTemp-1]
            elif currentIntent == 'skip_exam':
                answer = 'Na'
            global lastAnswerResult
            if str(answer).lower() == str(realAnswers[currentQuestionNumber]).lower():
                lastAnswerResult = True
            else: 
                lastAnswerResult = False

            dispatcher.utter_message(text=f"{utterMultilanguage['rememberAnswer'][language]}: {answer}.")
            answers[int(askedQuestions[-1])] = (str(answer))
            return { 'answer1': answer }
        else:
            dispatcher.utter_message(text=f"{utterMultilanguage['badAnswer'][language]}.")
            return { 'answer1': None }
        
    def validate_answer2(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if slot_value != None:
            proposal = queryProposalDB(askedQuestions[-1], language, languageDim)
            proposalArray = proposal[0].split('*')

            currentIntent = tracker.latest_message['intent'].get('name')
            answerTemp = ''
            answer = ''
            if currentIntent == 'affirm':
                answer = mappingTF[language][str(slot_value)]
            elif currentIntent == 'deny':
                answer = mappingTF[language][str(slot_value)]
            elif currentIntent == 'resolve_entity':
                answerTemp = get_key_from_value(mapping, str(slot_value).lower())
                answer = proposalArray[answerTemp-1]
            elif currentIntent == 'skip_exam':
                answer = 'Na'
            global lastAnswerResult
            if str(answer).lower() == str(realAnswers[currentQuestionNumber]).lower():
                lastAnswerResult = True
            else: 
                lastAnswerResult = False

            dispatcher.utter_message(text=f"{utterMultilanguage['rememberAnswer'][language]}: {answer}")
            answers[int(askedQuestions[-1])] = (str(answer))
            

            return { 'answer2': answer }
        else:
            dispatcher.utter_message(text=f"{utterMultilanguage['badAnswer'][language]}.")
            return { 'answer2': None }

    def validate_answer3(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if slot_value != None:
            proposal = queryProposalDB(askedQuestions[-1], language, languageDim)
            proposalArray = proposal[0].split('*')

            currentIntent = tracker.latest_message['intent'].get('name')
            answerTemp = ''
            answer = ''
            if currentIntent == 'affirm':
                answer = mappingTF[language][str(slot_value)]
            elif currentIntent == 'deny':
                answer = mappingTF[language][str(slot_value)]
            elif currentIntent == 'resolve_entity':
                answerTemp = get_key_from_value(mapping, str(slot_value).lower())
                answer = proposalArray[answerTemp-1]
            elif currentIntent == 'skip_exam':
                answer = 'Na'
            global lastAnswerResult
            if str(answer).lower() == str(realAnswers[currentQuestionNumber]).lower():
                lastAnswerResult = True
            else: 
                lastAnswerResult = False

            dispatcher.utter_message(text=f"{utterMultilanguage['rememberAnswer'][language]}: {answer}")
            answers[int(askedQuestions[-1])] = (str(answer))

            return { 'answer3': answer }
        else:
            dispatcher.utter_message(text=f"{utterMultilanguage['badAnswer'][language]}.")
            return { 'answer3': None }

    def validate_answer4(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if slot_value != None:
            proposal = queryProposalDB(askedQuestions[-1], language, languageDim)
            proposalArray = proposal[0].split('*')

            currentIntent = tracker.latest_message['intent'].get('name')
            answerTemp = ''
            answer = ''
            if currentIntent == 'affirm':
                answer = mappingTF[language][str(slot_value)]
            elif currentIntent == 'deny':
                answer = mappingTF[language][str(slot_value)]
            elif currentIntent == 'resolve_entity':
                answerTemp = get_key_from_value(mapping, str(slot_value).lower())
                answer = proposalArray[answerTemp-1]
            elif currentIntent == 'skip_exam':
                answer = 'Na'
            dispatcher.utter_message(text=f"{utterMultilanguage['rememberAnswer'][language]}: {answer}")
            answers[int(askedQuestions[-1])] = (str(answer))

            global lastAnswerResult
            if str(answer).lower() == str(realAnswers[currentQuestionNumber]).lower():
                lastAnswerResult = True
            else: 
                lastAnswerResult = False

            return { 'answer4': answer }
        else:
            dispatcher.utter_message(text=f"{utterMultilanguage['badAnswer'][language]}.")
            return { 'answer4': None }

    def validate_answer5(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if slot_value != None:
            proposal = queryProposalDB(askedQuestions[-1], language, languageDim)
            proposalArray = proposal[0].split('*')

            currentIntent = tracker.latest_message['intent'].get('name')
            answerTemp = ''
            answer = ''
            if currentIntent == 'affirm':
                answer = mappingTF[language][str(slot_value)]
            elif currentIntent == 'deny':
                answer = mappingTF[language][str(slot_value)]
            elif currentIntent == 'resolve_entity':
                answerTemp = get_key_from_value(mapping, str(slot_value).lower())
                answer = proposalArray[answerTemp-1]
            elif currentIntent == 'skip_exam':
                answer = 'Na'
            global lastAnswerResult
            if str(answer).lower() == str(realAnswers[currentQuestionNumber]).lower():
                lastAnswerResult = True
            else: 
                lastAnswerResult = False

            dispatcher.utter_message(text=f"{utterMultilanguage['rememberAnswer'][language]}: {answer}")
            answers[int(askedQuestions[-1])] = (str(answer))
            now = datetime.now()
            global ending_time
            ending_time = now.strftime("%d/%m/%Y %H:%M:%S")

            return { 'answer5': answer }
        else:
            dispatcher.utter_message(text=f"{utterMultilanguage['badAnswer'][language]}.")
            return { 'answer5': None }

    def validate_wanna_explanation(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if slot_value != None:

            grade, explication = getGrade(answers, realAnswers, languageDim)
            
            if slot_value == True and explication != {}:

                for i in explication:
                    dispatcher.utter_message(text=f"{utterMultilanguage['eplanationQuestion'][language]}: {queryQuestionDB(i, language, languageDim)}")
                    img = queryImagesDB(str(i), languageDim)
                    if img != '' and img != None:
                        dispatcher.utter_image_url(img)
                    dispatcher.utter_message(text=f"{utterMultilanguage['eplanationAnswer'][language]}: {answers[i]}, {utterMultilanguage['eplanationRealAnswer'][language]} {realAnswers[i]}.")
                    dispatcher.utter_message(text=f"{utterMultilanguage['eplanationExplanation'][language]}: {explication[i]}")
            elif slot_value == True and explication == {}:
                    dispatcher.utter_message(text=f"{utterMultilanguage['eplanationAllCorrect'][language]}.")


            tempsAnswerFormated = []
            tempsRealAnswerFormated = []
            tempsIdQuestions  = []
            for n in answers:
                tempsAnswerFormated.append(answers[n])
                tempsRealAnswerFormated.append(realAnswers[n])
                tempsIdQuestions.append(idQuestions[n])
            answersFormated = '*'.join(tempsAnswerFormated)
            realAnswerFormated = '*'.join(tempsRealAnswerFormated)
            idQuestionsFormated = '*'.join(tempsIdQuestions)
            
            insertAnswers = f'INSERT INTO exam (id_exam, id_student, starting_time, id_questions, answers, real_answers, grade, ending_time) VALUES ("{id_exam}", "{id_student}", "{str(starting_time)}", "{str(idQuestionsFormated)}", "{str(answersFormated)}", "{str(realAnswerFormated)}", {grade}, "{str(ending_time)}");'
            queryMySql(insertAnswers)
            dispatcher.utter_message(text=f"{utterMultilanguage['end'][language]}.")
            dispatcher.utter_message(text=f"{utterMultilanguage['grade'][language]}: {grade}.")


            return { 'wanna_explanation': slot_value }
        else:
            dispatcher.utter_message(text=f"{utterMultilanguage['badAnswer'][language]}.")
            return { 'wanna_explanation': None }

class ActionSkipExam(Action):

    def name(self):
        return "action_skip_exam"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        requestedSlot = tracker.slots['requested_slot']

        if 'answer'  in requestedSlot:
            dispatcher.utter_message(text=f"As you requested, i skip the current question.")
            return [SlotSet(requestedSlot,'Na')]
        else:
            dispatcher.utter_message(text=f"I can't skip this question.")
            return []


class ActionResetExamSlots(Action):

    def name(self):
        return "action_reset_exam_slots"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet('answer1',None), SlotSet('answer2',None), SlotSet('answer3',None), SlotSet('answer4',None), SlotSet('answer5',None)]

class AskForSlotActionIdExam(Action):
    def name(self) -> Text:
        return "action_ask_id_exam"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        dispatcher.utter_message(text=f"Please, could you give us your exam id ?")
        return []

class AskForSlotActionLanguage(Action):
    def name(self) -> Text:
        return "action_ask_language"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        dispatcher.utter_message(text=f"In order to give you the best condition, could you please give us your prefered language ?")
        return []

class AskForSlotActionIdStudent(Action):
    def name(self) -> Text:
        return "action_ask_id_student"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        dispatcher.utter_message(text=f"Before starting the exam, could you please give us your student id ?")
        return []

class AskForSlotActionWannaHelp(Action):
    def name(self) -> Text:
        return "action_ask_wanna_explanation"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        dispatcher.utter_message(text=f"{utterMultilanguage['explanation'][language]}")
        return []

class AskForSlotActionAnswer1(Action):
    def name(self) -> Text:
        return "action_ask_answer1"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        createNestedDataDict(language, languageDim)
        global mediumComplexity
        mediumComplexity = getMediumComplexity()

        now = datetime.now()
        global starting_time
        starting_time = now.strftime("%d/%m/%Y %H:%M:%S")

        questionNumber = randomQuestionComplexity2()
        askedQuestions.append(str(questionNumber))

        global currentQuestionNumber
        currentQuestionNumber = int(questionNumber)

        global currentComplexity
        currentComplexity = queryQuestionComplexityDB(questionNumber, languageDim)

        global currentTheme
        currentTheme = queryQuestionThemeDB(questionNumber, languageDim)

        global realAnswers
        realAnswers[int(questionNumber)] = (queryAnswerDB(questionNumber, language, languageDim))

        question = queryQuestionDB(questionNumber, language, languageDim)
        proposal = queryProposalDB(questionNumber, language, languageDim)
        proposalList = proposal[0].split('*')
        
        dispatcher.utter_message(text=f"This question is complexity {currentComplexity} in theme {currentTheme}")
        dispatcher.utter_message(text=f"{question}")
        img = queryImagesDB(questionNumber, languageDim)
        if img != '' and img != None:
            dispatcher.utter_image_url(img)
        count = 0
        for answerProposal in proposalList:
            count += 1
            dispatcher.utter_message(text=f'{count}: {answerProposal}')
        
        questionType = queryQuestionTypeDB(questionNumber, languageDim)
        idQuestions[int(questionNumber)] = f'{questionNumber}{languageDim}'
        dispatcher.utter_message(text=f"{questionType}: {instruction[str(questionType)]}")
        return []

class AskForSlotActionAnswer2(Action):
    def name(self) -> Text:
        return "action_ask_answer2"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        global nextQuestionNumber, currentComplexity, currentTheme
        nextQuestionNumber, nextComplexity, nextTheme = getNextQuestionNumber()
        currentTheme = nextTheme
        currentComplexity = nextComplexity
        questionNumber = nextQuestionNumber
        global currentQuestionNumber
        currentQuestionNumber = int(questionNumber)
        askedQuestions.append(str(questionNumber))
        #questionNumber = randomQuestion()

        global realAnswers
        realAnswers[int(questionNumber)] = (queryAnswerDB(questionNumber, language, languageDim))

        question = queryQuestionDB(questionNumber, language, languageDim)
        proposal = queryProposalDB(questionNumber, language, languageDim)
        proposalList = proposal[0].split('*')
        
        dispatcher.utter_message(text=f"This question is complexity {currentComplexity} in theme {currentTheme}")
        dispatcher.utter_message(text=f"{question}")
        img = queryImagesDB(questionNumber, languageDim)
        if img != '' and img != None:
            dispatcher.utter_image_url(img)
        count = 0
        for answerProposal in proposalList:
            count += 1
            dispatcher.utter_message(text=f'{count}: {answerProposal}')
        
        questionType = queryQuestionTypeDB(questionNumber, languageDim)
        idQuestions[int(questionNumber)] = f'{questionNumber}{languageDim}'
        dispatcher.utter_message(text=f"{questionType}: {instruction[str(questionType)]}")
        return []

class AskForSlotActionAnswer3(Action):
    def name(self) -> Text:
        return "action_ask_answer3"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        global nextQuestionNumber, currentComplexity, currentTheme
        nextQuestionNumber, nextComplexity, nextTheme = getNextQuestionNumber()
        currentTheme = nextTheme
        currentComplexity = nextComplexity
        questionNumber = nextQuestionNumber
        global currentQuestionNumber
        currentQuestionNumber = int(questionNumber)
        askedQuestions.append(str(questionNumber))
        #questionNumber = randomQuestion()

        global realAnswers
        realAnswers[int(questionNumber)] = (queryAnswerDB(questionNumber, language, languageDim))

        question = queryQuestionDB(questionNumber, language, languageDim)
        proposal = queryProposalDB(questionNumber, language, languageDim)
        proposalList = proposal[0].split('*')
        
        dispatcher.utter_message(text=f"This question is complexity {currentComplexity} in theme {currentTheme}")
        dispatcher.utter_message(text=f"{question}")
        img = queryImagesDB(questionNumber, languageDim)
        if img != '' and img != None:
            dispatcher.utter_image_url(img)
        count = 0
        for answerProposal in proposalList:
            count += 1
            dispatcher.utter_message(text=f'{count}: {answerProposal}')
        
        questionType = queryQuestionTypeDB(questionNumber, languageDim)
        idQuestions[int(questionNumber)] = f'{questionNumber}{languageDim}'
        dispatcher.utter_message(text=f"{questionType}: {instruction[str(questionType)]}")
        return []

class AskForSlotActionAnswer4(Action):
    def name(self) -> Text:
        return "action_ask_answer4"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        global nextQuestionNumber, currentComplexity, currentTheme
        nextQuestionNumber, nextComplexity, nextTheme = getNextQuestionNumber()
        currentTheme = nextTheme
        currentComplexity = nextComplexity
        questionNumber = nextQuestionNumber
        global currentQuestionNumber
        currentQuestionNumber = int(questionNumber)
        askedQuestions.append(str(questionNumber))
        #questionNumber = randomQuestion()

        global realAnswers
        realAnswers[int(questionNumber)] = (queryAnswerDB(questionNumber, language, languageDim))

        question = queryQuestionDB(questionNumber, language, languageDim)
        proposal = queryProposalDB(questionNumber, language, languageDim)
        proposalList = proposal[0].split('*')
        
        dispatcher.utter_message(text=f"This question is complexity {currentComplexity} in theme {currentTheme}")
        dispatcher.utter_message(text=f"{question}")
        img = queryImagesDB(questionNumber, languageDim)
        if img != '' and img != None:
            dispatcher.utter_image_url(img)
        count = 0
        for answerProposal in proposalList:
            count += 1
            dispatcher.utter_message(text=f'{count}: {answerProposal}')
        
        questionType = queryQuestionTypeDB(questionNumber, languageDim)
        idQuestions[int(questionNumber)] = f'{questionNumber}{languageDim}'
        dispatcher.utter_message(text=f"{questionType}: {instruction[str(questionType)]}")
        return []

class AskForSlotActionAnswer5(Action):
    def name(self) -> Text:
        return "action_ask_answer5"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        global nextQuestionNumber, currentComplexity, currentTheme
        nextQuestionNumber, nextComplexity, nextTheme = getNextQuestionNumber()
        currentTheme = nextTheme
        currentComplexity = nextComplexity
        questionNumber = nextQuestionNumber
        global currentQuestionNumber
        currentQuestionNumber = int(questionNumber)
        askedQuestions.append(str(questionNumber))
        #questionNumber = randomQuestion()

        global realAnswers
        realAnswers[int(questionNumber)] = (queryAnswerDB(questionNumber, language, languageDim))

        question = queryQuestionDB(questionNumber, language, languageDim)
        proposal = queryProposalDB(questionNumber, language, languageDim)
        proposalList = proposal[0].split('*')
        
        dispatcher.utter_message(text=f"This question is complexity {currentComplexity} in theme {currentTheme}")
        dispatcher.utter_message(text=f"{question}")
        img = queryImagesDB(questionNumber, languageDim)
        if img != '' and img != None:
            dispatcher.utter_image_url(img)
        count = 0
        for answerProposal in proposalList:
            count += 1
            dispatcher.utter_message(text=f'{count}: {answerProposal}')
        
        questionType = queryQuestionTypeDB(questionNumber, languageDim)
        idQuestions[int(questionNumber)] = f'{questionNumber}{languageDim}'
        dispatcher.utter_message(text=f"{questionType}: {instruction[str(questionType)]}")
        return []

city_db = {
    'brussels': 'Europe/Brussels',
    'zagreb': 'Europe/Zagreb',
    'london': 'Europe/London',
    'lisbon': 'Europe/Lisbon',
    'amsterdam': 'Europe/Amsterdam',
    'seattle': 'US/Pacific'
}

class ActionTellTime(Action):
    def name(self) -> Text:
        return "action_tell_time"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        current_place = next(tracker.get_latest_entity_values("place"), None)
        utc = arrow.utcnow()

        if not current_place:

            location = tracker.get_slot("location")

            if location:
                timezoneLocation = utc.to(city_db[location.lower()]).format('HH:mm')
                msg = f"It's {timezoneLocation} utc now."
                dispatcher.utter_message(text=msg)
                return []
            else:
                msg = f"It's {utc.format('HH:mm')} utc now. You can also give me a place"
                dispatcher.utter_message(text=msg)
                return []
        
        tz_string = city_db.get(current_place.lower(), None)
        if not tz_string:
            msg = f"I don't know this place: {current_place}. Did you spelled it correctly ?"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"It's {utc.to(city_db[current_place.lower()]).format('HH:mm')} in {current_place} now."
        dispatcher.utter_message(text=msg)
        
        return []



class ActionRememberWhereILive(Action):
    def name(self) -> Text:
        return "action_remember_where_i_live"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        current_place = next(tracker.get_latest_entity_values("place"), None)
        utc = arrow.utcnow()

        if not current_place:
            msg = f"I didn't get where you lived. Are you sure it's spelled correctly ?"
            dispatcher.utter_message(text=msg)
            return []
        
        tz_string = city_db.get(current_place.lower(), None)
        if not tz_string:
            msg = f"I don't know this place: {current_place}. Did you spelled it correctly ?"
            dispatcher.utter_message(text=msg)
            return []

        msg = f"Sure thing ! I'll remember you live in {current_place}"
        dispatcher.utter_message(text=msg)

        return [SlotSet("location", current_place)]



class ActionTimeDifference(Action):
    def name(self) -> Text:
        return "action_time_difference"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        timezone_to = next(tracker.get_latest_entity_values("place"), None)
        timezone_in = tracker.get_slot("location")

        if not timezone_in:
            msg = f"To calculate the timezone difference, i need to know where you live."
            dispatcher.utter_message(text=msg)
            return []
        
        if not timezone_to:
            msg = f"I didn't get the timezone you'd like to compare against. Are sure you spelled it correctly ?"
            dispatcher.utter_message(text=msg)
            return []
        
        tz_string = city_db.get(timezone_to.lower(), None)
        if not tz_string:
            msg = f"I don't know this place: {timezone_to}. Did you spelled it correctly ?"
            dispatcher.utter_message(text=msg)
            return []

        t1 = arrow.utcnow().to(city_db[timezone_to])
        t2 = arrow.utcnow().to(city_db[timezone_in])
        max_t, min_t = max(t1, t2), min(t1,t2)

        diff_seconds = dateparser.parse(str(max_t)[:19]) - dateparser.parse(str(min_t)[:19])
        diff_hours = int(diff_seconds.seconds/3600)

        msg = f"There is {min(diff_hours, 24-diff_hours)}H time difference."
        dispatcher.utter_message(text=msg)

        return []

ALLOWED_PIZZA_SIZES = ['s','m','l','xl']
ALLOWED_PIZZA_TYPES = ['fungi','veggie','hawai','hawaii', 'mozzarella', 'mozzarela', 'pepperoni']
VEGETARIAN_PIZZAS = ["mozzarella", "fungi", "veggie"]
MEAT_PIZZAS = ["pepperoni", "hawaii"]

class ValidateSimplePizzaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_simple_pizza_form"
    
    def validate_pizza_size(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        """Validate pizza_size value"""

        if slot_value.lower() not in ALLOWED_PIZZA_SIZES:
            dispatcher.utter_message(text=f'We only accept pizza sizes: s/m/l/xl.')
            return {"pizza_size": None}
        dispatcher.utter_message(text=f'OK! You want to have a {slot_value} pizza.')
        return {"pizza_size": slot_value}

    def validate_pizza_type(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        """Validate pizza_type value"""

        if slot_value.lower() not in ALLOWED_PIZZA_TYPES:
            dispatcher.utter_message(text=f"We don't recognize that pizza. We serve {'/'.join(ALLOWED_PIZZA_TYPES)}")
            return {"pizza_type": None}
        dispatcher.utter_message(text=f'OK! You want to have a {slot_value} pizza.')
        return {"pizza_type": slot_value}

class ActionResetPizzaSlots(Action):

    def name(self):
        return "action_reset_pizza_slots"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet('pizza_type',None), SlotSet('pizza_size',None)]

class ActionResetAllSlots(Action):

    def name(self):
        return "action_reset_all_slots"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [AllSlotsReset()]


class AskForVegetarianAction(Action):
    def name(self):
        return "action_ask_vegetarian"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Would you like to order a vegetarian pizza ?", buttons=[{"title": "yes", "payload": "/affirm"},{"title": "no", "pqyload": "/deny"}])

        return []

class AskForPizzaTypeAction(Action):
    def name(self):
        return "action_ask_pizza_type"

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if tracker.get_slot("vegetarian"):
            dispatcher.utter_message(text="What kind of vegetarian pizza you want ?", buttons=[{"title": p, "payload": p} for p in VEGETARIAN_PIZZAS])
        else:
            dispatcher.utter_message(text="What kind of meat pizza you want ?", buttons=[{"title": p, "payload": p} for p in MEAT_PIZZAS])

        return []

class ValidationFancyPizzaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_fancy_pizza_form"

    def validate_vegetarian(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if tracker.get_intent_of_latest_message() == "affirm":
            dispatcher.utter_message(text="I will remember you prefer vegetarian pizzas.")
            return {"vegetarian": True}
        if tracker.get_intent_of_latest_message() == "deny":
            dispatcher.utter_message(text="I will remember you prefer meat pizzas.")
            return {"vegetarian": False}
        dispatcher.utter_message(text="I didn't understand your preference.")
        return {"vegetarian": None}
    
    def validate_pizza_size(self, slot_value: any, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        """Validate pizza_size value"""

        if slot_value.lower() not in ALLOWED_PIZZA_SIZES:
            dispatcher.utter_message(text=f'We only accept pizza sizes: s/m/l/xl.')
            return {"pizza_size": None}
        dispatcher.utter_message(text=f'OK! You want to have a {slot_value} pizza.')
        return {"pizza_size": slot_value}



def resolve_mention(tracker: Tracker) -> Text:
    """
    Resolves a mention of an entity, such as first, to the actual entity.
    If multiple entities are listed during the conversation, the entities
    are stored in the slot 'listed_items' as a list. We resolve the mention,
    such as first, to the list index and retrieve the actual entity.
    :param tracker: tracker
    :return: name of the actually entity
    """
    graph_database = GraphDatabase()

    mention = tracker.get_slot("mention")
    listed_items = tracker.get_slot("listed_items")

    if mention is not None and listed_items is not None:
        idx = int(graph_database.map("mention-mapping", mention))

        if type(idx) is int and idx < len(listed_items):
            return listed_items[idx]


def get_entity_type(tracker: Tracker) -> Text:
    """
    Get the entity type mentioned by the user. As the user may speak of an
    entity type in plural, we need to map the mentioned entity type to the
    type used in the knowledge base.
    :param tracker: tracker
    :return: entity type (same type as used in the knowledge base)
    """
    graph_database = GraphDatabase()
    entity_type = tracker.get_slot("entity_type")
    return graph_database.map("entity-type-mapping", entity_type)


def get_attribute(tracker: Tracker) -> Text:
    """
    Get the attribute mentioned by the user. As the user may use a synonym for
    an attribute, we need to map the mentioned attribute to the
    attribute name used in the knowledge base.
    :param tracker: tracker
    :return: attribute (same type as used in the knowledge base)
    """
    graph_database = GraphDatabase()
    attribute = tracker.get_slot("attribute")
    return graph_database.map("attribute-mapping", attribute)


def get_entity_name(tracker: Tracker, entity_type: Text):
    """
    Get the name of the entity the user referred to. Either the NER detected the
    entity and stored its name in the corresponding slot or the user referred to
    the entity by an ordinal number, such as first or last, or the user refers to
    an entity by its attributes.
    :param tracker: Tracker
    :param entity_type: the entity type
    :return: the name of the actual entity (value of key attribute in the knowledge base)
    """

    # user referred to an entity by an ordinal number
    mention = tracker.get_slot("mention")
    if mention is not None:
        return resolve_mention(tracker)

    # user named the entity
    entity_name = tracker.get_slot(entity_type)
    if entity_name:
        return entity_name

    # user referred to an entity by its attributes
    listed_items = tracker.get_slot("listed_items")
    attributes = get_attributes_of_entity(entity_type, tracker)

    if listed_items and attributes:
        # filter the listed_items by the set attributes
        graph_database = GraphDatabase()
        for entity in listed_items:
            key_attr = schema[entity_type]["key"]
            result = graph_database.validate_entity(
                entity_type, entity, key_attr, attributes
            )
            if result is not None:
                return to_str(result, key_attr)

    return None


def get_attributes_of_entity(entity_type, tracker):
    # check what attributes the NER found for entity type
    attributes = []
    if entity_type in schema:
        for attr in schema[entity_type]["attributes"]:
            attr_val = tracker.get_slot(attr.replace("-", "_"))
            if attr_val is not None:
                attributes.append({"key": attr, "value": attr_val})
    return attributes


def reset_attribute_slots(slots, entity_type, tracker):
    # check what attributes the NER found for entity type
    if entity_type in schema:
        for attr in schema[entity_type]["attributes"]:
            attr = attr.replace("-", "_")
            attr_val = tracker.get_slot(attr)
            if attr_val is not None:
                slots.append(SlotSet(attr, None))
    return slots


def to_str(entity: Dict[Text, Any], entity_keys: Union[Text, List[Text]]) -> Text:
    """
    Converts an entity to a string by concatenating the values of the provided
    entity keys.
    :param entity: the entity with all its attributes
    :param entity_keys: the name of the key attributes
    :return: a string that represents the entity
    """
    if isinstance(entity_keys, str):
        entity_keys = [entity_keys]

    v_list = []
    for key in entity_keys:
        _e = entity
        for k in key.split("."):
            _e = _e[k]

        if "balance" in key or "amount" in key:
            v_list.append(f"{str(_e)} €")
        elif "date" in key:
            v_list.append(_e.strftime("%d.%m.%Y (%H:%M:%S)"))
        else:
            v_list.append(str(_e))
    return ", ".join(v_list)


class ActionQueryEntities(Action):
    """Action for listing entities.
    The entities might be filtered by specific attributes."""

    def name(self):
        return "action_query_entities"

    def run(self, dispatcher, tracker, domain):
        graph_database = GraphDatabase()

        # first need to know the entity type we are looking for
        entity_type = get_entity_type(tracker)

        if entity_type is None:
            dispatcher.utter_template("utter_rephrase", tracker)
            return []

        # check what attributes the NER found for entity type
        attributes = get_attributes_of_entity(entity_type, tracker)

        # query knowledge base
        entities = graph_database.get_entities(entity_type, attributes)

        # filter out transactions that do not belong the set account (if any)
        if entity_type == "transaction":
            account_number = tracker.get_slot("account")
            entities = self._filter_transaction_entities(entities, account_number)

        if not entities:
            dispatcher.utter_template(
                "I could not find any entities for '{}'.".format(entity_type), tracker
            )
            return []

        # utter a response that contains all found entities
        # use the 'representation' attributes to print an entity
        entity_representation = schema[entity_type]["representation"]

        dispatcher.utter_message(
            "Found the following '{}' entities:".format(entity_type)
        )
        sorted_entities = sorted([to_str(e, entity_representation) for e in entities])
        for i, e in enumerate(sorted_entities):
            dispatcher.utter_message(f"{i + 1}: {e}")

        # set slots
        # set the entities slot in order to resolve references to one of the found
        # entites later on
        entity_key = schema[entity_type]["key"]

        slots = [
            SlotSet("entity_type", entity_type),
            SlotSet("listed_items", list(map(lambda x: to_str(x, entity_key), entities))),
        ]

        # if only one entity was found, that the slot of that entity type to the
        # found entity
        if len(entities) == 1:
            slots.append(SlotSet(entity_type, to_str(entities[0], entity_key)))

        reset_attribute_slots(slots, entity_type, tracker)

        return slots

    def _filter_transaction_entities(
        self, entities: List[Dict[Text, Any]], account_number: Text
    ) -> List[Dict[Text, Any]]:
        """
        Filter out all transactions that do not belong to the provided account number.
        :param entities: list of transactions
        :param account_number: account number
        :return: list of filtered transactions with max. 5 entries
        """
        if account_number is not None:
            filtered_entities = []
            for entity in entities:
                if entity["account-of-creator"]["account-number"] == account_number:
                    filtered_entities.append(entity)
            return filtered_entities[:5]

        return entities[:5]


class ActionQueryAttribute(Action):
    """Action for querying a specific attribute of an entity."""

    def name(self):
        return "action_query_attribute"

    def run(self, dispatcher, tracker, domain):
        graph_database = GraphDatabase()

        # get entity type of entity
        entity_type = get_entity_type(tracker)

        if entity_type is None:
            dispatcher.utter_template("utter_rephrase", tracker)
            return []

        # get name of entity and attribute of interest
        name = get_entity_name(tracker, entity_type)
        attribute = get_attribute(tracker)

        if name is None or attribute is None:
            dispatcher.utter_template("utter_rephrase", tracker)
            slots = [SlotSet("mention", None)]
            reset_attribute_slots(slots, entity_type, tracker)
            return slots

        # query knowledge base
        key_attribute = schema[entity_type]["key"]
        value = graph_database.get_attribute_of(
            entity_type, key_attribute, name, attribute
        )

        # utter response
        if value is not None and len(value) == 1:
            dispatcher.utter_message(
                f"{name} has the value '{value[0]}' for attribute '{attribute}'."
            )
        else:
            dispatcher.utter_message(
                f"Did not found a valid value for attribute {attribute} for entity '{name}'."
            )

        slots = [SlotSet("mention", None), SlotSet(entity_type, name)]
        reset_attribute_slots(slots, entity_type, tracker)
        return slots


class ActionCompareEntities(Action):
    """Action for comparing multiple entities."""

    def name(self):
        return "action_compare_entities"

    def run(self, dispatcher, tracker, domain):
        graph = GraphDatabase()

        # get entities to compare and their entity type
        listed_items = tracker.get_slot("listed_items")
        entity_type = get_entity_type(tracker)

        if listed_items is None or entity_type is None:
            dispatcher.utter_template("utter_rephrase", tracker)
            return []

        # get attribute of interest
        attribute = get_attribute(tracker)

        if attribute is None:
            dispatcher.utter_template("utter_rephrase", tracker)
            return []

        # utter response for every entity that shows the value of the attribute
        for e in listed_items:
            key_attribute = schema[entity_type]["key"]
            value = graph.get_attribute_of(entity_type, key_attribute, e, attribute)

            if value is not None and len(value) == 1:
                dispatcher.utter_message(
                    f"{e} has the value '{value[0]}' for attribute '{attribute}'."
                )

        return []


class ActionResolveEntity(Action):
    """Action for resolving a mention."""

    def name(self):
        return "action_resolve_entity"

    def run(self, dispatcher, tracker, domain):
        entity_type = tracker.get_slot("entity_type")
        listed_items = tracker.get_slot("listed_items")

        if entity_type is None:
            dispatcher.utter_template("utter_rephrase", tracker)
            return []

        # Check if entity was mentioned as 'first', 'second', etc.
        mention = tracker.get_slot("mention")
        if mention is not None:
            value = resolve_mention(tracker)
            if value is not None:
                return [SlotSet(entity_type, value), SlotSet("mention", None)]

        # Check if NER recognized entity directly
        # (e.g. bank name was mentioned and recognized as 'bank')
        value = tracker.get_slot(entity_type)
        if value is not None and value in listed_items:
            return [SlotSet(entity_type, value), SlotSet("mention", None)]

        dispatcher.utter_template("utter_rephrase", tracker)
        return [SlotSet(entity_type, None), SlotSet("mention", None)]