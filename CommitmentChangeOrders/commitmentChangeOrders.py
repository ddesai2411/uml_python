#!/usr/bin/env python
# coding: utf-8

from uml_python.uml_lib import ebAPI_lib as eb
import glob
import xmltodict
import pandas as pd
from uml_python.uml_lib import web_lib as web
from datetime import datetime

def checkUMLPO(POFiles, filepath):
    PO_dict = {'UMLPOFiles': [], 'nonUMLPOFiles': []}
    # UMLPOFiles = []
    # nonUMLPOFiles = []
    for i in range(len(POFiles)):
        if POFiles[i].startswith(filepath + 'Jaggaer_PO_L'):
            PO_dict['UMLPOFiles'].append(POFiles[i])
            # UMLPOFiles.append(POFiles[i])
        else:
            PO_dict['nonUMLPOFiles'].append(POFiles[i])
    return PO_dict

def getFieldFromSource(source, field):
    retval = ''
    if source != 'Field Not Found in XML' and field in source:
        # print(type(source),type(field))
        # retval = retval + source[field]
        retval = source[field]
        return retval
    else:
        retval = retval + 'Field Not Found in XML'
        return retval

def getCurrPONum(datasource):
    currPONum = getFieldFromSource(datasource, 'PONumber')
    return currPONum

def getPOCurrValue(datasource):
    # linecharge = getFieldFromSource(datasource, 'LineCharges')
    # unitprice = getFieldFromSource(linecharge, 'UnitPrice')
    # money = getFieldFromSource(unitprice, 'Money')
    # itemcost = getFieldFromSource(money, '#text')
    # return itemcost
    #
    linecharge = getFieldFromSource(datasource, 'LineCharges')
    extendedprice = getFieldFromSource(linecharge, 'ExtendedPrice')
    money = getFieldFromSource(extendedprice, 'Money')
    commitItemAmount = getFieldFromSource(money, '#text')
    return commitItemAmount

def getPOCurrCommitItemAmnt(datasource):
    linecharge = getFieldFromSource(datasource, 'LineCharges')
    extendedprice = getFieldFromSource(linecharge, 'ExtendedPrice')
    money = getFieldFromSource(extendedprice, 'Money')
    commitItemAmount = getFieldFromSource(money, '#text')
    return commitItemAmount

def getPOCurrUnitPrice(datasource):
    linecharge = getFieldFromSource(datasource, 'LineCharges')
    unitprice = getFieldFromSource(linecharge, 'UnitPrice')
    money = getFieldFromSource(unitprice, 'Money')
    itemcost = getFieldFromSource(money, '#text')
    return itemcost

def getCurrItemQuantity(datasource):
    quantity = getFieldFromSource(datasource, 'Quantity')
    return quantity

def getShippingCharges(datasource):
    linecharge = getFieldFromSource(datasource, 'LineCharges')
    shpChrges = getFieldFromSource(linecharge, 'ShippingCharges')
    TaxShippingHandling = getFieldFromSource(shpChrges, 'TaxShippingHandling')
    actualCharge = getFieldFromSource(TaxShippingHandling, 'TSHActualCharge')
    money = getFieldFromSource(actualCharge, 'Money')
    shippingCharge = getFieldFromSource(money, '#text')
    return shippingCharge

def getHandlingCharges(datasource):
    linecharge = getFieldFromSource(datasource, 'LineCharges')
    hndlngCharge = getFieldFromSource(linecharge, 'HandlingCharges')
    TaxShippingHandling = getFieldFromSource(hndlngCharge, 'TaxShippingHandling')
    actualCharge = getFieldFromSource(TaxShippingHandling, 'TSHActualCharge')
    money = getFieldFromSource(actualCharge, 'Money')
    handlingCharge = getFieldFromSource(money, '#text')
    return handlingCharge

def getTax1(datasource):
    linecharge = getFieldFromSource(datasource, 'LineCharges')
    taxField = getFieldFromSource(linecharge, 'Tax1')
    TaxShippingHandling = getFieldFromSource(taxField, 'TaxShippingHandling')
    actualCharge = getFieldFromSource(TaxShippingHandling, 'TSHActualCharge')
    money = getFieldFromSource(actualCharge, 'Money')
    tax1 = getFieldFromSource(money, '#text')
    return tax1

def getTax2(datasource):
    linecharge = getFieldFromSource(datasource, 'LineCharges')
    taxField = getFieldFromSource(linecharge, 'Tax2')
    TaxShippingHandling = getFieldFromSource(taxField, 'TaxShippingHandling')
    actualCharge = getFieldFromSource(TaxShippingHandling, 'TSHActualCharge')
    money = getFieldFromSource(actualCharge, 'Money')
    tax2 = getFieldFromSource(money, '#text')
    return tax2

