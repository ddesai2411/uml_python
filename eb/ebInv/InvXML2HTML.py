#!/usr/bin/env python
# coding: utf-8

# IMPORTANT: Make sure that you have necessary Styling (table3.css) and Scripting(table3.js) files in the directory where outputs will be saved

#import eb.ebAPI_lib as eb
import xmltodict
from uml_python.uml_lib import web_lib as web
import os, shutil, glob

def getFieldFromSource(source,field):
    retval = ''
    if source != 'Field Not Found in XML' and field in source:
        #print(type(source),type(field))
        #retval = retval + source[field]
        retval = source[field]
        return retval
    else:
        retval = retval + 'Field Not Found in XML'
        return retval

def get_customField(theData,theField):
    retVal = "NOT FOUND"

    for f in theData:
        #print "???", f["@name"]
        if f["@name"] == theField:
            try:
                retVal =  f["CustomFieldValue"]["Value"]
            except:
                retVal = "MULTIPLE"
                #for g in f:
                #    print( "\tget_customField", g)
    #print(retVal)
    return retVal

def checkFMP(theFMP):
    retVal = True
    for c in theFMP:
        if c not in "0123456789":
            retVal = False
            break
    return retVal

def get_FMPfromPSproject(psProj):
    retVal = "FMP NOT FOUND"
    #print (">>>>", psProj)

    iFMP = psProj.find("FMP")
    iDash = psProj.find("-")
    if iFMP == -1:
        retVal = "FMP STRING NOT FOUND"
    elif iDash == -1:
        retVal = "FMP: DASH NOT FOUND"
    else:
        #print( "get_FMP >>>>", psProj[(iFMP+3):iDash])
        currFMP = psProj[(iFMP+3):iDash]
        if currFMP[0] == "0":
            currFMP = currFMP[1:]
            #print ">>>>", currFMP
        if len(currFMP) != 6:
            retVal = "FMP: LENGTH OF STRING IS WRONG"
        elif checkFMP(currFMP):
            retVal = currFMP
        else:
            retVal = "FMP: NON-NUMERIC CHARACTER"
    return retVal

#def getCurrPONum(datasource):
#    currPONum =  getFieldFromSource(datasource, 'PONumber')
#    return currPONum

def getCurrPONum(datasource):
    currOriginCode = get_customField(datasource["CustomFieldValueSet"],"Origin Code")
    currExtReq = get_customField(datasource["CustomFieldValueSet"],"External Req #")
    if currOriginCode == "LEB":
        currPONum = currExtReq[:2]
    else:
        currPONum =  getFieldFromSource(datasource,'PONumber')
    return currPONum


def getInvoiceNum(datasource):
    currInvoiceNum = getFieldFromSource(datasource, 'InvoiceNumber')
    return currInvoiceNum

def getInvoiceAmount(datasource):
    currInvoiceAmnt = getFieldFromSource(datasource, 'UnitPrice')
    return currInvoiceAmnt

def getSchedulePaidDate(datasource):
    currSchedulePaidDate = getFieldFromSource(datasource, 'DueDate')
    return currSchedulePaidDate

def checkUMLPAYAP(invFiles, theDir):
    PAYAP_FilesDir = theDir + 'PAYAP_Files'
    Invoice_dict = {'PAYAP Files': [], 'Non PAYAP Files': []}
    for f in invFiles:
        # print(f)
        PAYAP_flag = f.find("PAYAP")
        if PAYAP_flag != -1:
            try:
                os.mkdir(PAYAP_FilesDir)
            except:
                print("Directory Exists")
            try:
                shutil.move(f, PAYAP_FilesDir + "/" + f.replace(theDir, ''))
            except:
                print("File exists")
            Invoice_dict['PAYAP Files'].append(f)
        else:
            Invoice_dict['Non PAYAP Files'].append(f)
            # isPAYAP +=1
    return Invoice_dict

