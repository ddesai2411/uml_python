"""
9/3/2021: added FMlead for filtering POs (not importing O&S)
"""
#import uml_new.eb.ebAPI_lib as ebAPI
import uml_python.uml_lib.ebAPI_lib as ebAPI
#import ebCOST_newAPI.eb.ebAPI_lib as ebAPI

def debugPrint(theStr):
    print("Debug print:", theStr)
    ignoreThis = 0

def padstr2(s, l):
    retVal = s
    if len(s) < l:
        for i in range(0,l-len(s)):
            retVal = "0" + retVal
    return retVal


def write_PO_Cost_line(POrow,ebCompanies,fundRule, multST, budgTasks, ws, samePO, FMlead):
    """
    r, currFundRule, multipleST, costWS, samePO
    201016
    Need to check if this came from integration. Check for External Req #. If so, we need to pad line numbers
    to 3-digits
    To write multi-line POs, we can rewind the description writing?
    Yes
    2020-06018
    - Commitment types 2 and 3 require additional fields (quantity, date, UOM?)
    - Funding rule: we're changing so it's named by the fund
    """
    # Need to pass in Funding Rule and Commitment type, or look them up. We may know them from EB report or API
    # or, we may not if no invoice has been processed
    #print POrow
    # Key here, pun intended, is to cull the fields we want from the PO data dictionary and write them in the right order to Excel
    #
    # Should this be global?? Is it needed in INvoices?
    #budgTasks = getBudgetTasks()
    print(">>>>>????? from write line -- what?")
    padLine = False
    #print("?????????? from write_line", POrow['PO Line #'], samePO)
    #CHECK THIS - SPACES NEEDED IN L-POREQ??? 201021
    if POrow['External Req #'][:7] == "L-POREQ":
        print ("Came from POREQ integrated Process")
        #print POrow['Origin Code']
        padLine = True
    else:
        padLine = False

    #print "Write line", POrow["PO #"], POrow["Speedtype"], POrow["Project"]
    errorLine = []
    # CHECK HEADERS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # 1: Commitment number - This is a non-integrated PO, started outside e-builder. We'll use the PO # for the commitment number
    # Will speedtype exist??? Need to mix test2 in wit test3, mix LEB and SCI
    outCell = ws.cell(row=write_PO_Cost_line.counter, column=1)
    outCell.value = POrow['PO #'] # to match EB commitment name
    # debugPrint(POrow['PO #'])

    # 2: FMP Number
    outCell = ws.cell(row=write_PO_Cost_line.counter, column=2)
    outCell.value = POrow["Project"] # We looked this up from the EB report (ebPOs) and changed the PS Project ID that BW had
    # debugPrint(POrow["Project"])
    # if FMP number does not exist in POrow["Project"] look for it in "Header Notes" add it here and continue adding other fields too??

    # 3: Commitment type: we won't know, Buyways doesn't know. Wrong type will cause problems. Is it required?
    outCell = ws.cell(row=write_PO_Cost_line.counter, column=3)
    #outCell.value = "1. Purchase Order"

    currBWsupplierName = POrow["Supplier Name"]
    currBWsupplierNum = POrow["Supplier Number"]
    currBWsupplierNum = padstr2(currBWsupplierNum, 10)
    # print(">>>>>>>@@!@! BW values", currBWsupplierNum, len(currBWsupplierNum))
    try:
        #print ">>>>>>>.......................", ebCompanies[currBWsupplierNum]
        currEBsupplierName = ebCompanies[currBWsupplierNum]
    except:
        #print "WHAT?"
        currEBsupplierName = "NOT FOUND"
    #print ">>>>>>>@@!@! BW values", currBWsupplierName, currBWsupplierNum
    commitType = ebAPI.get_commitType(currEBsupplierName)

    # print ("OK: ", commitType)
    #commitType = "CHECK"
    #print(">>>???", FMlead)
    if FMlead == "O&S":
        print("Got here")
        outCell.value = "1. Purchase Order"
    else:
        outCell.value = commitType
    # debugPrint(commitType)

    # 4: Company Name
    # 8/12/2022 Need to get Supplier ID and check EB for the name as entered IN EB. We have minor spelling/character
    # differences plus "doing business as" issues that make Name unreliable
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=4)
    outCell.value = currEBsupplierName
    # debugPrint(currEBsupplierName)

    # 5: Budget Line Item - is this supposed to be Description? Can it be instead?
    # 240209 For O&S projects, Bus Ops now wants all POs to go against the 99 Contingency line
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=5)
    currLine = str(POrow['Account'])
    #print currLine, currLine[:-2]
    # 200219 CAREFUL: CHECK what we're doing in POs
    #print "Current line", currLine, currLine[:-2], budgTasks[currLine[:-2]]
    if FMlead == "O&S":
        ebLine = "99.99CONT"
        print("240209: O&S Contingency")
    else:
        try:
            print("240209: FM lead O&S didn't work:", FMlead)
            ebLine = budgTasks[currLine[:-2]]
            #print ebLine
        except:
            #print "Account Not Found",str(r['Account'][:6])
            # CAUTION: Changing line item to Contingency if line item is not in eb
            ebLine = "99.99CONT"
            #print ">>>Not found:", r['Account'][:6]
            errorLine.append(POrow['Account'])
            # debugPrint("Error" + POrow['Account'])

    # debugPrint(ebLine)
    outCell.value = ebLine

    # 6: Status --
    # Old - Always Draft, manual approval required
    # 230308 Chaning from Draft to Approved. Too many problems with Draft
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=6)
    outCell.value = "Approved"
    # debugPrint('Approved')


    # 7: Item Number
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=7)
    if padLine == True:
        while len(POrow["PO Line #"]) < 3:
            POrow["PO Line #"] = "0" + POrow["PO Line #"]
    outCell.value = POrow["PO Line #"]
    # debugPrint(POrow["PO Line #"])

    # 8: Description - !!???
    if len(POrow["Product Description"]) > 365:
        #print "Description is too long"
        POrow["Product Description"] = "SEE BUYWAYS FOR FULL DESCRIPTIONS " + POrow["Product Description"][0:364]

    if samePO:
        currPOline = int(POrow['PO Line #'])
        print("???? from write_line, samePO desc", currPOline)
              
        for i in range(1,currPOline):
            print("????", i, write_PO_Cost_line.counter-1)
            outCell = ws.cell(row=(write_PO_Cost_line.counter-i),column=8)
            outCell.value = POrow["Product Description"]
        # now get current (last/highest row of samePO)
        outCell = ws.cell(row=(write_PO_Cost_line.counter),column=8)
        outCell.value = POrow["Product Description"]
            
    else:
        outCell = ws.cell(row=write_PO_Cost_line.counter,column=8)
        # safeifying this in function above - concatenating for multi lines there too
        outCell.value = POrow["Product Description"]
    # debugPrint(POrow["Product Description"])

    # 9: Item Quantity
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=9)
    outCell.value = POrow["Quantity"]
    # debugPrint(POrow["Quantity"])

    # 10: Item Unit Cost
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=10)
    outCell.value = POrow["Unit Price"]

    # 11: Commitment Date
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=11)
    outCell.value = POrow["Creation Date"]

    # 12: Company Number
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=12)
    compNum = str(POrow["Supplier Number"]).zfill(10)
    outCell.value = compNum

    # 13: Commitment Item Amount
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=13)
    outCell.value = POrow["Extended Price"]

    # 14: Item Unit of Measure
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=14)
    outCell.value = POrow["Amount/UOM & UOM"]

    # 15: Funding Rule - we looked this up. How do we retrieve it???
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=15)
    try:
        # 201016 We have the rule (fund + hyphen + speedtype)
        # Passed in from translate function. Error checking in translate??
        # 200711 appending "-" and speedtype to fund, to ensure unique for each project
        outCell.value = fundRule
    except:
        outCell.value = "CHECK FUNDING RULE"

    # 16: Speedtype
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=16)
    # outCell.value = POrow["Speedtype"]
    if "-L" in POrow["Speedtype"]:
        theST = POrow["Speedtype"][:-2]
        # print("writing st:", theST, POrow["Speedtype"])
        outCell.value = theST
    else:
        outCell.value = POrow["Speedtype"]

    # 17: PeopleSoft PO # - custom field, for reporting, repeats commitment number for Cost imports
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=17)
    outCell.value = POrow["PO #"]

    # 18: Origin Code - confirmation only, not imported
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=18)
    outCell.value = POrow["Origin Code"]

    # 19: Commodity Code -
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=19)
    outCell.value = POrow["Commodity Code"]

    # 20: Retainage -
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=20)
    if commitType == "2. Purchase Order for Ch. 149+30/39M Contractors":
        retainage = str(5)
    else:
        retainage = "0"
    outCell.value = retainage

    # 21: Notes: add original speedtype to document multiple speedtypes
    outCell = ws.cell(row=write_PO_Cost_line.counter,column=21)
    outCell.value = multST
    if FMlead == "FMP XXXXXX":
        outCell.value += "\nCheck FMP is XXXXXXX"

    # print("XXXX", outCell.value)

    write_PO_Cost_line.counter += 1
    # print(write_PO_Cost_line.counter)