def pad_string(string):
    if len(string) == 5:
        return string
    else:
        num_zeros = 5 - len(string)
        padded_string = '0' * num_zeros + string
        return padded_string

def getCOData(PONumber):
    CORecords = {}
    dataFields = {
        "selectedFields":["Project/CustomFields/FMP Number", "ProcessInstance/InstanceCounter", "Process/Prefix", "Process/ProcessName",
                          "ProcessInstance/Subject","ProcessInstance/DataFields/Commitment Number", "ProcessInstance/Status", "ProcessInstance/CurrentStepName"],
        "Filters":[
            {
                "Field" : "ProcessInstance/DataFields/Commitment Number",
                "Operation" : "=",
                "Value" : str(PONumber)
            }
        ]
    }
    theURL = 'https://api2.e-builder.net/api/v2/noncostProcesses/query?processprefix=CO'
    print('Getting CO data of PO Number: ', PONumber)
    COdata = eb.postTOAPI(theURL, dataFields)
    if 'records' in COdata:
        CORecord = COdata['records']
        if len(CORecord) > 0:
            for i in range(0,len(CORecord)):
                currFMP = CORecord[i]['Project']['CustomFields']['FMP Number']
                currProcessCounter = CORecord[i]['ProcessInstance']['InstanceCounter']
                currCommitmentNumber = CORecord[i]['Process']['Prefix'] + ' - ' + pad_string(CORecord[i]['ProcessInstance']['InstanceCounter'])
                currPSPONumber = CORecord[i]['ProcessInstance']['DataFields']['Commitment Number']
                currUniqueIdentifier = currPSPONumber + ' - ' + currCommitmentNumber
                currStatus = CORecord[i]['ProcessInstance']['Status']
                currStepName = CORecord[i]['ProcessInstance']['CurrentStepName']
                CORecords[currUniqueIdentifier] = {"FMP Number": currFMP,
                                                    "Process Counter": currProcessCounter,
                                                    "Commitment Number": currCommitmentNumber,
                                                    "PeopleSoft PO Number": currPSPONumber,
                                                    "Status": currStatus,
                                                    "Step Name": currStepName,
                                                    "Notes": ""}
    # print(CORecords)
        return CORecords

def getPCOData(PONumber):
    PCORecords = {}
    dataFields = {
        "selectedFields":[ "Project/CustomFields/FMP Number", "ProcessInstance/InstanceCounter", "Process/Prefix",
                           "ProcessInstance/Subject", "ProcessInstance/Status", "ProcessInstance/CurrentStepName", "ProcessInstance/DataFields/PeopleSoft PO#"],
        "Filters":[
            {
                "Field" : "ProcessInstance/DataFields/PeopleSoft PO#",
                "Operation" : "=",
                "Value" : PONumber
            }
        ]
    }
    theURL = 'https://api2.e-builder.net/api/v2/noncostprocesses/query?processprefix=PCO'
    print('Getting PCO data of PO Number: ', PONumber)
    PCOdata = eb.postTOAPI(theURL, dataFields)
    if 'records' in PCOdata:
        PCORecord = PCOdata['records']
        if len(PCORecord) > 0:
            for i in range(0,len(PCORecord)):
                currFMP = PCORecord[i]['Project']['CustomFields']['FMP Number']
                currProcessCounter = PCORecord[i]['ProcessInstance']['InstanceCounter']
                currCommitmentNumber = PCORecord[i]['Process']['Prefix'] + ' - ' + pad_string(PCORecord[i]['ProcessInstance']['InstanceCounter'])
                currPSPONumber = PCORecord[i]['ProcessInstance']['DataFields']['PeopleSoft PO#']
                currUniqueIdentifier = currPSPONumber + ' - ' + currCommitmentNumber
                currStatus = PCORecord[i]['ProcessInstance']['Status']
                currStepName = PCORecord[i]['ProcessInstance']['CurrentStepName']
                PCORecords[currUniqueIdentifier] = {"FMP Number": currFMP,
                                                    "Process Counter": currProcessCounter,
                                                    "Commitment Number": currCommitmentNumber,
                                                    "PeopleSoft PO Number": currPSPONumber,
                                                    "Status": currStatus,
                                                    "Step Name": currStepName,
                                                    "Notes": ""}
        # print(PCORecords)
        return PCORecords

