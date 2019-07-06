from django.http import HttpResponse
from django.shortcuts import render
import pymysql as sql
from datetime import datetime
from random import choice

from os import system
from base64 import b64decode
import requests, json

use_base64 = False
testcases = {}
question = []
def homepage(request):
    return render(request, 'base.html')

def redirect(request):
    if request.GET['goto'] == 'Login': return render(request, 'login.html', {'login': ''})
    elif request.GET['goto'] == 'Register': return render(request, 'register.html')
    elif request.GET['goto'] == 'RegisterQ': return render(request, 'new.html')

def loginCheck(request):
    conn = sql.connect(host = 'localhost', port = 3306, user = 'root', password = '12345678', db = 'Practice')
    cmd = conn.cursor()
    # Password Check
    q = f"select password from Compiler where email = '{request.GET['email']}'"
    cmd.execute(q)
    row = cmd.fetchone()

    # Question Title Fetch
    q = "select * from OrganizationRecord"
    cmd.execute(q)
    qBank = cmd.fetchall()
    if row == None: return render(request, 'login.html', {'login': 'Email not found.   Please consider registering first.'})
    conn.close()
    if row[0] == request.GET['pass']: return render(request, 'questionView.html', {'qBank': qBank})
    else: return render(request, 'login.html', {'login': 'Invalid Password'})

def register(request):
    conn = sql.connect(host = 'localhost', port = 3306, user = 'root', password = '12345678', db = 'Practice')
    cmd = conn.cursor()
    q = f"insert into Compiler (first_name, last_name, email, mobile, password, create_date, update_date, status) values('{request.GET['fn']}', '{request.GET['ln']}', '{request.GET['email']}', '{request.GET['mob']}', '{request.GET['pass']}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', 'Not Verified')"
    cmd.execute(q)
    print('Record Added.')
    conn.commit()
    conn.close()
    return HttpResponse("<html><h1>User Registered.</h1></html>")

def result(request):
    global testcases
    global question
    # Global
    URL = ''
    language_d = {}
    data_d = {}
    result = None
    use_base64 = False

    URL = 'https://api.judge0.com/submissions/' 

    languages = [
        {"id": 1,"name": "C (gcc 7.2.0)"},
        {"id": 2,"name": "C++ (g++ 7.2.0)"},
        {"id": 3,"name": "C# (mono 5.4.0.167)"},
        {"id": 4,"name": "Java (OpenJDK 9 with Eclipse OpenJ9)"},
        {"id": 5,"name": "JavaScript (nodejs 8.5.0)"},
        {"id": 6,"name": "Python (3.6.0)"},
    ]
    data = {
        "source_code": None,
        "language_id": None,
        "number_of_runs": "1",
        "stdin": None,
        "expected_output": None,
        "cpu_time_limit": "2",
        "cpu_extra_time": "0.5",
        "wall_time_limit": "5",
        "memory_limit": "128000",
        "stack_limit": "64000",
        "max_processes_and_or_threads": "30",
        "enable_per_process_and_thread_time_limit": False,
        "enable_per_process_and_thread_memory_limit": True,
        "max_file_size": "1024"
    }


    # Functions
    def initialize(url, language, data, testcases=None):
        global URL
        global language_d
        global data_d
        URL = url
        language_d = language
        data_d = data

    def code_string():
        code = request.GET['code']
        return code

    def language_id(l):
        global use_base64
        s = request.GET['language']
        if s == '4' or s == '10' or s == '16' or s == '26': use_base64 = True
        return s

    def prep_submissionDict(stdin, exp):
        data_d["language_id"] = language_id(language_d)
        data_d["source_code"] = code_string()
        data_d["stdin"] = stdin
        data_d["expected_output"] = exp
        return data_d

    def generate_token(data):
        r = requests.post(URL, data)
        if r.status_code == 201: return r.json()
        elif r.status_code == 401:
            print('Authentication Failed')
            quit()
        elif r.status_code == 422:
            print('Language ID invalid')
            quit()

    def fetch_server(token):
        while True:
            global use_base64
            print('OUTPUT:-')
            print('Processing...')
            if use_base64 == True: useb64 = 'true'
            else: useb64 = 'false'
            r = requests.get(URL + token['token'] + '?base64_encoded=' + useb64)
            if r.status_code != 200: break
            else:
                r = r.json()
                if r['status']['id'] == 1 or r['status']['id'] == 2: continue
                else:
                    if use_base64 == True:
                        if r['stdout'] != None: r['stdout'] = decrypt(r['stdout'])
                        if r['compile_output'] != None: r['compile_output'] = decrypt(r['compile_output'])
                        if r['message'] != None: r['message'] = decrypt(r['message'])
                        if r['stderr'] != None: r['stderr'] = decrypt(r['stderr'])
                    return [1, r]
        x = r.status_code
        if x == 401: return [0, {'error': 'Authentication Failed', 'exception': 'Unknown'}]
        elif x == 500:
            return [0, {'error': 'Authentication Failed', 'exception': 'Unknown'}]

    def display_output(o):
        return o[1]

    def decrypt(s):
        return b64decode(s).decode()

    # Compiler.py
    returnResult = []
    for x in testcases.keys():
        initialize(URL, languages, data)
        s_dict = prep_submissionDict(testcases[x]['stdin'], testcases[x]['expected_output'])
        token = generate_token(s_dict)
        response = fetch_server(token)
        s = display_output(response)
        returnResult.append(s)
    d = []
    t = []
    for x in testcases.keys(): t.append(x)
    for i, r in enumerate(returnResult):
        d.append([i+1,testcases[t[i]]['stdin'], r['stdout'], r['status']['description']])
    # print('\n\n\n', returnResult, '\n\n\n')
    # print('\n\n\n', testcases, '\n\n\n')
    print(d)
    return render(request, 'compiler_extended.html', {'d': d, 'question': question})
    # return render(request, 'compiler_extended.html', d)