def ParseXMLInvoices(InvoiceFiles):
    currPONums = []
    currFMPs = []
    currInvoiceNums = []
    currInvoiceAmounts = []
    currPAYAPFlags = []
    currSchedulePaidDates= []
    count = 0
    for f in InvoiceFiles:
        isPAYAP = f.find("PAYAP")
        if isPAYAP != -1:
            currPAYAPFlag = "Yes"
        else:
            currPAYAPFlag = "No"
        theFile = open(f,encoding='utf-8')
        #print(theFile)
        xml_content = theFile.read()
        bwdata = xmltodict.parse(xml_content,encoding='utf-8')
        headerData = bwdata['BuyerInvoiceExportMessage']['Invoice']['InvoiceHeader']
        if 'InvoiceLine' in bwdata['BuyerInvoiceExportMessage']['Invoice']:
            Invlinedata = bwdata['BuyerInvoiceExportMessage']['Invoice']['InvoiceLine']
            #print(type(InvoiceLinedata))
            #print(headerData["InvoiceNumber"])
            if type(Invlinedata) == dict:
                currPONumber = getCurrPONum(Invlinedata) #getFieldFromSource(InvoiceLinedata,'PONumber')
                if currPONumber[0] != 'L':
                    print(currPONumber + 'is not a UML PO')
                else:
                    currPSproject = get_customField(Invlinedata["CustomFieldValueSet"],"Project")
                    #currPSproject = xml_lib.get_customField(InvoiceLinedata["CustomFieldValueSet"],"Project")
                    currFMP = get_FMPfromPSproject(currPSproject)
                    currInvoiceNum = getInvoiceNum(headerData)
                    currInvoiceAmount = getInvoiceAmount(Invlinedata)
                    currSchedulePaidDate = getSchedulePaidDate(headerData)

                    currPONums.append(currPONumber)
                    currFMPs.append(currFMP)
                    currInvoiceNums.append(currInvoiceNum)
                    currInvoiceAmounts.append(currInvoiceAmount)
                    currPAYAPFlags.append(currPAYAPFlag)
                    currSchedulePaidDates.append(currSchedulePaidDate)
            else:
                for k in Invlinedata:
                    currPONumber = getCurrPONum(k) #getFieldFromSource(InvoiceLinedata,'PONumber')
                    if currPONumber[0] != 'L':
                        print(currPONumber + 'is not a UML PO')
                    else:
                        currPSproject = get_customField(k["CustomFieldValueSet"],"Project")
                        #currPSproject = xml_lib.get_customField(InvoiceLinedata["CustomFieldValueSet"],"Project")
                        currFMP = get_FMPfromPSproject(currPSproject)
                        currInvoiceNum = getInvoiceNum(headerData)
                        currInvoiceAmount = getInvoiceAmount(k)
                        currSchedulePaidDate = getSchedulePaidDate(headerData)

                        currPONums.append(currPONumber)
                        currFMPs.append(currFMP)
                        currInvoiceNums.append(currInvoiceNum)
                        currInvoiceAmounts.append(currInvoiceAmount)
                        currPAYAPFlags.append(currPAYAPFlag)
                        currSchedulePaidDates.append(currSchedulePaidDate)

            inv_data = {'PO Numbers': currPONums,
                    'FMP Numbers': currFMPs,
                    'Invoice Numbers': currInvoiceNums,
                    'Invoice Amounts': currInvoiceAmounts,
                    'Is PAYAP?': currPAYAPFlags,
                    'Schedule Paid Date': currSchedulePaidDates}
    return inv_data

#theDir = "/Users/kysgattu/FIS/CostXML/testdata/"
theDir = "B:\\fromBW\\"
InvoiceFiles = glob.glob(theDir + "*_Invoice_*.xml")

inv_data = ParseXMLInvoices(InvoiceFiles)
rows = len(inv_data['PO Numbers'])
headerRow = inv_data.keys()
currTime = web.tstamper()

oDir = "B:\\dailyImports\\fromXML\\"

web.copyFiles(oDir)
html_file = open(oDir + 'invoice-log.html', 'w')


htmldata = web.makeHTMLtop('Invoice Log on ' + currTime, currTime, 'Invoice Log')
htmldata += web.startBody()
htmldata += web.writedatainbody("E-Builder Project data as of: "+ currTime)
htmldata += web.makeTableHeader(headerRow)
htmldata += web.makeRows(inv_data, rows)
htmldata += web.makeHTMLbottom(currTime)
html_file.write(htmldata)
#get_ipython().system('jupyter nbconvert --to script InvoiceLog_HTML.ipynb')
