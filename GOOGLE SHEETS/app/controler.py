from flask import Flask, request
from flask import current_app as app
from flask_login import login_user,current_user
from .models import Sheets, Users
import requests, json, string
from .database import db
import os


@app.route('/sheetsAPI',methods=['POST'])
def sheets_api():
    data = request.json
    form_id = data['form_id']
    user_id = data['user_id']
    form_title = data['form_title']
    sheet = Sheets.query.filter_by(form_id=form_id).first()
    if(sheet):
        return 'no'
    else:
        user = Users.query.filter_by(id = user_id).first()
        access_token = user.access_token
        url = "https://sheets.googleapis.com/v4/spreadsheets"
        data_google ={
                    'properties': {
                'title': form_title
            }
        }

        headers = {
            "Authorization" : "Bearer "+access_token
        }
        response = requests.post(url, headers=headers, json=data_google)
        res = response.json()

        sheet_url = res['spreadsheetUrl']
        sheet_id = res['spreadsheetId']
        newsheet = Sheets(form_id=form_id,sheet_url=sheet_url,user_id=user_id,sheet_id=sheet_id)
        db.session.add(newsheet)
        db.session.commit()

    
            # spreadsheet data push
        head_data = data['head']
        range_letter = string.ascii_uppercase[len(head_data)-1] 
        range_val = 'A1:{}1'.format(range_letter)
        url = 'https://sheets.googleapis.com/v4/spreadsheets/{}/values/{}:append?valueInputOption=RAW'.format(sheet_id,range_val)

        data_spreadsheet = {
            'values' : [
                head_data
            ]
        }

        # headers = {
        #     "Authorization" : "Bearer "+access_token
        # }

        response = requests.post(url, headers=headers, json=data_spreadsheet)
        res = response.json()

        final_data = []
        for field in data.keys():
            if(field.isnumeric()):
                field_data = data[field] 
                field_data_manipulated = [] 
                for elem in field_data.values():
                    if isinstance(elem, list):
                        str = ''
                        for element in elem:
                            str+=element+','
                        field_data_manipulated.append(str)
                    else:
                        field_data_manipulated.append(elem)
                final_data.append(field_data_manipulated)
        
        for field in final_data:
            data_spreadsheet = {
                'values' : [
                    field
            ]
            }
            response = requests.post(url, headers=headers, json=data_spreadsheet)
            res = response.json()
    print(data)
    return sheet_url


# google login
@app.route('/redir', methods=['GET'])
def google_redirect():
    code = request.args.get('code')
    # getting the access token
    url = "https://oauth2.googleapis.com/token"
    body = {
        "client_id" : os.getenv('CLIENT_ID'),
        "client_secret" : "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",
        "code" : code,
        "grant_type" : "authorization_code",
        "redirect_uri" : "http://localhost:8080/redir",
    }

    # get access token
    res = requests.post(url, json = body)
    data =  json.loads(res.text)
    access_token = data["access_token"]
    id_token = data["id_token"]
    refresh_token = data["refresh_token"]


    # # getting user information 
    url = "https://oauth2.googleapis.com/tokeninfo?id_token={}".format(id_token)
    res = requests.post(url, json = body)
    data =  json.loads(res.text)
    email = data["email"]
    id = data["sub"]
    
    user = Users.query.filter_by(id=id).first()
    if user:
        user.access_token = access_token
        user.refresh_token = refresh_token
        db.session.add(user)
        db.session.commit()
        login_user(user)
    else:
        newuser = Users(access_token=access_token,refresh_token=refresh_token,id=id)
        db.session.add(newuser)
        db.session.commit()
        login_user(newuser)
    return "<script>window.onload = window.close();</script>"


@app.route('/add_sheet_data',methods=['POST'])
def add_sheets_data():
    data = request.json
    form_id = data['form_id']
    user_id = data['user_id']
    form_data = data['data']
    head_data = list(form_data.keys())
    range_letter = string.ascii_uppercase[len(head_data)-1] 
    range_val = 'A1:{}1'.format(range_letter)
    values = list(form_data.values())
    print(values)
    access_token = Users.query.filter_by(id = user_id).first().access_token
    sheet_id = Sheets.query.filter_by(form_id=form_id).first().sheet_id
    url = 'https://sheets.googleapis.com/v4/spreadsheets/{}/values/{}:append?valueInputOption=RAW'.format(sheet_id,range_val)
    # print(sheet_id)
    data_spreadsheet = {
        'values' : [
            values
        ]
    }

    headers = {
        "Authorization" : "Bearer "+access_token
    }
    response = requests.post(url, headers=headers, json=data_spreadsheet)
    res = response.json()
    # print(res)
    return '0'