def questionDashboard(request):
    def insertQuestion():
        x = 1
        while True:
            testcase_id = str(question_id)+ '_' + str(x)
            try:
                q = f"insert into Testcases values ({transaction_id}, '{question_id}', '{testcase_id}', '{stdin}', '{expected_output}')"
                cmd.execute(q)
                break
            except:
                print('\n\nTestcase Exists\n\n')
            x += 1

    transaction_id = 1
    organization_id = request.GET['org_id']
    set_no = str(organization_id) + '_' + str(request.GET['set_id'])
    question_id = str(set_no) + str(request.GET['ques_id'])
    question_title = request.GET['ques_title']
    question = request.GET['ques']
    stdin = request.GET['stdin']
    expected_output = request.GET['expected_output']

    conn = sql.connect(host = 'localhost', port = 3306, user = 'root', password = '12345678', db = 'Practice')
    cmd = conn.cursor()

    try:
        q = f"insert into OrganizationRecord values ({transaction_id}, '{organization_id}', '{set_no}', '{question_id}', '{question_title}','{question}')"
        cmd.execute(q)
    except Exception as e:
        print('\n', e, '\n')

    insertQuestion()
    conn.commit()
    conn.close()
    return render(request, "new_extended.html")

def questionDisplay(request):
    global testcases
    global question
    qid = request.GET['qid']
    conn = sql.connect(host = 'localhost', port = 3306, user = 'root', password = '12345678', db = 'Practice')
    cmd = conn.cursor()
    q = f"select question_title, question from OrganizationRecord where question_id = '{qid}'"
    cmd.execute(q)
    question = cmd.fetchone()
    q = f"select testcase_no, stdin, expected_output from Testcases where question_id = '{qid}'"
    cmd.execute(q)
    testcases_list = cmd.fetchall()
    testcases = {}
    print('\n\n\n',testcases)
    for i, x in enumerate(testcases_list): testcases[i+1] = {'stdin': x[1], 'expected_output': x[2], 'description': 'comment_result'}
    return render(request, "compiler.html", {'question': question})