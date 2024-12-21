#!/usr/bin/env python
# coding: utf-8
from uml_lib import ebAPI_lib as eb
from datetime import datetime

#Code WorkFlow -

#Fetching Required data with reference to old Monthly Status Code.
#Storing the data of all the active Projects in a dictionary
#The Dictionary contains Project Names as Keys and each Project Name will have a Dictionary as Value which has fields required for Monthly Status Export.

#To Post data for a particular Project to API, call getMoStatData() method with Project Name as parameter. This returns the required fields for Monthly Status report for that particular Project.

#The method to Post the data to API takes URL of the endpoint and the above fetched data as parameters.

def get_monthYear():
    retVal = ""
    months = ["Unknown","January","Febuary","March","April","May","June",
          "July","August","September","October","November","December"]
    now = datetime.now()
    if now.month == 12:
        mo = "January"
        retVal = mo + " " + str(now.year + 1)
    else:
        mo = months[now.month+1]
        retVal = mo + " " + str(now.year)
    return(retVal)

def convertDate(ut):
    timeStr = datetime.fromisoformat(ut).strftime('%m.%d.%y')
    return timeStr

def get_TPC(budget_data, currProjID):
    currTPC = -1
    a = len(budget_data)

    for b in range(0,a):
        if budget_data[b]["projectId"] == currProjID:
            #print ">>>>", budget_data[b]["ProjectID"], currProjID
            #print "!!!!!!",budget_data[b]["Custom_Total_Current_Working_EstimateTPC"]
            try:
                currTPC = budget_data[b]["Total Current Working Estimate/TPC"]
            except:
                currTPC = -1
            break

    if currTPC == -1:
        currTPC = None
    #print ("RETURNING ............................................... TPC", currTPC)
    return currTPC

def checkLead(dept, PM, Planner):
    retVal = True
    # we don't want to output if the lead department's person is TBD or blank
    if dept == "Project Management":
        if PM == "TBD" or PM == "":
            retVal = False
    elif dept == "Planning":
        if Planner == "TBD" or Planner == None:
            retVal = False
    else:
        "Dept is not PM or Planning", dept
    return retVal



