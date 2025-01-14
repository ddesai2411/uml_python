import json, os, shutil, sys
import xmltodict, glob
from datetime import datetime
# import uml.eb.ebCostLib as ebCost
# import uml.eb.ebAPI_lib as ebAPI
import uml_python.uml_lib.ebCostLib as ebCost
import uml_python.uml_lib.ebAPI_lib as ebAPI


"""
October 2022: THIS is the code we run with ebProjs, windows task scheduler
every hour
Logic checks:
- Is Status = PAID?
- Is it a PAYAP? >> EBprocess
- Is PO in EB?
    - FMP(s)?       >>ebFMP
    - Speedtype(s)  >> ebST

"""
def isSTinEB(theSTs):
    global ebSTs
    retVal = False
    
    for s in theSTs:
        if s in theSTs:
            #print "Found", s
            retVal = True
            break

    return retVal

def allNumbers(s):
    retVal = True
    for c in s:
        if c not in "0123456789":
            retVal = False
    return retVal

def get_Speedtypes(theLine):
    retVal = []

    toks = theLine.split("\"Speedtype\" label=\"Speedtype\"")
    if len(toks) > 0:
        for i in range(0,len(toks)):
            #print i, toks[i][:100]
            subtoks = toks[i].split("<Value>") # is it always first?????
            for s in subtoks:
                #print "\t", i, s[:100]
                subsubtoks = s.split("</Value>")
                for t in subsubtoks:
                    currLen = len(t) # check for "-L" as last 2 digits?????
                    #if currLen == 8 and t[7] == "-" and t[8] == "L":
                    if currLen == 8:
                        if (allNumbers(t[0:6])) and t[0:6] not in retVal:
                            retVal.append(t[0:6])
    return retVal

def get_PSprojs(theLine):
    retVal = []

    toks = theLine.split("<CustomFieldValueSet name=\"Project\" label=\"Project\">")
    print("bwFilter:")
    print(toks)
    if len(toks) > 0:
        for i in range(0,len(toks)):
            print (i, toks[i][:100])
            subtoks = toks[i].split("<Value>") # is it always first?????
            for s in subtoks:
                #print "\t", k, s[:100]
                subsubtoks = s.split("</Value>")
                for t in subsubtoks:
                    currLen = len(t) # check for "-L" as last 2 digits?????
                    
                    if (currLen == 17 or currLen == 16):
                        #print "\t", t
                        if "FMP0" in t:
                            if t[9:15] not in retVal:
                                retVal.append(t[9:15])
                        elif "FMP" in t:
                            if t[8:14] not in retVal:
                                retVal.append(t[8:14])
    return retVal

def get_POdetails(theFile):
    global ebPOs
    
    fo = open(theFile)
    line = fo.readline()
    #retVal2 = {"UMLOW":False, "EBtype":"nonEB", "Status":""}
    retVal = "TBD"
    currPO = get_PO(line)
        
    #print "\t>>>>", currPSprojects
    if currPO in ebPOs:
        retVal = "ebEXISTS"
    else:
        retVal = currPO
        currPSprojects = get_PSprojs(line)
        #print "\t..... FMPs", currPSprojects
        if len(currPSprojects) == 0:
            #retVal = "noFMP"
            currSTs = get_Speedtypes(line)
            #print "\t.... Speedtypes:", currSTs
            if (isSTinEB(currSTs)):
                retVal = "ebCostST"
            else:
                retVal = "notEB"
        else:
            retVal = "ebCostFMP"
    fo.close()
    return retVal

def get_VoucherID(theLine):
    retVal = "VOUCHER ID TBD"
    try:
        toks = theLine.split("<InvoiceNumber>")
        retVal = toks[1][:8]
    except:
        retVal = "ERROR: GET VOUCHER ID FAILED"

    return retVal

def get_STATUS(theLine):
    retVal = "TBD"
    try:
        toks = theLine.split("status=\"")
        retVal = toks[1][:4]
    except:
        retVal = "ERROR: GET STATUS FAILED"

    return retVal

