import csv, datetime, getpass
import chardet
"""
import ebCOST_newAPI.eb.ebCostLib as ebCost
import ebCOST_newAPI.eb.ebPO.write_PO_Cost_line as wPOC
import ebCOST_newAPI.eb.ebPO.write_PO_Process_line as wPOP
import ebCOST_newAPI.eb.ebAPI_lib as ebAPI
"""

import uml_python.uml_lib.ebCostLib as ebCost
import uml_python.eb.ebPO.write_PO_Cost_line as wPOC
import uml_python.eb.ebPO.write_PO_Process_line as wPOP
import uml_python.uml_lib.ebAPI_lib as ebAPI


# basic_Buyways_POs
# PURPOSE:  Translate Buyways PO data to EB import data/Excel
# METHOD:   Read CSV, pull needed fields, output to Excel with field headers conforming to EB import standards
# INPUT:    CSV from Buyways "transaction" report
# OUTPUT:   Dictionary ready for writing to Excel
# ERRORS:   BW may have budget lines/codes that don't exist in EB. These are flagged for Contingency
# NOTES:    Needs to be reworked in light of new Origin Code, "LEB", which flags any PO or Invoice that started
#           from an EB Process. Those all should be brought in via Process Import, not direct import to the Cost Module
# 200509    Adding logic to write lines one at a time to excel, rather than building dictionary

# June 05, 2023
# Modified to seperate EBCOSTFMP and EBCOSTST
# April 24, 2023
# NOTE: Noticed the encoding type of csv file is not same always, so adding code to check encoding of the file before reading the rows
# 201202
# uname = getpass.getuser()
# srcDir = "C:\\Users\\" + uname + "\\Downloads\\"201117
# 1. Is Origin Code "LEB"? If so, check custom field for PO number
#    plus, we have the FMP number in the External Notes
# 2.
# 201016
# Need to check if this came from integration. Check for External Req #. If so, we need to pad line numbers
# to 3-digits
# June 5, 2020
# Adding back multi line support: track if we're in the same PO. Copy description - or store multiple lines so we
# can combinen descriptions and use that for all lines.
# May 18, 2020
# Not so fast on API. going back to ebuilder: can report on funding, including Speedtype, FMP, and Funding Source
# Category name - closest I can get to Funding Rule. So, logic is: Is Origin Code "LEB" -that means process import?
# If not, is speedtype in EB? Get FMP and Funding Source and include for cost import. If not, check if FMP is in PS
# Project ID: report and warn ifso
# May 16, 2020
# Modifying logic: how do know a PO belongs to ebuilder? Previously, just used EB report. But, the only way to report
# on funding rules and speedtypes, is to report on Actuals (invoices). We were limiting filter to EB projects
# with invoices. No 1st PO on a project, no 1st invoice on PO. So, we need to also check active EB projects. We can
# get that from API. In fact, we can probably get Actuals, speedtypes, and funding rules from API too. First things
# first
# May 4, 2020
# print "basic", ofilebase
# Sep 3, 2021
# added call to ebProjs here and tracking FM Dept lead for PO filtering

def padstr(s):
    retVal = s
    if len(s) == 1:
        retVal = "0" + retVal
    return retVal


def tstamper2():
    now = datetime.now()
    mo = padstr(str(now.month))
    d = padstr(str(now.day))
    h = padstr(str(now.hour))
    mi = padstr(str(now.minute))
    s = padstr(str(now.second))
    tstamp = str(now.year)[2:] + mo + d + "_" + h + mi + s
    return(tstamp)

        
def getFundRuleFromFMP(currFMP, currST):
    currFRfromFMP = ebAPI.get_FundingRules_FMP()[currFMP]['Name']
    for i in range(len(currFRfromFMP)):
        if currFRfromFMP[i].split('-')[1] == currST:
            currFundingRule = currFRfromFMP[i]
    return currFundingRule

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


