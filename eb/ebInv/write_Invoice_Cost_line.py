# March 24, 2022: Buyways changes included field names for invoice report - see PO line number, tax 1 and tax 2

def debugPrint(theStr):
    #print "Debug print:", theStr
    ignoreThis = 0


def parseStr(s):
    safeStr = ""
    for c in s:
        if c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 /-.&$":
            safeStr += c
        else:
            safeStr += " "
    #print safeStr
    if len(safeStr) > 400:
        safeStr = safeStr[:400]
    return safeStr

def write_Invoice_Cost_line(POrow, activePOs, fundRule, multiLine, ws):
    # 210123    Now, an invoice dictionary to handle multi line invoices
    # 201104:   All invoices are treated as Cost because of UPST, email to invoices@umassp.edu and inability to pass docs
    #           through integration
    print( ">>>>>write_Invoice_Cost_line", type(fundRule))
    padLine = False
    #print "!!!!!!!!!!!!!!!!!",POrow["Invoice No"]
    if POrow['External Req #'][:7] == "L-POREQ":
        #print "Came from POREQ integrated Process"
        #print POrow['Origin Code']
        padLine = True
    else:
        padLine = False
    # 1: FMP Number - not in CSV, we looked up the speedtype to get it and changed CSV field Project
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=1)
    outCell.value = POrow["Project"]

    # 2: Invoice Number: which one? We'll use BW Voucher
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=2)
    outCell.value = POrow["Invoice No"]

    # 3: Vendor Invoice #
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=3)
    outCell.value = POrow["Supplier Invoice No"]

    # 4: Commitment Number (BW, verify exists in EB?)
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Old, imported will LXXXX, like BW. New, will be "POREQ - 00023"
    # So, we need to look up PO No (old imported EB POs). If not there, check custom date field
    # and get the POREQ - XXXX from the ebPOs dictionary
    # ADD CUSTOM DATA FIELD TO DICTIONARY

    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=4)
    if POrow["Origin Code"] == "LEB":
        commitNum = POrow["External Req #"][2:] # strip "L-" from beginning of this field, to get POREQ - XXXX
    else:
        commitNum = POrow["PO No"]
    #print "?>?>?", POrow["PO No"]
    outCell.value = commitNum
    #POrow["PO No"]  # What if it was created in EB??? Then, we need another lookup

    # 5: Description
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=5)
    #outCell.value = POrow[r['PO No']]["Desc"] # need another look up
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #outCell.value = "See PO"
    # MAY NEED TO SAFEIFY THIS!!!!
    outCell.value = parseStr(POrow['Product Name'])

    # 6: Invoice Item Amount
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=6)
    """
    # Check with FM Procurement: should we ignore Tax?
    if (int(POrow["PO Line No"]) == 1): # so we don't add these more than once -- BW has them at the header
        lineTotal += float(POrow["Tax1 Charge"]) + float(POrow["Tax2 Charge"])
        lineTotal += float(POrow["Shipping Charge"]) + float(POrow["Handling Charge"])
        print "SHIPPING!!!???", POrow["Shipping Charge"]
        # check true/false on Early Payment discount?
        if POrow["Apply Early Payment Discount"] == "TRUE" or POrow["Apply Early Payment Discount"] == "true":
            #if int(float(POrow["Early Payment Discount"])) > 0:
            lineTotal -= float(POrow["Early Payment Discount"])
        #else:
            #lineTotal += float(POrow["Early Payment Discount"])
    """
    # 230703 CHECK THIS: HOW DO WE KNOW MULTILINE? VOUCHER ID?
    if multiLine:
        lineTotal = POrow["Invoice Line Extended Price"]
    else:
        lineTotal = POrow["Invoice Total"]
    outCell.value = str(lineTotal)

    # 7: Commitment Item number
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=7)
    if padLine == True:
        while len(POrow["PO Line No"]) < 3:
            POrow["PO Line No"] = "0" + POrow["PO Line No"]
        #print "!?!?!?!?!!?!", POrow["PO Line No"]
    #else:
        #print "WHAT?"
    outCell.value = POrow["PO Line No"]

    # 8: Funding Rule: Not in CSV, look up in EB Import Support Report
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=8)
    try:
        print("WHAT??",type(fundRule))
        #fundRule
        outCell.value = fundRule.encode() # Passed in

    except:
        outCell.value = "CHECK FUNDING RULE"

    # 9: Voucher ID - repeating Invoice Number - this is for custom fields, reporting
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=9)
    outCell.value = POrow["Invoice No"]

    # 10: Status
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=10)
    if POrow["Invoice Status"] == "Payable":
        outCell.value = "Approved"
    elif POrow["Invoice Status"] == "Paid": # This works: EB will show as actual cost against PO
        outCell.value = "Paid"              # But, how do/do we eventually mark it Paid?
    else:
        outCell.value = (POrow["Invoice Status"] + " ERROR!!!!")

    # 11: "Approved Date"
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=11)
    outCell.value = POrow["Invoice System Created Date"]

    # 12: "Amount this Period"
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=12)
    outCell.value = str(lineTotal)

    # 13: "Stored Materials"
    outCell = ws.cell(row=write_Invoice_Cost_line.counter,column=13)
    outCell.value = "0"

    # 14: "Quantity"
    try:
        currQuant = POrow["Quantity"]
        outCell = ws.cell(row=write_Invoice_Cost_line.counter, column=13)
        outCell.value = currQuant
    except:
        noQuant = True

    write_Invoice_Cost_line.counter += 1