def get_PO(theLine):
    retVal = "NO PO NUMBER FOUND"
    toks = theLine.split("<PONumber>")
    if len(toks) > 0:
        for i in range(0,len(toks)):
            retVal = toks[i][:10]

    return retVal

def isPAYAP(theLine):
    retVal = False
    toks = theLine.split("<AttachmentName>")
    if len(toks) > 0:
        for i in range(0,len(toks)):
            if toks[i][:5] == "PAYAP":
                #print "\n", i, ":", toks[i][:20]
                retVal = True
    return retVal
            
def invoiceCheck(theFile):
    global ebPOs
    global ebInvoices

    fo = open(theFile)
    line = fo.readline()
    #retVal2 = {"UMLOW":False, "EBtype":"nonEB", "Status":""}
    retVal = "TBD"

    currStatus = get_STATUS(line)
    currVoucherID = get_VoucherID(line)
    
    if currStatus == "Paid":
        if currVoucherID in ebInvoices:
            retVal = "ebEXISTS" # What if we add the vouhcer id when we check on an inprocess payap?
        else:
            if (isPAYAP(line)):
                retVal = "ebPAYAP"
        
            else: 
                currPO = get_PO(line)
                if currPO == "NO PO NUMBER FOUND":
                    retVal = "ERROR: NO PO"
                elif currPO[0] != "L":
                    retVal = "nonEB"
                elif currPO in ebPOs:
                    #print "PO is in EB"
                    retVal = "EBcost"
                else:
                    retVal = "nonEB"

                #print currPO, currPO[0]
    else:
        retVal = "NOT_PAID_YET"
    
    return retVal
def POnumber_from_file(fname):
    retVal = "NO PO NUMBER FOUND"
    try:
        toks = fname.split("Jaggaer_PO_")
        retVal = toks[1][10]
    except:
        retVal = "PO PARSE FAILED"
    return retVal

def bwFilter():
    global logFile
    print("Calling bwFilter")
    logFile.write("bwFilter called\n")
    logFile.close()
    
    theDir = "C:\\bw2eb\\"
    theFiles = os.listdir(theDir)
    invCounts = {"NOT_PAID_YET":0,"ebPAYAP":0,"ERROR: NO PO":0,"nonEB":0,"EBcost":0,"ebEXISTS":0} # add ebEXISTS
    POcounts = {"ebCostFMP":0,"notEB":0,"ebCostST":0,"ebEXISTS":0,"notUML":0}
    # Set up output: need to refine this. For now, just keep writing to the same excel file, same WS
    costXL, costWS = ebCost.create_Excel()
    ebCost.write_ExcelHeaders(costXL, costWS, "POcost") # create return value so we know headers, template for writing?
    write_POcost_line.counter = 2 

    for f in theFiles:
        if "Jaggaer_PO" in f:
            if "Jaggaer_PO_L" in f:
                print("jaggaer")
                print(theDir+f)
                POdetails = get_POdetails(theDir + f)
                if POdetails == "ebCostFMP" or POdetails == "ebCostST" or POdetails == "ebProcess":
                    currPOnum = POnumber_from_file(f)
                    # we're opening this in PO details too. We should do it once 
                    ifile = open((theDir+f),'r')
                    process_POxml(currPOnum,ifile,costWS)
                    ifile.close()
                    oDir = (r"\\fs.uml.edu\UMLFiles\Facilities\_ebuilder\bw2eb\toEB\PO\\" + POdetails + "\\")
                    shutil.copy2((theDir + f), oDir)
                #print "copied", f
                os.remove(theDir + f)
                POcounts[POdetails] += 1
            else:
                os.remove(theDir + f)
                #print "Not uml, removed", f
                POcounts["notUML"] += 1
            
                
        elif "Jaggaer_Invoice" in f:
            invDetails = invoiceCheck(theDir + f)
            print("???>>?>?>", invDetails)
            if invDetails == "ebPAYAP":
                shutil.copy2((theDir + f), r"\\fs.uml.edu\UMLFiles\Facilities\_ebuilder\bw2eb\toEB\Invoice\ebProcess\\")
            if invDetails == "ebCost":
                shutil.copy2((theDir + f), r"\\fs.uml.edu\UMLFiles\Facilities\_ebuilder\bw2eb\toEB\Invoice\ebCost\\")
            os.remove(theDir + f)
            invCounts[invDetails] += 1
    for c in invCounts:
        print(c, invCounts[c])
    for c in POcounts:
        print(c, POcounts[c])
    if POcounts["ebCostFMP"] > 0 or POcounts["ebCostST"] > 0:
        print("Write Excel: at least 1 costfmp or costST")
        costXL.save(r"\\fs.uml.edu\UMLFiles\Facilities\_ebuilder\bw2eb\toEB\PO\\" + "TEST_POcost.xlsx")
        