def translate_Buyways_POs(theCSV, currStamp):
    # print("Translating Buyways POs on: ", theCSV)
    #print(theCSV)
    #print(theCSV)
    #with open(theCSV) as csvfile:
    #    print('opened and checked')
    budgTasks = ebCost.getBudgetTasks()
    # function has long list of budget lines, with 2 digit task code and 6 digit line
    # number
    # 201211 We can get actual funding rule names so changing this function to get
    # speedtype and name - no category to manipulate
    # ebST = ebCost.ebSupportData(supportFile)
    ebST = ebAPI.get_FundingRules()
    ebProjs = ebAPI.get_Projects()
    activePOs = ebAPI.get_activePOs(ebProjs)
    ebCompanies = ebAPI.get_Companies_dict2()
    fundRules = ebAPI.get_FundingRules()
    retval = ''

    for s in sorted(ebST):
        if s == "120439":
            ebST[s] = {"Name":"Campus Renovations-120439","FMP":["393361"]}
        if s == "120552":
            print (s, ebST[s])

    testST = ["118213","118214","118409","118412"]

    myCount = 1
    lineType = ""

    firstProcess = False    # flags to create Excel
    firstCost = False
    costFile = False

    # counts = {"EBprocess":0,"EBcost":0,"EBexists":0,"EBexistsCO?":0, "nonEB":0}
    counts = {"EBprocess": 0, "EBcostST": 0, "EBcostFMP": 0, "EBexists": 0, "EBexistsCO?": 0, "nonEB": 0}
    COcount = 0

    #theCSV = "DataFiles\\transaction_export_po_search_POData884686266.csv"

    # NOTE: Noticed the encoding type of csv file is not same always,
    # so adding code to check encoding of the file before reading the rows Just in Case
    with open(theCSV, 'rb') as f:
        result = chardet.detect(f.read())
        encodingFormat = result['encoding']

    with open(theCSV,encoding=encodingFormat) as csvfile:
        POdata = csv.DictReader(csvfile,delimiter=',') #quotecharacter?
        currPO = ""
        currPOvalueTotal = 0.0

        samePO = False
        prevDesc = ""
        errorLine = []
        errorST = []
        EBvalue = 0.0
        currPOvalue = 0.0
        for r in POdata:
            #print "At line", myCount
            #print r
            print("From translate_BW_PO::!!!!!!!!!!!!!!!!!!!!::", r['PO #'])
            #print "From translate_BW_ST with L::::", r['Speedtype']
            #print "New line of data\nCurrPO:", currPO, " and BW PO:",r['PO #'], " and PO Line #", r['PO Line #']
            originalST = r["Speedtype"] # we want to preserve to see multiple speedtypes
            originalProject = r["Project"]
            if currPO != r['PO #']:
                # It's a new PO
                #print ("!!!<<<", currPO)
                currPO = r['PO #']

                if r['PO Line #'] == '1':
                    bwValue = float(r['Extended Price'].replace(',',''))
                    currPOvalueTotal = bwValue
                    #print ("!!!<<< Line 1")

                #print "****Changed POs", currPO
                if lineType == "EBexists":
                    #print "Check values - exists?", currPO, EBvalue, currPOvalue
                    #print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>EBexists?", currPO
                    delta = ebValue - bwValue
                    if delta < 0 or delta > 0:
                        #print r['PO #'], "Exists in EB, Values are not equal!!!", str(delta)
                        #print "Note: may be multi-line PO?", r['PO #'], r['PO Line #']
                        lineType = "EBexistsCO?"
                        #print "POssible CO:", currPO
                        COcount += 1
                samePO = False
            else:
                #if lineType == "EBexists":
                    #print "same PO>>>>>>>>>>>>>>>>>>>>", currPO
                    #print "SAME PO>>>>", currPO, r['PO #'], r["PO Line #"]
                #print "Same PO!!!", currPO
                try:
                    bwValue = float(r['Extended Price'].replace(',',''))
                    #print "extended price", bwValue
                except:
                    bwValue = 0.0
                    #print "!!!<<< extended price 0"
                #print r["PO #"]
                #print "Multi-line: running total was:", currPO, currPOvalueTotal, " this line is", bwValue
                currPOvalueTotal += bwValue
                #print "Running total is now:", currPOvalueTotal
                samePO = True # what happened to last line?
                print("????",  currPO, r['PO #'])

            if r['Origin Code'] == "LEB":
                #print "Found a process"
                #print "!!!! Process:",  r['PO #']
                # We need to know if it's already in EB
                lineType = "EBprocess"
            else:
                # 230727 We need to expand this logic: if the FMP is not in the PS project number, we need to look in the description of the first line
                # This is where Bus Ops is adding it as "FMP XXXXXX"
                
                PS_FMP = ebCost.parse_Buyways_Project(originalProject)
                DESC_FMP = ebCost.parse_Buyways_Description(r["Product Description"]) # may not be necessary?
                print(">>>>>!!!!",PS_FMP, DESC_FMP)
                
                if PS_FMP != "NON FMP":
                    # PS Project Number has FMP
                    print("DDDD")
                    lineType = "EBcostFMP"
                    currFMP = PS_FMP
                    print("@@@@@@@@@@ PS Project number has FMP",type(currFMP), currFMP, lineType)
                    currST = r["Speedtype"][:-2]
                    currST = currST.lstrip()
                    currFund = r["Fund"][:-2]
                    currFund= currFund.lstrip()
                    # currFundRule = ebCost.buildFundingRule(currST,currFund)
                    # currFundRule = currFundRule.lstrip()
                    # currFundRule = ebAPI.get_FundingRules_FMP()[currFMP]['FundingRule']
                    # print("NNNNNNNNNNN",currFundRule)
                    currLead = "NO LEAD YET"
                elif (DESC_FMP != "NON FMP"):
                    # Description has FMP
                    # check the description (only if we're on line 1???)
                    print(">>>>>!!!! PS PRoject Number did not have FMP\n", r["Product Description"])
                    currFMP = DESC_FMP
                    lineType = "EBcostFMP"
                    print(">>>>>!!!! Description has FMP", type(currFMP),DESC_FMP, currFMP)
                else:
                    print("Why ... did we get here?? SHould we dump this?")
                    lineType = "nonEB" # will change to non EB if we don't find speedtype OR FMP!!!!!
                    
                    #currST = r["Speedtype"][:-2]
                    #currST = currST.lstrip()
                    #currFund = r["Fund"][:-2]
                    #currFund= currFund.lstrip()
                    #currFundRule = ebCost.buildFundingRule(currST,currFund)
                    #currFundRule = currFundRule.lstrip()
                # lineType = "EBcost" # will change to non EB if we don't find speedtype
                #print "!!!<<< EBcost linetype"

            # GOT HERE 230728 print("Finished with FMP/lineType", lineType)
            if lineType != "nonEB":
                if currPO in activePOs: # Check custom field for POREQ?
                    lineType = "EBexists"
                    bwValue = float(r['Extended Price'].replace(',',''))
                    ebValue = float(activePOs[r['PO #']]["Value"])

                    #delta = ebValue - bwValue
                    #if activePOs[ ebValue > bwValue or activePOs[r['PO #']]["Value"] < bwValue:
                    #if delta < 0 or delta > 0:
                        #print r['PO #'], "Exists in EB, Values are not equal!!!", str(delta)
                        #print "Note: may be multi-line PO?", r['PO Line #']
                        #lineType = "EBexistsCO?"
                    #else:
                        #print "..............................................",r['PO #'], "Exists in EB - value matches with BW"
                else:
                    print("****PO number is not in EB - but we shou;dn't do this if we know it's not an EB FMP")
                    BW_STs = ebCost.parseST(r['Speedtype'][:-2])
                    # print ("!!!!>>>>>", BW_STs)
                    #print "Not in EB", currPO, BW_STs
                    if len(BW_STs) > 1:
                        multipleST = originalST
                    else:
                        multipleST = ""
                    foundST = False
                    for BW_ST in BW_STs:
                        # print("!!!<<< BW speedtype", BW_ST)
                        if foundST:
                            #print ("!!!<<< found ST")
                            break
                        # WHAT ABOUT 113847-L|108505-L
                        # We need a Speedtype parser
                        # For now, flag as multi, check both, take first FMP, make note
                        # on output
                        #print ">>>", BW_ST, "<<<", r['Speedtype']

                        if BW_ST in ebST: # or, == "APP200" for TEST project. Linetype = "EB_TEST" - funding rule is speedtype
                                            # plus "ST " (confirm!). Accept any data for tests
                            #print "!!!>>>Speedtype found in EB list: ",BW_ST
                            #print ("???>>>", ebST[BW_ST])
                            currST = BW_ST
                            # print("Hhhhhhhhhhhhhh", currST)

                            #201216 We need currFMP but we changed how we handle EB ST: no more support report
                            # now, we use FundingRules API. Does FundingRules have project ID? Go back to parsing
                            # BW PS Project ID?
                            # 230728 Commeting this out since:
                            # 1. We don't/can't import these multiple FMP number items
                            # 2. Bus Ops is now adding FMP to the description - there shouldn't be any items
                            #    that don't FMP already
                            """
                            if len(ebST[BW_ST]["FMP"]) > 1:
                                #print("here")
                                currFMP = ""
                                for f in ebST[BW_ST]["FMP"]:
                                    currFMP += str(f) + ","
                            else:
                                if BW_ST == "120217":
                                    currFMP = "393281"
                                elif BW_ST == "120925":
                                    currFMP = "393406"
                                # elif BW_ST == "111841":
                                #     currFMP = "APP200"
                                else:
                                    print("check",[BW_ST],"check", ebST[BW_ST],"check", ebST[BW_ST]["FMP"][0])
                                    currFMP = ebST[BW_ST]["FMP"][0]
                                    # just 1 FMP, use it WE SHOULD PARSE/ERROR CHECK
                                #print "______________________ Just one:", currFMP
                            print ("??????", currST, currFMP)
                            
                            if "," in currFMP: # multiple projects - do we need to check Phase and if complete, not consider multi FMP?
                                currLead = "TBD"
                                #print(currLead)
                            else:
                                if currFMP == "393150":
                                    currLead = "O&S"
                                    lineType = "nonEB"
                                    print("Changing for testing")
                                elif currFMP == "XXXXXX":
                                    currLead = "FMP XXXXXX"
                                else:
                                    currLead = ebProjs[currFMP.encode('ascii')]["FMlead"] #ebProjs return FMP values as Bytes, hence encoding.
                                    # currLead = ebProjs[currFMP]["FMlead"]  # ebProjs return FMP values as Bytes, hence encoding.
                            """
                            try:
                                currLead = ebProjs[currFMP.encode('ascii')]["FMlead"] #ebProjs return FMP values as Bytes, hence encoding.
                            except:
                                currLead = "FMP XXXXXX"
                            print(currFMP, " !!!>>> lead is", currLead)

                            #currFundRule = "Rule 1 " + ebST[BW_ST]["FundSource"]
                            try:
                                # 201211 We can get funding rules - no need to do Fund Source stuff
                                #currFundRule = ebST[BW_ST]["FundSource"] + "-" + currST
                                currFundRule = ebST[BW_ST]["Name"]
                                #print "translate_PO:", currST, currFMP, currFundRule
                            except:
                                currFundRule = "CHECK FUNDING RULE"
                            #print ">>>>>>", currFMP, currST
                            r['Project'] = currFMP
                            r['Speedtype'] = currST
                            foundST = True
                        elif BW_ST in testST:
                            print("Test project")
                            currST = BW_ST
                            currFMP == "APP200"
                            currFundRule = BW_ST # Test project funding rules match speedtypes
                            r['Project'] = currFMP
                            r['Speedtype'] = currST #Funding rule should equal speedtype, for APP200 - how?????
                            foundST = True
                        elif PS_FMP == "NON FMP":
                            lineType = "nonEB"
                            # print "Why did we get here?"
                            """
                            FMPfromBWproj = ebCost.parse_Buyways_Project(r['Project'])
                            # is it in ebST
                            inEB = False
                            lineType = "nonEB"
                            for s in ebST:
                                if ebST[s] == FMPfromBWproj:
                                    inEB = True
                                    print "WARNING: Found FMP in PS Project ID but not ST"
                                    break
                            """
                #@@@@@!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  200509: break up triage: is it LEB? Than it's process
                # Does speedtype exist in EB? If it does, and it's not LEB, than it's cost
                # Either way, change row data to make project FMP (note or check PS project?)
                print("Linetype logic", lineType)
                if lineType == "EBprocess":
                    print("OKOKOKOKOK Process")
                    if firstProcess == False:
                        #print "Create Process Excel file"
                        # get output file name and pointer to Excel/openpyxl and worksheet
                        processXL, processWS = ebCost.create_Excel()
                        ebCost.write_ExcelHeaders(processXL, processWS, "POprocess")
                        wPOP.write_PO_Process_line.counter = 2 # set counter for rows
                        firstProcess = True
                    print("......Write Process line to excel")
                    wPOP.write_PO_Process_line(r, multipleST, processWS)

                elif lineType == "EBcostST":
                    # print(">>>>Line Type:",lineType,"FMP:", currFMP,"ST:", currST)
                    # NEED TO ADD A CHECK: IS THE PO ALREADY IN EB? IF SO, IS VALUE SAME?
                    # WHAT ABOUT MULTIPLE LINES?????????????
                    if firstCost == False:
                        print("Create Cost Excel file")
                        # get output file name and pointer to Excel/openpyxl
                        costXL, costWS = ebCost.create_Excel()
                        ebCost.write_ExcelHeaders(costXL, costWS, "POcost")
                        wPOC.write_PO_Cost_line.counter = 2  # set counter for rows
                        firstCost = True
                    # print "......Write Cost line to excel"
                    if samePO:
                        # EB uses same description for all PO lines - we'll want to concatenate all BW
                        # descriptions and use that
                        # parseStr removes/changes EB illegal characters, like bullets
                        print("SAME PO")
                        prevDesc += " | " + ebCost.parseStr(r['Product Description'])
                        # 9/13/2021: 400 char limit. For future: the first field in CSV is a unique ID for Buyways. We can/should use that
                        # to put a URL in the description or in a custom field
                        r['Product Description'] = prevDesc
                    else:
                        prevDesc = ebCost.parseStr(r['Product Description'])
                        r['Product Description'] = prevDesc
                    # print "Going to write cost line"
                    # print("Holaaaaa", multipleST,"hiiiiii", currST)
                    # print("Fund",currFund,"ST",currST)
                    currFundRule = ebCost.buildFundingRule(currST,currFund)
                    # print(currFundRule)buildFundingRule
                    wPOC.write_PO_Cost_line(r, ebCompanies, currFundRule, multipleST, budgTasks, costWS, samePO, currLead)
                    # print("Back from write cost line")
                    # print('_____________________________________')

                elif lineType == "EBcostFMP":
                    # print(">>>>Line Type:",lineType,"FMP:", currFMP,"ST:", currST)
                    # NEED TO ADD A CHECK: IS THE PO ALREADY IN EB? IF SO, IS VALUE SAME?
                    # WHAT ABOUT MULTIPLE LINES?????????????
                    if firstCost == False:
                        print("Create Cost Excel file")
                        # get output file name and pointer to Excel/openpyxl
                        costXL, costWS = ebCost.create_Excel()
                        ebCost.write_ExcelHeaders(costXL, costWS, "POcost")
                        wPOC.write_PO_Cost_line.counter = 2  # set counter for rows
                        firstCost = True
                    # print( "......Write Cost line to excel")
                    if samePO:
                        # EB uses same description for all PO lines - we'll want to concatenate all BW
                        # descriptions and use that
                        # parseStr removes/changes EB illegal characters, like bullets
                        print("SAME PO")
                        prevDesc += " | " + ebCost.parseStr(r['Product Description'])
                        # 9/13/2021: 400 char limit. For future: the first field in CSV is a unique ID for Buyways. We can/should use that
                        # to put a URL in the description or in a custom field
                        r['Product Description'] = prevDesc
                        r["Project"] = currFMP
                        r["Speedype"] = currST

                    else:
                        # print('check')
                        prevDesc = ebCost.parseStr(r['Product Description'])
                        r['Product Description'] = prevDesc
                        # print ("Going to write cost line")
                        r["Project"] = currFMP
                        # print("Before assigning", r["Speedtype"], currST)
                        r["Speedype"] = currST
                        # print("After", r["Speedtype"], currST)
                        # print(currFundRule)
                    currFundRule = getFundingRule(currST, fundRules) # FundingRule using the method used in XML
                    wPOC.write_PO_Cost_line(r, ebCompanies, currFundRule, currST, budgTasks, costWS, samePO, currLead)
                    # print("Back from write cost line")
                    # print('_____________________________________')

                #else:
                    #print "Non FMP"
                    #nonFMP.append(r)
                #print ">>>>", lineType, BW_ST
            counts[lineType]+=1
            myCount += 1

    # print(counts)
    print("Done reading CSV....", theCSV)
    print('------------------')
    print(counts)

    for c in counts:
        print ("@@@@@@PO data totals", c, counts[c])
    print ("COs?", COcount)
    #retVal = str(counts["EBprocess"]) + str(counts["EBcost"])
    # retVal = "PO Cost Imports:" + str(counts["EBcost"])
    retVal = "PO Cost FMP Imports:" + str(counts["EBcostFMP"])
    retVal = "PO Cost Speedtype Imports:" + str(counts["EBcostST"])
    retVal += "\nPO Process Imports:" + str(counts["EBprocess"])
    # currStamp = tstamper2()
    #retVal = "What?"
    # Check if we creeated any Excels, if so, close 'em
    #uname = getpass.getuser()
    # ofilebase = "DataFiles/" + currStamp + "_"
    # ofilebase = "C:\\Users\\K_Gattu\\PycharmProjects\\uml_python\\uml\\DataFiles\\" + currStamp + "_"
    ofilebase = "B:\\dailyImports\\_CSV_" + currStamp + "_"
    print("First cost", firstCost)

    if firstProcess == True:
        ofile = ofilebase + "POprocessImport.xlsx"
        costFile = True
        processXL.save(ofile)

    if firstCost == True:
        ofile = ofilebase + "POcostImport.xlsx"
        costFile = True
        costXL.save(ofile)
    if costFile:
        retVal = {'Stats': counts, 'ImportFile': ofile}
        # print(retVal)
        return retVal
        # return ofile
    else:
        retVal = {'Stats':counts, 'ImportFile': 'No EBCost POs'}
        # print(retVal)
        return retVal
        # return 'No EBCost POs'

    print(ofile)
    # return ofile
    # return retVal
