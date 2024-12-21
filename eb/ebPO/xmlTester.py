#!/usr/bin/env python
# coding: utf-8

import xmltodict, glob
from uml_V2.uml_lib import ebAPI_lib as eb
from uml_V2.uml_lib import ebCostLib as ebCost
# import ebAPI_lib_v2 as eb
from datetime import datetime
from openpyxl import Workbook
import os
import pandas as pd
import shutil

def get_FMPfromPSproject(psProj):
    retVal = "FMP NOT FOUND"
    print (">>>>", psProj)
    toks = psProj.split("FMP")
    if len(toks) < 2:
        print("NO FMP")
    else:
        print(toks[1])
        if toks[1][0]=="0":
            retVal = toks[1][1:]
        else:
            retVal = toks[1]
    return retVal    

def get_XMLproject(theData):
    for f in theData:
        if f["@name"] == "Project":
            print("GOT IT")
            if type(f["CustomFieldValue"]) == dict:
                currPSproj = f["CustomFieldValue"]["Value"][:-2]
                print(currPSproj)
                return currPSproj
            else:
                multiProj = []
                for i in range(len(f["CustomFieldValue"])):
                    #print(f["CustomFieldValue"][i]["Value"])
                    currPSproj = f["CustomFieldValue"][i]["Value"][:-2]
                    if currPSproj not in multiProj:
                        multiProj.append(currPSproj)
                    retVal = multiProj
                PSprojects = ",".join(multiProj)
                return PSprojects
def get_XMLfund(theData):
    for f in theData:
        if f["@name"] == "Fund":
            print("GOT IT")
            if type(f["CustomFieldValue"]) == dict:
                currFund = f["CustomFieldValue"]["Value"][:-2]
                print(currFund)
                return currFund
            else:
                multiFund = []
                for i in range(len(f["CustomFieldValue"])):
                    #print(f["CustomFieldValue"][i]["Value"])
                    currFund = f["CustomFieldValue"][i]["Value"][:-2]
                    if currFund not in multiFund:
                        multiFund.append(currFund)
                    retVal = multiFund
                PSprojects = ",".join(multiFund)
                return PSprojects
            
def get_Speedtypes(theData):
    for f in theData:
        if f["@name"] == "Speedtype":
            if type(f["CustomFieldValue"]) == dict:
                currST = f["CustomFieldValue"]["Value"][:-2]
                #print(currST)
                return currST
            else:
                multiST = []
                for i in range(len(f["CustomFieldValue"])):
                    #print(f["CustomFieldValue"][i]["Value"])
                    currST = f["CustomFieldValue"][i]["Value"][:-2]
                    if currST not in multiST:
                        multiST.append(currST)
                    retVal = multiST
                speedtypes = ",".join(multiST)
                #for i in range(len(multiST)):
                    #speedtypes = speedtypes + "," + multiST[i]
                return speedtypes

def get_customField(theData, theField):
    retVal = "NOT FOUND"

    for f in theData:
        # print "???", f["@name"]
        if f["@name"] == theField:
            try:
                retVal = f["CustomFieldValue"]["Value"]
            except:
                retVal = "MULTIPLE"
                # for g in f:
                #    print( "\tget_customField", g)
    # print(retVal)
    return retVal

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

# These Methods are not used but kept as a backup - Getting FMPs using SpeedTypes instead
def checkFMP(theFMP):
    retVal = True
    for c in theFMP:
        if c not in "0123456789":
            retVal = False
            break
    return retVal



def getFMPNumber(activePOs,currPONumber):
    currFMP = activePOs[str(currPONumber)]['FMP'].decode()
    return currFMP


# 15. Funding Rules
def getFundingRule(currST, fundingRule):
    #print(currST)
    retval = ''
    flag = currST.find(',')
    if flag == -1:
        if currST in fundingRule.keys():
            retval = retval + fundingRule[currST]['Name']
        else:
            retval = retval + "Funding Rule Not Found"
        return retval
    else:
        fundrules = []
        speedtypes = currST.split(',')
        #print(speedtypes)
        for i in speedtypes:
            #print(i)
            if i in fundingRule.keys():
                #fundrules = ','.join(fundingRule[i]['Name'])
                fundrules.append(fundingRule[i]['Name'])
        #print(fundrules)
        if len(fundrules) != 0:
            for i in range(len(fundrules)):
                retval = ",".join(fundrules)
        else:
            retval = "Funding Rule Not Found"
        #print(retval)
        return retval

def POXMLtoExcel(PO_dict):
    print(PO_dict)
    for k in PO_dict:
        print(k, PO_dict[k])
    for f in PO_dict['UMLPOFiles']:
        theFile = open(f,encoding='utf-8')
        xml_content = theFile.read()
        bwdata = xmltodict.parse(xml_content, encoding='utf-8')
        headerData = bwdata['PurchaseOrderMessage']['PurchaseOrder']['POHeader']
        POlinedata = bwdata['PurchaseOrderMessage']['PurchaseOrder']['POLine']

        # check if the PO belongs to E-Builder
        if type(POlinedata) == dict:
            print("POlinedata is dict")
            currProj = get_XMLproject(POlinedata["CustomFieldValueSet"])
            currFMP = get_FMPfromPSproject(currProj) # does not handle multiple project numbers??
            currFundID = get_XMLfund(POlinedata["CustomFieldValueSet"])
            currFundRule = ebCost.buildFundingRule("TEST_ST", currFundID)
            print("CURRENT FMP:\t\t", currFMP, "\nCurrent Fund:\t\t",currFundRule)


        else:
            print("POlinedata is LIST")
           
def checkUMLPO(POFiles, filepath):
    PO_dict = {'UMLPOFiles': [], 'nonUMLPOFiles': []}
    for i in range(len(POFiles)):
        if POFiles[i].startswith(filepath + 'Jaggaer_PO_L'):
            PO_dict['UMLPOFiles'].append(POFiles[i])
            # UMLPOFiles.append(POFiles[i])
        else:
            PO_dict['nonUMLPOFiles'].append(POFiles[i])
    return PO_dict

def main():
    theDir = "B:\\fromBW\\"
    POFiles = glob.glob(theDir + "*_PO_*.xml")
    if len(POFiles) != 0:
        PO_dict = checkUMLPO(POFiles, theDir)
        PO_Report = POXMLtoExcel(PO_dict)
    
if __name__ == "__main__":
    main()