def get_commitmentType(BWnumber):
    global ebCompanies
    
    currBWsupplierNum = BWnumber.zfill(10)
    try:
        currEBsupplierName = ebCompanies[currBWsupplierNum]
    except:
        currEBsupplierName = "NOT FOUND"
    commitType = ebAPI.get_commitType(currEBsupplierName)
    return commitType

def get_fundingRule(currST):
    global ebSTs
    
    currFR = ""
    
    if currST in ebSTs:
        currFR = ebSTs[currST]["Name"]
        currFMPs = ebSTs[currST]["FMP"]
    else:
        currFR = "CHECK FUNDING RULE"
        currFMPs = []
    return currFR, currFMPs

def get_Speedtypes2(theData):
    retVal = [] # list of speedtypes, hopefully just 1
    for f in theData:
        if f["@name"] == "Speedtype":
            try:
                if f["CustomFieldValue"]["Value"] not in retVal:
                    retVal.append(f["CustomFieldValue"]["Value"])
            except:
                retVal.append("SPLIT FUNDING")
    return retVal

def get_FMP_fromPSprojectID(theString):
    # Logic (ish): is FMP in it? look at next character. If 0, get 6 after it. if number, get 6 starting there
    i = theString.find("FMP")
    if i == -1:
        retVal = "NO FMP"
    else:
        if theString[i+3] == "0":
            retVal = theString[i+4:i+10]
        else:
            retVal = theString[i+3:i+9]
    return retVal

def find_PSprojectIDs(currData):
    # could vary by line. each line could be split funded
    print("parse data for PS project ids, custom field <Project>")
    for f in currData:
        print("???", f)
        #if f["@name"] == "Project":
            #retVal =  f["CustomFieldValue"]["Value"]
    
def get_customField(theData,theField):
    retVal = "NOT FOUND"
    # what about multiple ones?
    for f in theData:
        #print "???", f["@name"]
        try:
            if f["@name"] == theField:
                retVal =  f["CustomFieldValue"]["Value"]
                if theField == "Speedtype":
                    print(theField, retVal)
        except:
            retVal = "ERROR - NOT FOUND"
    return retVal


def process_XML_POline(lineData):
    for x in lineData:
        print(x)
        

def get_OriginCode(POdata, numLines):
    originCode = "FAILED ON ORIGIN CODE"
    if numLines == 1:
        try:
            originCode = get_customField(POdata["POLine"]["CustomFieldValueSet"],"Origin Code")
        except:
            originCode = "FAILED ON SINGLE LINE ORIGIN CODE"
    else:
        try:            
            originCode = get_customField(POdata["POLine"][0]["CustomFieldValueSet"],"Origin Code")
        except:
            originCode = "FAILED ON MULTI LINE ORIGIN CODE"
            
    return originCode
    
def get_POnumber_fromFilename(theFile):
    toks = theFile.split("Jaggaer_PO_")
    #print "1: Commitment number", toks[1][:10]
    return toks[1][:10]