def getCONData(FMP, ChangedPOs):
    CONRecords = {}
    dataFields = {
        "selectedFields":["Project/CustomFields/FMP Number", "ProcessInstance/InstanceCounter", "Process/Prefix",
                          "ProcessInstance/Subject", "ProcessInstance/Status", "ProcessInstance/CurrentStepName", "ProcessInstance/DataFields/PS PO Number",
                          ],
        "Filters":[
            {
                "Field" : "Project/CustomFields/FMP Number",
                "Operation" : "=",
                "Value" : FMP
            }
        ]
    }
    theURL = 'https://api2.e-builder.net/api/v2/noncostprocesses/query?processprefix=CO-N'
    print('Getting CON data with FMP Number: ', FMP)
    CONdata = eb.postTOAPI(theURL, dataFields)
    # print(CONdata)
    # return CONdata
    CONRecord = CONdata['records']
    if len(CONRecord) > 0:
        for i in range(0,len(CONRecord)):
            currPSPONumber = CONRecord[i]['ProcessInstance']['DataFields']['PS PO Number']
            if currPSPONumber in ChangedPOs:
                currFMP = CONRecord[i]['Project']['CustomFields']['FMP Number']
                currProcessCounter = CONRecord[i]['ProcessInstance']['InstanceCounter']
                currCommitmentNumber = CONRecord[i]['Process']['Prefix'] + ' - ' + pad_string(CONRecord[i]['ProcessInstance']['InstanceCounter'])
                currUniqueIdentifier = currPSPONumber + ' - ' + currCommitmentNumber
                currStatus = CONRecord[i]['ProcessInstance']['Status']
                currStepName = CONRecord[i]['ProcessInstance']['CurrentStepName']
                CONRecords[currUniqueIdentifier] = {"FMP Number": currFMP,
                                                    "Process Counter": currProcessCounter,
                                                    "Commitment Number": currCommitmentNumber,
                                                    "PeopleSoft PO Number": currPSPONumber,
                                                    "Status": currStatus,
                                                    "Step Name": currStepName,
                                                    "Notes": ""}
        return CONRecords

def dataToDF(data,dataFrame):
    if data!= None:
        if len(data)!=0:
            for i in data:
                df = pd.DataFrame(data=data[i], index=[1])
                dataFrame = pd.concat([dataFrame,df])
    return dataFrame

def padstr(s):
    retVal = s
    if len(s) == 1:
        retVal = "0" + retVal
    return retVal

def tstamper():
    now = datetime.now()
    mo = padstr(str(now.month))
    d = padstr(str(now.day))
    h = padstr(str(now.hour))
    mi = padstr(str(now.minute))
    s = padstr(str(now.second))
    tstamp = str(now.year)[2:] + mo + d + "_" + h + mi + s
    return (tstamp)

def makeHTMLHead():
    htmlHead = "<!DOCTYPE html>\n<html>\n<head>\n<title>Commitment Change Orders</title>\n</head>\n"
    return htmlHead

def makeHTMLStyle():
    htmlStyle = "<style>\n"
    htmlStyle += "table {font-family: Open Sans, sans-serif; border-collapse: collapse; width: 100%; margin-bottom: 20px;}\n"
    htmlStyle += "td, th {border: 1px solid #ddd; padding: 8px; text-align: left;}\n"
    htmlStyle += "th {background-color: #0463a7; color: white;}\n"
    htmlStyle += "tr:nth-child(even) {background-color: #f9f9f9;}\n"
    htmlStyle += "body{ font-family: 'Open Sans',sans-serif;}\n"
    htmlStyle += "</style>\n"
    return htmlStyle

def makeHTMLbody(tableData):
    now = datetime.now()
    htmlBody = "<body>\n"
    htmlBody += "<h2>Commitment Change Orders</h2>\n"
    htmlBody += tableData
    htmlBody += "<p> Last Updated on: <i>" + str(now) + "</i></p>"
    htmlBody += "\n</body>\n</html>"
    return htmlBody

def getHTML(oDir,htmlData):
    changeOrderRecords.to_excel(oDir + "CommitmentChangeOrders.xlsx", index=False)
    html_file = open(oDir + 'CommitmentChangeOrders.html', 'w')
    html_file.write(htmlData)
    return htmlData

# ## Get POs From E-Builder
ebProjs = eb.get_Projects()
activePOs = eb.get_activePOs(ebProjs)
#activePOs['L001138273']
ebPOs = {k: v['Value'] for k, v in activePOs.items()}
del ebPOs[None]
ebPOs = dict(sorted(ebPOs.items()))

# ## Get POs From Buyways XML Files
# In[25]:

theDir = "fromBW/"
POFiles = glob.glob(theDir + "*_PO_*.xml")
PO_dict = checkUMLPO(POFiles, theDir)
UMLPOFiles = PO_dict['UMLPOFiles']
BWPOs = {}
for f in UMLPOFiles:
    theFile = open(f, encoding='utf-8')
    # print(count,f)
    xml_content = theFile.read()
    bwdata = xmltodict.parse(xml_content, encoding='utf-8')
    headerData = bwdata['PurchaseOrderMessage']['PurchaseOrder']['POHeader']
    POlinedata = bwdata['PurchaseOrderMessage']['PurchaseOrder']['POLine']
    currPONumber = getCurrPONum(headerData)
    #print(currPONumber)
    if type(POlinedata) == dict:
        currExtendedPrice = getPOCurrCommitItemAmnt(POlinedata)
        currUnitQuantity = float(getCurrItemQuantity(POlinedata))
        currUnitPrice = float(getPOCurrUnitPrice(POlinedata))
        if currExtendedPrice == 'Field Not Found in XML':
            currTotalPrice = currUnitPrice * currUnitQuantity
        else:
            currTotalPrice = float(currExtendedPrice)
        currShippingCharges = float(getShippingCharges(POlinedata))
        currHandlingCharges = float(getHandlingCharges(POlinedata))
        currTax1 = float(getTax1(POlinedata))
        currTax2 = float(getTax2(POlinedata))
        currOtherCharges = currShippingCharges + currHandlingCharges + currTax1 +currTax2
        currTotalCost = currTotalPrice + currOtherCharges
        currTotalCost = float('{:.2f}'.format(float(currTotalCost)))
        BWPOs[currPONumber] = currTotalCost
        # print('----------------------')
    else:
        currTotalCost = 0
        for k in POlinedata:

            currExtendedPrice = getPOCurrCommitItemAmnt(k)
            currUnitQuantity = float(getCurrItemQuantity(k))
            currUnitPrice = float(getPOCurrUnitPrice(k))
            if currExtendedPrice == 'Field Not Found in XML':
                currTotalPrice = currUnitPrice * currUnitQuantity
            else:
                currTotalPrice = float(currExtendedPrice)
            currShippingCharges = float(getShippingCharges(k))
            currHandlingCharges = float(getHandlingCharges(k))
            currTax1 = float(getTax1(k))
            currTax2 = float(getTax2(k))
            currOtherCharges = currShippingCharges + currHandlingCharges + currTax1 +currTax2
            currLineTotalCost = currTotalPrice + currOtherCharges
            #BWPOs[currPONumber] = currLineTotalCost
            # print(getPOCurrValue(k))
            currTotalCost += float(currLineTotalCost)
            currTotalCost = float('{:.2f}'.format(float(currTotalCost)))
        BWPOs[currPONumber] = currTotalCost
    # print(currPONumber, ',', currItemCost)
BWPOs = dict(sorted(BWPOs.items()))

# ## Check Corresponding Costs in Ebuilder and Buyways

count = 0
ChangedPOs = {}
print('PONumber   - Ebuilder - Buyways XML')
for i in ebPOs:
    if i in BWPOs:
        BWPOs[i] = float('{:.2f}'.format(float(BWPOs[i])))
        #print(i, '-' ,ebPOs[i], '-' ,BWPOs[i])
        if BWPOs[i] == ebPOs[i]:
            count+=1
        else:
            print(i, '-' ,ebPOs[i], '-' ,BWPOs[i])
            ChangedPOs[i] = BWPOs[i]
            #count+=1
# ChangedPOs
CPO_FMPs = {}
for i in ChangedPOs:
    CPO_FMPs[i] = activePOs[i]['FMP'].decode('utf-8')
#CPO_FMPs

changeOrderRecords = pd.DataFrame()
for i in ChangedPOs:
    # PCOData = getPCOData(i)
    COData = getCOData(i)
    # changeOrderRecords = dataToDF(PCOData,changeOrderRecords)
    changeOrderRecords = dataToDF(COData,changeOrderRecords)
for i in CPO_FMPs:
    # print(i)
    CONData = getCONData(CPO_FMPs[i],ChangedPOs)
    changeOrderRecords = dataToDF(CONData,changeOrderRecords)

print(changeOrderRecords)
CO_PWB = changeOrderRecords[changeOrderRecords['Step Name'] == 'Pending Buyways Approval']
print(CO_PWB)
# currTime = web.tstamper()

COTableData = changeOrderRecords.to_html(index=False)
CO_PWBTableData = CO_PWB.to_html(index = False)
twoTables = "<h3>Commitment Change Orders - Pending Buyways Approval</h3>" + CO_PWBTableData
twoTables += "<br><hr><h3>Other Commitment Change Orders</h3>" + COTableData + "<hr>"

head = makeHTMLHead()
style = makeHTMLStyle()
body = makeHTMLbody(twoTables)
htmlData = head + style + body

oDir = 'outputfiles\\'
getHTML(oDir,htmlData)

# get_ipython().system('jupyter nbconvert --to script commitmentChangeOrders.ipynb')
