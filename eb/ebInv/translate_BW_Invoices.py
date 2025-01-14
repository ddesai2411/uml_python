import csv
import chardet
import uml_python.uml_lib.ebHTML as ebHTML

"""
import ebCOST_newAPI.eb.ebCostLib as ebCost
import ebCOST_newAPI.eb.ebInv.write_Invoice_Cost_line as wINC
import uml_new.eb.ebInv.write_Invoice_Process_line as wINP
import ebCOST_newAPI.eb.ebAPI_lib as ebAPI
"""

import uml_python.uml_lib.ebCostLib as ebCost
import uml_python.eb.ebInv.write_Invoice_Cost_line as wINC
#import uml_python.ebInv.write_Invoice_Process_line as wINP
import uml_python.uml_lib.ebAPI_lib as ebAPI


def debugPrint(theStr):
    #print "Debug print:", theStr
    ignoreThis = 0

"""
June 2023
Filtering out any invoices against Type 2 commitments
- these should be using the PAYAP process and we don't to double count
- the cost
January 8, 2021
- Adding ability to handle BW Payable status
    - Bring in new, belongs-in-EB, invoice as Approved
    - Bring in BW Paid, EB Approved, via Invoice Update Import
    - Still need to detect and handle PayAp Process related new invoices
        - bring in BW "Payable" via Process Import
        - bring in BW "Paid", EB "Approved", via Invoice Update import
          same as above
"""
# September 25, 2020
# adding process support
# May 16, 2020
# Modifying logic: how do know a PO belongs to ebuilder? Previously, just used EB report. But, the only way to report
# on funding rules and speedtypes, is to report on Actuals (invoices). We were limiting filter to EB projects
# with invoices. No 1st PO on a project, no 1st invoice on PO. So, we need to also check active EB projects. We can
# get that from API. In fact, we can probably get Actuals, speedtypes, and funding rules from API too. First things
# first
# May 21, 2020
# Adding a check: is the voucher already in e-Builder? If so, skip it
# may want to refine to check dollar value
# get_Invoices is just looking for "X" as first character. That's flimsy.
# Should check EB Projects, EB POs
# May 10, 2020
#print "basic", ofilebase

# July 22, 2021
# outputting "not paid" to log file for debugging/analysis