def getMoStatData(projectName):
    project_data = eb.get_project_allData()
    print('Projects data imported')
    budget_data = eb.get_budget_all_data()
    print('Budgets data imported')
    moStatDict = {}
    currProjNames = []
    currFMPs = []
    currPrevStatusComments = []
    currLeadDepts = []
    currProjHealths = []
    currPhases = []
    currSuccessorProjs = []
    currEnablingProjs = []
    currStartDates = []
    currEndDates = []
    currSteps = []
    currTPCs = []
    currMonthYears = []
    currPMs = []
    currPlanners = []
    ignoreCounts = 0

    for j in range(0,len(project_data)):
        currMonthYear = get_monthYear()
        currProjName = project_data[j]["name"]
        #print(currProjName)
        currFMP = project_data[j]["FMP Number"]
        currStatus = project_data[j]["status"] # Project Status
        #print ">>>>", currProjName, currFMP, currStatus

        currLeadDept = project_data[j]["FM Department Lead"]
        currStatusComments = project_data[j]["Status Comments"] #newliner here?
        currProjID = project_data[j]["projectId"] # Need this for lookup in Budget Data
        currPM = project_data[j]["Project Manager"]
        currPlanner = project_data[j]["Project Planner"]
        currPhase = project_data[j]["Project Phase"]
        if currLeadDept == "Planning" or currLeadDept == "Project Management":
            reportable = True # FIS or O&S, don't report
            definedLead = checkLead(currLeadDept, currPM, currPlanner)
        else:
            reportable = False
        if reportable:
            if currStatus == "Active" or currStatus == "TD Active" or currProjName == 'zzTEST Integration' or currProjName == '*TEST - PGB Test':
                #print (">>>>", currPhase, currPhase[:2])
                ignoreCounts += 1
                if currPhase[:2] != "08":
                    #print "Not 08", currPhase
                    if definedLead == True:
                        #print currFMP
                        currTPC = get_TPC(budget_data, currProjID)

                        if currLeadDept == "Project Management":
                            currStep = "PM Review"
                        elif currLeadDept == "Planning":
                            currStep = "Planning Review"
                        else:
                            currStep = "IGNORE: no updates"
                        #print currStatus, currTPC,currLeadDept,currStep
                        if currStep != "IGNORE: no updates":
                            if project_data[j]["Project Health"] == None:
                                currProjHealth = "TBD"
                            else:
                                currProjHealth = project_data[j]["Project Health"]
                            try:
                                currSuccessorProjects = project_data[j]["Successor Projects"]
                            except:
                                currSuccessorProjects = "None"
                            try:
                                currEnablingProjects = project_data[j]["Enabling Projects"]
                            except:
                                currEnablingProjects = "None"
                            currStartDate = convertDate(project_data[j]["startDate"])
                            currTargetDate = convertDate(project_data[j]["targetDate"])


                            currProjNames.append(currProjName)
                            currFMPs.append(currFMP)
                            currPrevStatusComments.append(currStatusComments)
                            currLeadDepts.append(currLeadDept)
                            currProjHealths.append(currProjHealth)
                            currPhases.append(currPhase)
                            currSuccessorProjs.append(currSuccessorProjects)
                            currEnablingProjs.append(currEnablingProjects)
                            currStartDates.append(currStartDate)
                            currEndDates.append(currTargetDate)
                            currSteps.append(currStep)
                            currTPCs.append(currTPC)
                            currMonthYears.append(currMonthYear)
                            currPMs.append(currPM)
                            currPlanners.append(currPlanner)
                        else:
                            #print ("Step was no updates?", currFMP, currProjName)
                            ignoreCounts += 1
                            #retVal["No Updates"] += 1
                else:
                    #print "Lead is not defined (TBD or None)"
                    ignoreThis = 1
                    ignoreCounts += 1
                    #print ("Undefined lead", currFMP, currProjName, currLeadDept, currPM, currPlanner)
            else:
                ignoreCounts += 1
                #print ("Ignoring - not Active or TD Active", currFMP, currProjName)
                #retVal["Not Active"] += 1

    for i in range(len(currProjNames)):
        moStatDict[currProjNames[i]] = {
            'FMP Number': currFMPs[i],
            'Previous Status Comments': currPrevStatusComments[i],
            'FM Department Lead': currLeadDepts[i],
            'Project Health': currProjHealths[i],
            'Project Phase': currPhases[i],
            'Successor Projects': currSuccessorProjs[i],
            'Enabling Projects': currEnablingProjs[i],
            'Current Project Start Date': currStartDates[i],
            'Current Project End Date': currEndDates[i],
            'Step': currSteps[i],
            'Total Current Working Estimate/TPC': currTPCs[i],
            'Monthly Status Report (Month of Report)': currMonthYears[i],
            'Project Manager': currPMs[i],
            'Planner': currPlanners[i]}

    projMoStatData = moStatDict[projectName]
    data =\
        {
        "options": {
            "projectIdentifier": "ProjectName",
            "processPrefix": "STAT",
            "importMode": "Entity"
        },
        "data": [
            {
                    "projectIdentifier": projectName,
                    "processDataFields": {
                        "FMP Number" : projMoStatData['FMP Number'],
                        "Status Comments" :projMoStatData['Previous Status Comments'],
                        "Project Health" : projMoStatData['Project Health'],
                        "Project Phase" : projMoStatData['Project Phase'],
                        "Successor Projects" : projMoStatData['Successor Projects'],
                        "Enabling Projects" : projMoStatData['Enabling Projects'],
                        "startDate" : projMoStatData['Current Project Start Date'],
                        "targetDate" : projMoStatData['Current Project End Date'],
                        "Step" : projMoStatData['Step'],
                        "Total Current Working Estimate" : projMoStatData['Total Current Working Estimate/TPC'],
                        "Monthly Status" : projMoStatData['Monthly Status Report (Month of Report)'],
                        "Project Manager" : projMoStatData['Project Manager'],
                        "Planner" : projMoStatData['Planner']

                },
                    "status": "Pending"
            }
        ]
    }
    return data
    #return moStatDict

#data = getMoStatData('zzTEST Integration')
data = getMoStatData('*TEST - PGB Test')
theURL = 'https://api2.e-builder.net/api/v2/noncostprocesses/import'

eb.postTOAPI(theURL,data)