def get_SupplierInfo(POdata):
    currSupplierNumber = POdata["POHeader"]["Supplier"]["SupplierNumber"]
    currSupplierName = POdata["POHeader"]["Supplier"]["Name"]
    ebSupplierName = get_EBcompanyName(currSupplierNumber)
    commitType = ebAPI.get_commitType(ebSupplierName)
    return currSupplierNumber, currSupplierName, ebSupplierName, commitType

def get_EBcompanyName(supplierNum):
    global ebCompanies
    
    try:
        currCompanyName = ebCompanies[supplierNum]
    except:
        currCompanyName = "NOT FOUND"
    return currCompanyName
    
def get_PSprojectIDs(POdata, numLines):
    # Watch out for multi-line and for split funding 
    FMPs= []
    
    if numLines == 1:
        theProject = get_customField(POdata["POLine"]["CustomFieldValueSet"],"Project")
        if theProject != "ERROR - NOT FOUND":
            theFMP = get_FMP_fromPSprojectID(theProject)
            if theFMP != "NO FMP" and theFMP not in FMPs:
                FMPs.append(theFMP)
    else:
        for i in range( 1, numLines):
            theProject = get_customField(POdata["POLine"][i]["CustomFieldValueSet"],"Project")
            if theProject != "ERROR - NOT FOUND":
                theFMP = get_FMP_fromPSprojectID(theProject)
                if theFMP != "NO FMP" and theFMP not in FMPs:
                    FMPs.append(theFMP)

    #if len(PSprojects) == 0:
        #PSprojects.append("PS Project NOT FOUND")

    return FMPs

def convertDate(theDate):
    #2022-10-13T16:53:51.356-04:00

    retVal = ""
    try:
        retVal = theDate[5:7] + "/" + theDate[8:10] + "/" + theDate[0:4]
        
    except:
        retVal = "DATE CONVERSION FAILED"
    return retVal

def get_budgetLine(currAccount):
    global budgTasks
    retVal = ""
    
    try:
        ebLine = budgTasks[currAccount[:-2]]
        retVal = ebLine
     
    except:
        #print "Account Not Found",str(r['Account'][:6])
        # CAUTION: Changing line item to Contingency if line item is not in eb
        retVal = "99.99CONT"
        #print ">>>Not found:", r['Account'][:6]
        #errorLine.append(POrow['Account'])
        #debugPrint("Error" + POrow['Account'])
    return retVal

def process_POline2(theLine, theData,lineNo):
    currAccount = get_customField(theLine["CustomFieldValueSet"],"Account")
    theData[5] = get_budgetLine(currAccount)
    theData[7] = lineNo
    theData[8] = theLine["Item"]["Description"]
    theData[9] = theLine["Quantity"]
    theData[10] = theLine["LineCharges"]["UnitPrice"]["Money"]["#text"]
    theData[13] = theLine["LineCharges"]["ExtendedPrice"]["Money"]["#text"]
    try:
        theData[14] = str(theLine["Item"]["ProductUnitOfMeasure"][0]["Measurement"]["MeasurementUnit"])
    except:
        theData[14] = "N/A"
    theData[19] = str(theLine["Item"]["CommodityCode"])
    currSTs = get_Speedtypes2(theLine["CustomFieldValueSet"])
    if len(currSTs) == 1 and currSTs[0] != "SPLIT FUNDED":
        try:
            currSpeedtype = currSTs[0][:6]
            print(">>>>>>", currSpeedtype)
            currFundingRule, currFMPs = get_fundingRule(currSpeedtype)
        except:
            currFundingRule = "NOT FOUND"
            currSpeedtype = "MULTI-NEEDS WORK"
            
    theData[15] = currFundingRule
    theData[16] = currSpeedtype
    
def write_POcost_line(theData,ws,currLine):
    for d in sorted(theData):
        outCell = ws.cell(row=currLine,column=d)
        outCell.value = theData[d]
    write_POcost_line.counter += 1
    
