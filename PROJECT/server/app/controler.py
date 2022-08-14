
from flask import Flask, redirect, render_template, request
from flask import current_app as app
from flask_login import login_manager,login_user,current_user,LoginManager
import requests, json

from sqlalchemy import values
from .database import db
from .models import Response_event, Users, Forms,Fields, Subfield_names,Number_values,Text_values,Responses
import os
import string
import random



@app.route('/', methods=['GET'])
def home():
    if(current_user.is_authenticated):
        return render_template('home_authenticated.html')
    return render_template('home.html')

@app.route('/redir', methods=['GET'])
def google_redirect():
    code = request.args.get('code')
    # getting the access token
    url = "https://oauth2.googleapis.com/token"
    body = {
        "client_id" : os.getenv("CLIENT_ID"),
        "client_secret" :os.getenv("CLIENT_SECRETE"),
        "code" : code,
        "grant_type" : "authorization_code",
        "redirect_uri" : "http://localhost:8081/redir",
    }

    # get access token
    res = requests.post(url, json = body)
    data =  json.loads(res.text)
    access_token = data["access_token"]
    id_token = data["id_token"]
    refresh_token = data["refresh_token"]

    
    # getting user information 
    url = "https://oauth2.googleapis.com/tokeninfo?id_token={}".format(id_token)
    res = requests.post(url, json = body)
    data =  json.loads(res.text)
    email = data["email"]
    id = data["sub"]
    
    # save user information
    user = Users.query.filter_by(id = id).first()
    if not user:
        new_user = Users(id = id, email = email, access_token=access_token, refresh_token=refresh_token)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
    else:
        login_user(user)
    return redirect("/")

@app.route("/create-forms",methods=['GET'])
def create_forms():
    return render_template('create-forms.html')

@app.route("/create-forms",methods=['POST'])
def create_form():
    data = request.json
    form_name = data["form_name"]
    base = os.getenv("BASE")
    random_str = ''.join(random.choices(string.ascii_uppercase +string.digits, k = 5))
    
    #  create from object
    while(True):
        form_url = base+'/forms/'+form_name+'/'+random_str
        forms = Forms.query.filter_by(form_url = form_url).first()
        if not forms:
            form = Forms(user_id = current_user.id , form_title=form_name, form_url=form_url)
            db.session.add(form)
            db.session.commit() 
            break
    # create field object
    form = Forms.query.filter_by(form_url=form_url).first()
    form_id = form.id
    for elem in data["fields"].keys():
        name = elem
        field = Fields(form_id=form_id,type=data["fields"][elem][0], name=name)
        db.session.add(field)
        db.session.commit()
        
        if(data["fields"][elem][0] == 3 or data["fields"][elem][0] == 4):
        # create field_names   
            for i in range(1,len(data["fields"][elem])):
                subfield_names = Subfield_names(field_id = field.id, title = data["fields"][elem][i])
                db.session.add(subfield_names)
                db.session.commit()
    
    return 'done'

@app.route('/forms/<string:form_name>/<string:identifier>',methods=['GET'])
def form_url(form_name,identifier):
    form_url = os.getenv("BASE")+'/forms/'+form_name+'/'+identifier
    print(form_url)
    form = Forms.query.filter_by(form_url=form_url).first()
    form_fields = {}
    if form:
        fields = Fields.query.filter_by(form_id = form.id).all()
        for field in fields:
            form_fields[field.name] = [field.type]
            if(field.type == 3 or field.type==4):
                subfield_names = Subfield_names.query.filter_by(field_id = field.id)
                for subfield_name in subfield_names:
                    form_fields[field.name].append(subfield_name.title)
        form_data = {
            "form_name" : form.form_title,
            "fields" : form_fields
        }
        field_type_index = {
            0: 'text',
            1: 'number',
            2: 'tel',
            3: 'radio',
            4: 'checkbox'
        }
        return render_template('forms.html',form_data= form_data,index=field_type_index,form_id = form.id)            
    else:
        return ('not_found')

@app.route('/submitted', methods=['GET'])
def submitted():
    return render_template('form_submitted.html')


@app.route('/send_response', methods=['POST'])
def respond():
    data = request.form
    form_id = data.to_dict()['form_id']
    form = Forms.query.filter_by(id = form_id).first()

    response_event = Response_event(form_id = form_id)
    db.session.add(response_event)
    db.session.commit()

    data_list = list(data.lists())
    for elem in range(1,len(data_list)):
        field_data =  data_list[elem]
        field = Fields.query.filter_by(form_id = form.id).filter_by(name = field_data[0]).first()
        response = Responses(field_id= field.id, response_event_id = response_event.id)
        db.session.add(response)
        db.session.commit()
        for val in field_data[1]:
            if field.type == 1:
                number_val = Number_values(response_id = response.id, value = val)
                db.session.add(number_val)
                db.session.commit()               
            else:
                tex_val = Text_values(response_id = response.id, value = val)
                db.session.add(tex_val)
                db.session.commit()
            
    # whenever someone sends an response
    print(data_list)
    if form.google_sheets == 1:
        url =  os.getenv("BASE")+'/upload_response'
        body = list(request.form.lists())
        res = requests.post(url, json = body)

    return redirect('/submitted')

