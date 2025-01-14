import csv, datetime, getpass, chardet
import uml_python.uml_lib.ebCostLib as ebCost
# Cost line - 230731 - working on FMP in description/simplifying code
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

firstCost = False
firstProcess = False

def get_Speedtype(r):
    retVal = ""
    if "|" in r["Speedtype"]:
        print("WARNING: multiple speedtypes, just taking first")
    try:
        retVal = r["Speedtype"][:6]
    except:
        retVal = "INVALID SPEEDTYPE"
    return retVal

def get_FMP_from_POdata(r):
    # 3 possibilities:
    # - FMP in PeopleSoft Project number
    # - FMP in description (line 1 only)
    # - no FMP
    # 230728: note - we are not including speedtype as a possible indicator that a PO belongs in EB
    # we tried that. But, we never know what project it belongs to, they were all O&S and now Bus Ops
    # is adding FMP to description on line 1
    currFMP = ""
    currFMP = ebCost.parse_Buyways_Project(r["Project"])
    if currFMP == "NON EB":
        currFMP = ebCost.parse_Buyways_Description(r["Product Description"])
    return(currFMP)
                
def parse_POcsv(theCSV,currStamp):
    # read CSV line by line, check if samePO, Store FMP and process POs that belong in EB, finish
    # 1. Same PO? 2. Already in EB? Change Order? 3. Is it a Process? 4. FMP in PeopleSoft Project? (can be multiple)
    # 5. FMP in Description? 6. Non EB (may want to track POs with STs that are in EB)
    # We need projects to get POs. We need POs so we know what's already in
    global firstCost
    global firstProcess
    budgTasks = ebCost.getBudgetTasks()
    ebProjs = ebAPI.get_Projects()
    ebST = ebAPI.get_FundingRules()
    ebProjs = ebAPI.get_Projects()
    activePOs = ebAPI.get_activePOs(ebProjs)
    ebCompanies = ebAPI.get_Companies_dict2()
    fundRules = ebAPI.get_FundingRules()
    
    retval = ''
    currFMP = ""
    lineType = ""
    
    
    # EB fields derived from BW: FMP, Funding Rule
    # EB lookup: Commitment Type
    # EB fields contstant/predetermined: Status, Retainage (0 or 5)
        
    with open(theCSV, 'rb') as f:
        result = chardet.detect(f.read())
        encodingFormat = result['encoding']
    myCount = 0
    with open(theCSV,encoding=encodingFormat) as csvfile:
        POdata = csv.DictReader(csvfile,delimiter=',') #quotecharacter?
        counts = {"EBprocess": 0, "EBcostST": 0, "EBcostFMP": 0, "EBexists": 0, "EBexistsCO?": 0, "nonEB": 0}
        currPOvalueTotal = 0.0
        currPO = ""
        lineType = ""
        samePO = False # what if it is the same and is non fmp? what if it's the first line(s) of CSV?
        for r in POdata:
            print("240106 start of POdata loop::", myCount, r["PO #"], samePO)
            print("***** currFMP: " , currFMP, "and linetype: ", lineType)
            print("**::::", r["Project"],r["Product Description"])
            FMlead = "TBD"
            if currPO == r["PO #"]:
                print("240106 Same PO")
                samePO = True
                if currFMP == "NON FMP":
                    linetype = "nonEB"
                    print("\t****Do not look for speedtype, etc, do not write PO line just go to next row")
                else:
                    # What if multiline is first? Do we have WS?
                    print("\tcall next function with row data and FMP", currFMP, " and lineType", lineType)
                    print("Excel:", costWS, firstCost)
                    wPOC.write_PO_Cost_line(r,ebCompanies,currFundRule, currST, budgTasks, costWS, samePO, FMlead)
                    print("240106: back from write PO Cost line") #24016 never gets here
                        
            else:
                # it's not the same PO, update currPO
                currPO = r["PO #"]
                if r['PO Line #'] == '1':
                    bwValue = float(r['Extended Price'].replace(',',''))
                    currPOvalueTotal = bwValue
                r["Speedtype"] = get_Speedtype(r)
                print("1. ****!! WHAT", currPO, (currPO in activePOs))
                if currPO in activePOs:
                    print("Already in EB, check for change order")
                elif r['Origin Code'] == "LEB":
                    lineType = "EBprocess"
                    currFMP = get_FMP_from_POdata(r)
                    r['Project'] = currFMP
                    # should get from external notes field
                    if firstProcess == False:
                        processXL, processWS = ebCost.create_Excel()
                        ebCost.write_ExcelHeaders(processXL, processWS, "POprocess")
                        wPOP.write_PO_Process_line.counter = 2 # set counter for rows
                        firstProcess = True
                    currST = get_Speedtype(r)
                    wPOP.write_PO_Process_line(r, currST, processWS)
                    counts["EBprocess"] += 1
                    print("\tIt's a process: get FMP (could be in external notes\n What happens with multi line?")
                    print("\tWe only want one line in Excel\n - and other data go to write line")
                else:
                    currFMP = get_FMP_from_POdata(r)
                    currST = get_Speedtype(r)
                    currFund = r["Fund"][:-2]
                    currFund= currFund.lstrip()
                    
                    if currFMP == "NON FMP":
                        lineType = "nonEB"
                        print("***::: 240106 Skip this non eb line")
                    else:
                        r['Project'] = currFMP
                        if firstCost == False:
                            firstCost = True
                            costXL, costWS = ebCost.create_Excel()
                            ebCost.write_ExcelHeaders(costXL, costWS, "POcost")
                            wPOC.write_PO_Cost_line.counter = 2  # set counter for rows
                            print(":::: first cost, excel set up")
                        

                        lineType = "EBcostFMP"
                        currFundRule = ebCost.buildFundingRule(currST,currFund)
                        print("::::",currFundRule, currST)
                        # Need to detect/warn about multiple ST - not going to write them
                        currLead = "TBD"
                        #def write_PO_Cost_line(POrow,ebCompanies,fundRule, multST, budgTasks, ws, samePO, FMlead):
                    
                        
                        print(costWS, samePO, FMlead)
                        #write_PO_Cost_line(r,ebCompanies,currFundRule, currST, budgTasks, costWS, samePO, FMlead)
                        wPOC.write_PO_Cost_line(r,ebCompanies,currFundRule, currST, budgTasks, costWS, samePO, FMlead)
                        print("Back from write cost line")
                        counts["EBcostFMP"] += 1
                    print("\tnew PO, not process", currPO, currFMP, firstCost)
                #print ("***:::", r["PO #"], "count is", myCount)
            myCount += 1
            #print("Out of loop; count is " , myCount)
            


    # print(counts)
    print("240106 we don't get here? Done reading CSV....", theCSV)
    print('------------------')
    print(counts)

    for c in counts:
        print ("@@@@@@PO data totals", c, counts[c])
    #230731 does this exist now? add back in?print ("COs?", COcount)
    #retVal = str(counts["EBprocess"]) + str(counts["EBcost"])
    # retVal = "PO Cost Imports:" + str(counts["EBcost"])
    retVal = "PO Cost FMP Imports:" + str(counts["EBcostFMP"])
    retVal = "PO Cost Speedtype Imports:" + str(counts["EBcostST"])
    retVal += "\nPO Process Imports:" + str(counts["EBprocess"])
    print(">>>>>",retVal)
    # Check if we creeated any Excels, if so, close 'em
    #uname = getpass.getuser()
    # ofilebase = "DataFiles/" + currStamp + "_"
    # ofilebase = "C:\\Users\\K_Gattu\\PycharmProjects\\uml_python\\uml\\DataFiles\\" + currStamp + "_"
    print("First cost", firstCost)

    #ofilebase = "B:\\dailyImports\\_CSV_" + currStamp + "_"
    ofilebase = ("C:\\temp\\_" + currStamp + "_")
    
    if firstProcess == True:
        ofile = ofilebase + "POprocessImport.xlsx"
        costFile = True
        processXL.save(ofile)

    if firstCost == True:
        print("WHAT?")
        ofile = ofilebase + "POcostImport.xlsx"
        print(">>>>>", firstCost, ofile)
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
    return(retVal)
    # return ofile
    # return retVal
    
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