def process_POxml(currPOnum,theFile,ws):
    global ebCompanies
    hdrData = {}
    
    
    xmlcontent = theFile.read()
    bwdata = xmltodict.parse(xmlcontent)
    currPOdata = bwdata["PurchaseOrderMessage"]["PurchaseOrder"]
    print(type(currPOdata["POLine"]))
    try:
        line1 = currPOdata["POLine"]["@linenumber"]
        numLines = 1
    except:
        numLines = len(currPOdata["POLine"])

    print("\tNumber of lines", numLines)
    print("\t1. Commitment number:", currPOnum)
    hdrData[1] = currPOnum
    
    FMPs = get_PSprojectIDs(currPOdata,numLines)
    if len(FMPs) == 0:
        print("\t2. FMP -- None Found! check speedtypes for EB STs")
        hdrData[2] = str("NO FMP FOUND")
    else:
        print("\t2. FMP:", FMPs)
        FMPstr = ""
        if len(FMPs)> 1:
            for i in range(0,len(FMPs)):
                FMPstr += FMPs[i] + ","
            hdrData[2] = FMPstr
        else:
            hdrData[2] = FMPs[0]
    
    currSupplierNumber, currSupplierName, ebCompanyName, commitType = get_SupplierInfo(currPOdata)
    hdrData[4] = currSupplierName
    hdrData[6] = "Approved"
   

    print("\t3. Commitment Type:", commitType)
    
    #print "4. Company Name (from BW - need to switch to EB)", currSupplierName
    print("\t4. Company Name (EB)", ebCompanyName)

    # Status: if company number/name ok, FMP is a single number, and ST is ok, and Commitment type is known,
    # we can make this Approved. Much easier for import
    currStatus = "Draft"
    print("\t6. Status:", currStatus)

    POrevDate = currPOdata["POHeader"]["RevisionDate"]
    print("\t11. Commitment Date (BW Revision Date):", POrevDate)

    print("\t12. Supplier Number:", currSupplierNumber)
    currCommitType = get_commitmentType(currSupplierNumber)
    hdrData[3] = currCommitType 
    
    currOriginCode = get_OriginCode(currPOdata, numLines)
    print("\t18. Origin Code:", currOriginCode)
    hdrData[11] = convertDate(POrevDate)
    hdrData[12] = currSupplierNumber
    hdrData[17] = currPOnum
    hdrData[18] = currOriginCode
    
    # Now, process single line or loop for multi line
    if numLines == 1:
        hdrData[7] = 1 # Item number
        process_POline2(currPOdata["POLine"],hdrData,1)
        write_POcost_line(hdrData,ws,write_POcost_line.counter) # WATCH OUT! What happends when we're processing lots files? Need to track what row
                                    # output row will be counter + item number - 1 ?
    else:
        for i in range(0,numLines):
            print("::::::::::::",i)
            process_POline2(currPOdata["POLine"][i],hdrData,i+1)
            write_POcost_line(hdrData,ws,write_POcost_line.counter)
       
def main():
    ignoreThis = 1

"""
ebProjs = ebAPI.get_Projects()  
ebPOs = ebAPI.get_activePOs(ebProjs)
ebSTs = ebAPI.get_FundingRules2()
ebInvoices = ebAPI.get_Invoices()
budgTasks = ebCost.getBudgetTasks()
ebCompanies = ebAPI.get_Companies_dict2()
logFile = open("C:\\bw2eb\\_bwFilterLog.txt","a")
"""
# March 23: just copying to new VM for new filtering/process
theDir = "C:\\bw2eb\\"
oDir = (r"\\UML-BW2EB-01\bw2eb\\fromBW\\")
       
theFiles = os.listdir(theDir)
#print theFiles
for f in theFiles:
    if f.endswith(".xml"):
        print(f, (theDir+f))
        shutil.copy2((theDir + f), oDir)
        os.remove(theDir + f)
            
if __name__ == "__main__":
    main()
