#!/usr/bin/env python
import requests, oauth2, json

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

def get_ebToken():
    payload = {
        'grant_type': 'password',
        'username': "KamalYeshodharShastry_Gattu@uml.edu",
        'password': "72ca0b6cfa174807804d807b5ced84e6"
    }

    r = requests.post("https://api2.e-builder.net/api/v2/authenticate",
                      headers={"Content-Type": "application/x-www-form-urlencoded"},
                      data=payload)

    reqDict = json.loads(r.content)
    ebTok = reqDict["access_token"]
    return ebTok

ebTok = get_ebToken()

def API_connect_get_data(module):
    print("Conncting to the API to get: " + module)
    modStr = "https://api2.e-builder.net/api/v2/" + module + "?$format=json"
    print(modStr)
    #ebTok = get_ebToken()
    response = requests.get(modStr, auth = BearerAuth(ebTok))
    mystr = response.content
    data = json.loads(mystr)
    return data

"""
1. Get list of Projects by connecting to the API
2. From the Projects extract the 'records' attribute.
3. Iterate through records to get Project ID
    4. Using Project IDs get Custom Fields of each Project.
    5. Custom Fields are present in the column 'details' pull data from details 
    attribute and make a dictionary of corresponding custom field and its value.
    6.Create an empty dictionary; merge and store data in records and corresponding
     custom field.
    7.Consolidate entire data in a list of dictionaries containing Project attribute
     and its corresponding value 
"""
def get_project_all_data():
    records = API_connect_get_data("Projects")['records']
    project_all_data = []
    for i in range(0,len(records)):
        project_data = records[i]
        project_id = records[i]["projectId"]
        theURL = "https://api2.e-builder.net/api/v2/Projects/" + project_id + "/customfields"
        response = requests.get(theURL, auth=BearerAuth(ebTok))
        custom_fields_raw = json.loads(response.content)
        custom_fields_details = custom_fields_raw['details']
        dict_custom_fields_details = {}
        for j in range(len(custom_fields_details)):
            dict_custom_fields_details[custom_fields_details[j]['name']] = custom_fields_details[j]['value']
        project_data = project_data | dict_custom_fields_details
        project_all_data.append(project_data)
    return project_all_data

def get_active_project_all_data():
    records = API_connect_get_data("Projects")['records']
    active_project_all_data = []
    for i in range(0,len(records)):
        if records[i]['status'] == "Active" or records[i]["status"] == "TD Active":
            project_data = records[i]
            project_id = records[i]["projectId"]
            theURL = "https://api2.e-builder.net/api/v2/Projects/" + project_id + "/customfields"
            response = requests.get(theURL, auth=BearerAuth(ebTok))
            custom_fields_raw = json.loads(response.content)
            custom_fields_details = custom_fields_raw['details']
            dict_custom_fields_details = {}
            for j in range(len(custom_fields_details)):
                dict_custom_fields_details[custom_fields_details[j]['name']] = custom_fields_details[j]['value']
            project_data = project_data | dict_custom_fields_details
            active_project_all_data.append(project_data)
    return active_project_all_data

def get_budget_all_data():
    records = API_connect_get_data("Budgets")['records']
    budget_all_data = []
    for i in range(0,len(records)):
        budget_data = records[i]
        budget_id = records[i]["budgetId"]
        theURL = "https://api2.e-builder.net/api/v2/Budgets/" + budget_id + "/customfields"
        response = requests.get(theURL, auth=BearerAuth(ebTok))
        custom_fields_raw = json.loads(response.content)
        custom_fields_details = custom_fields_raw['details']
        dict_custom_fields_details = {}
        for j in range(len(custom_fields_details)):
            dict_custom_fields_details[custom_fields_details[j]['name']] = custom_fields_details[j]['value']
        budget_data = budget_data | dict_custom_fields_details
        budget_all_data.append(budget_data)

    return budget_all_data