@app.route('/myforms', methods=['GET'])
def myforms():
    forms = Forms.query.filter_by(user_id = current_user.id).all()
    forms_data = []
    for form in forms:
        form_data = {}
        form_data['form_id'] = form.id
        form_data['form_title'] = form.form_title
        form_data['url'] = form.form_url
        form_data['sheets'] = form.google_sheets
        form_data['sheets_url'] = form.sheet_url

        forms_data.append(form_data)
    return render_template('myforms.html',forms_data= forms_data,client_id = os.getenv("CLIENT_ID"), client_sercret=os.getenv("CLIENT_SCRETE"))

@app.route('/show_data/<int:form_id>', methods=['GET'])
def showData(form_id):
    form_title = Forms.query.filter_by(id = form_id).first().form_title
    response_events = Response_event.query.filter_by(form_id = form_id).all()
    responses_all = []
    for response_event in response_events:
        response_this = {}
        responses = Responses.query.filter_by(response_event_id = response_event.id).all()
        for response in responses:
            response_question_data = Fields.query.filter_by(id = response.field_id).first()
            response_question = response_question_data.name
            response_type = response_question_data.type
            if(response_type == 1):
                response_answers_query = Number_values.query.filter_by(response_id = response.id).all()

            else:
                response_answers_query = Text_values.query.filter_by(response_id = response.id).all()
            response_answers = []
            for response_answer in response_answers_query:
                response_answers.append(response_answer.value)
            if(len(response_answers)==1):
                response_this[response_question] = response_answers[0]
            else:
                response_this[response_question] = response_answers
        responses_all.append(response_this)
    print(responses_all)
    return render_template('form_data.html',responses = responses_all, form_title = form_title)

@app.route('/get_form_data',methods=['POST'])
def get_form_data():
    form_id = request.json['form_id']
    form = Forms.query.filter_by(id = form_id).first()
    form_title = form.form_title
    fields = Fields.query.filter_by(form_id = form.id).all()
    response_events = Response_event.query.filter_by(form_id = form_id).all()
    responses_all = {}
    responses_all["form_title"] = form_title
    responses_all["form_id"] = form_id
    responses_all["user_id"] = form.user_id
    responses_all["head"] = []

    for field in fields:
        responses_all["head"].append(field.name)
    for i,response_event in enumerate(response_events):
        response_this = {}
        responses = Responses.query.filter_by(response_event_id = response_event.id).all()
        for response in responses:
            response_question_data = Fields.query.filter_by(id = response.field_id).first()
            response_question = response_question_data.name
            response_type = response_question_data.type
            if(response_type == 1):
                response_answers_query = Number_values.query.filter_by(response_id = response.id).all()

            else:
                response_answers_query = Text_values.query.filter_by(response_id = response.id).all()
            response_answers = []
            for response_answer in response_answers_query:
                response_answers.append(response_answer.value)
            if(len(response_answers)==1):
                response_this[response_question] = response_answers[0]
            else:
                response_this[response_question] = response_answers
            
        responses_all[str(i)]= response_this
    # print(responses_all)
    return responses_all

# google sheets integration
@app.route('/create_sheet',methods=['POST'])
def create_sheet():
    form_id = request.json['form_id']
    form = Forms.query.filter_by(id = form_id).first()
    form.google_sheets = 1
    db.session.commit()
    url = os.getenv("BASE")+"/get_form_data"
    body = {
        "form_id" : form_id
    }
    res = requests.post(url, json=body)
    form_data =  json.loads(res.text)

    url = os.getenv("BASE2")+"/sheetsAPI"
    body = form_data
    res = requests.post(url, json = body)
    
    sheet_url = res.text
    form.sheet_url = sheet_url
    db.session.commit()
    return 'done' 

@app.route('/upload_response',methods=['POST'])
def upload_response():
    data = request.json
    form_id = data[0][1][0]
    # print(data)
    user_id = Forms.query.filter_by(id=form_id).first().user_id
    data_payload = {
        'form_id' : form_id,
        "user_id" : user_id,
        'data' : {}
    }

    for i in range(1,len(data)):
        question_title = data[i][0]
        question_answers = data[i][1]
        if(len(question_answers) == 1):
            question_answer = question_answers[0]
        else:
            question_answer = ''
            for elem in question_answers:
                question_answer+=elem+','
        data_payload['data'][question_title] = question_answer

    url = os.getenv("BASE2")+"/add_sheet_data"
    body = data_payload
    res = requests.post(url, json = body)

    return '0'