def translate_Buyways_Invoices(theCSV, currStamp):
    print("Translating Buyways Invoices on: ", theCSV)
    logfile = open("ebInvoiceLog.txt", "w")
    retVal = ""

    budgTasks = ebCost.getBudgetTasks()
    ebST = ebAPI.get_FundingRules()
    # print ebST
    ebProjs = ebAPI.get_active_Projects()
    activePOs = ebAPI.get_activePOs(ebProjs)
    ebInvoices = ebAPI.get_Invoices()
    lineType = ""
    lineCount = 0
    firstProcess = False    # flags to create Excel
    firstCost = False
    costFile = False
    counts = {"timestamp":currStamp,
              "source":"CSV",
              "EBcost": 0,
              "EBprocess":0,
              "EBcostType2":0,
              "InProcess": 0,
              "Payable":0,
              "AlreadyInEB": 0,
              "Other":0,
              "nonEB":0,
              }

    # NOTE: Noticed the encoding type of csv file is not same always,
    # so adding code to check encoding of the file before reading the rows Just in Case
    with open(theCSV, 'rb') as f:
        result = chardet.detect(f.read())
        encodingFormat = result['encoding']
    print(encodingFormat)
    with open(theCSV,encoding=encodingFormat) as csvfile:
        InvData = csv.DictReader(csvfile,delimiter=',') #quotecharacter?
        errorLine = []
        errorST = []
        for r in InvData:
            #print(r.keys())
            # 200925 Adding support for process vs cost. Still not filtering - assuming all belong in EB
            # No filtering: send all lines to Cost import. Assumption is that we run a BW report on EB POs
            #print "??????>>>>>>", r["Invoice No"], r['PO No']
            lineCount += 1
            #print "Line number: ", lineCount
            # print(">>>>",r["Invoice No"])
            if r["Invoice No"] in ebInvoices:
                print("Already in EB", r["Invoice No"])
                counts["AlreadyInEB"] += 1
            elif r['PO No'] in activePOs and activePOs[r['PO No']]["CommitmentType"][0] != '2': # what about PO reqs? If origin code is LEB, check custom field? or always custom field?
                print("Not already in EB:", r["Invoice No"])
                # 230630: Check commitment type (or filter out type 2s?)
                
                currFMP = activePOs[str(r['PO No'])]["FMP"]
                #print(currFMP)
                debugPrint(currFMP)
                r['Project'] = currFMP
                if r["Invoice Status"] == "Paid" or r["Invoice Status"] == "Payable" :# Will change when we add payables
                    #print "FMP, needed for both cost and process, is:", currFMP, r['PO No']
                    # THIS section goes away when we check for ebProccess
                    lineType = "EBcost" # will change to non EB if we don't find speedtype
                    debugPrint(lineType)
                    counts[lineType] += 1
                    print(firstCost)
                    # Check this before process? we need it in both?

                    if firstCost == False:
                        #print "Create Cost Excel file"
                        # get output file name and pointer to Excel/openpyxl
                        costXL, costWS = ebCost.create_Excel()
                        #print "Writing Invoice Cost headers"
                        ebCost.write_ExcelHeaders(costXL, costWS, "InvoiceCost")
                        wINC.write_Invoice_Cost_line.counter = 2 # set counter for rows
                        firstCost = True
                    debugPrint( "......Write Cost line to excel")
                    # 201117 Shouldn't we just check the PO?????
                    BW_ST = r['Speedtype'][:-2]
                    #print "****", BW_ST
                    #print ">>>>", ebST[BW_ST]["Name"]
                    try:
                        #currFundRule = ebST[BW_ST]["FundSource"] + "-" + BW_ST
                        currFundRule = ebST[BW_ST]["Name"]
                       
                        #currFundRule = "Rule 1 " + ebST[BW_ST]["FundSource"]
                    except:
                        try:
                            currFundID = r["Fund"][:-2]
                            print(">>>>",currST, currFundID)
                            currFundRule = ebCost.buildFundingRule(currST, currFundID)
                            print(">>>>",currFundRule, type(currFundRule))
                        except:
                            print("Why are we here????")
                            currFundRule = "CHECK FUNDING RULE"
                    #print( "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@Current funding rule", currFundRule, type(currFundRule))
                    wINC.write_Invoice_Cost_line(r, activePOs, currFundRule, "CHECK_THIS", costWS)
                # REWORK THIS: WE ARE CHECKING acivePOs twice. I can't get elif working
                

                elif r['Invoice Status'] == "In Process": # Not EB
                    lineType = "InProcess"
                    counts[lineType]+=1
                elif r['Invoice Status'] == "Payable": # Not EB
                    lineType = "Payable"
                    oStr = str(currFMP) + "," + r['PO No'] + "," + r['Invoice No'] + "," + r['Invoice Status'] + "\n"
                    print(oStr)
                    logfile.write(oStr)
                    counts[lineType]+=1
            elif r['PO No'] in activePOs and activePOs[r['PO No']]["CommitmentType"][0] == '2': # what about PO reqs? If origin code is LEB, check custom field? or always custom field?
                    print ("Got to type 2")
                    lineType = "EBcostType2"
                    counts[lineType] += 1
            else:
                lineType = "Other"
                counts[lineType]+=1
    logfile.close()

    print("Done reading CSV", theCSV)

    print('-----------')
    print(counts)

    for c in counts:
        print("Invoice Data totals", c, counts[c])

    retVal = "Invoice Cost Imports: " + str(counts["EBcost"])
    retVal += "\nInvoice Process Imports (currently not used): " + str(counts["EBprocess"])
    #uname = getpass.getuser()
    #print currStamp

    #ofilebase = "DataFiles/" + currStamp + "_"
    ofilebase = "B:\\dailyImports\\_CSV_" + currStamp + "_"
    # INVhtml = "B:\\dailyImports\\_InvoiceDataTotals.html"

    #ofilebase = "/Users/kysgattu/FIS/BDrive/dailyImports/_CSV_" + currStamp + "_"
    #INVhtml = "/Users/kysgattu/FIS/BDrive/dailyImports/_kysTestInvoiceDataTotals.html"
    INVhtml = "\\\\UML-BW2EB-01.fs.uml.edu\\bw2eb\\_InvoiceDataTotals.html"

    # ebHTML.checkHTMLfile(INVhtml, counts,"Invoice", "") -- This is redundant
    
    if firstCost == True:
        ofile = ofilebase + "InvoiceCostImport.xlsx"
        costXL.save(ofile)
        costFile = True
    if firstProcess == True:
        ofile = ofilebase + "InvoiceProcessImport.xlsx"
        processXL.save(ofile)
        costFile = True
    if costFile:
        retval = {'Stats': counts, 'ImportFile': ofile}
        return retval
        # return ofile
    else:
        retVal = {'Stats':counts, 'ImportFile': 'No EBCost Invoices'}
        # print(retVal)
        return retVal
        # return 'No EBCost POs'

    # retval = {'Stats':counts,'ImportFile':ofile}
    # print(retval)
