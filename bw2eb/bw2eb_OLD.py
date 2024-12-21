import time, shutil, os, getpass
from datetime import datetime
"""
import ebCOST_newAPI.eb.ebCostLib as eb
import ebCOST_newAPI.eb.ebPO.translate_BW_POs as tPO
import ebCOST_newAPI.eb.ebInv.translate_BW_Invoices as tIN
"""

import uml_V2.uml_lib.ebCostLib as eb
import uml_V2.eb.ebPO.translate_BW_POs as tPO
import uml_V2.eb.ebInv.translate_BW_Invoices as tIN

"""
v10p0
PURPOSE:  Check for Buyways reports and, if appropriate, process them for
          import to EBuilder
METHOD:   Check _fromBuyways on I: drive. Inspect CSVs, if any, and translate to EB imports as appropriate                                         
INPUT:    Files in "_fromBuways"
OUTPUT:   If needed, timestamped Excel files in "_toEBuilder"
          1. PO Cost import
          2. PO Process Import
          3. Invoice Cost Import
          4. Invoice Process Import
Roadmap:
1. Add cost invoice fields for commitment types 2 and 3
2. Revise funding rules, including "CHECK FUNDING RULES"
3. ADD COMMODITY CODE - JUST COST, JUST PO?
4. Revise so TEST files get "TEST" in name. maybe all files get original name in processed name?
    also, send TEST files to other destination?
5. Confirm that invoice line totals, shipping, tax are working
6. Revise log/HTML. Aim for one eb Update page, with:
    - FMP numbers
    - Draft POs
    - Imports log/status
    - COs, potential COs, POs with values that don't match
    - Summit reconcile
200630
- Log to JSON for new web page
"""


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


def checkCSV(CSVfile, currStamp):
    # retVal = ""

    cat = eb.checkBWcsv(CSVfile)
    # print(cat)
    if cat == "notBW":
        # print("Not a BW CSV", CSVfile)
        # renameCSV(srcDir, theCSV,cat)
        fileSuffix = cat
        retVal = 'Not a BW CSV'
    elif cat == "File Not Found":
        print("Did not find:", CSVfile)
        # renameCSV(srcDir, theCSV,cat)
        fileSuffix = "notBW"
        retVal = "File Not Found"
    else:
        if cat == "isPO":
            # print("Translating BW PO")
            tstamp = tstamper2()
            # print(tstamp, ": Going to POs and Translating BW POs", CSVfile)
            # retVal += CSVfile + "\n"
            try:
                results = tPO.translate_Buyways_POs(CSVfile, currStamp)
                # fileSuffix = "What?"
                # retVal += results
                retVal = results
                # return results
            except:
                retVal = "No results"

        else:
            # print("Translating BW Invoice")
            # ebInvoices = ebAPI.get_Invoices()
            tstamp = tstamper2()
            # print(tstamp, ": Going to translate Invoices and Translating BW Invoices", CSVfile)
            # retVal += CSVfile + "\n"
            results = tIN.translate_Buyways_Invoices(CSVfile, currStamp)
            retVal = results
    # print('BOooooooooooooooo')
    # print(retVal)
    return retVal


def main(CSVfile):
    # print "Got 'em", CSVfile
    # print(" Version 230728a: retainage restored")
    starttime = time.time()

    currTime = time.time()
    # 200930 Updated time stamp to YYMM instead of YYYYMM
    currStamp = tstamper2()
    pyFile = os.path.basename(__file__)
    # print("Running", pyFile)
    print("Python started", currStamp, " running", pyFile)

    resultStr = checkCSV(CSVfile, currStamp)
    print("Python commpleted\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print(resultStr)
    return resultStr
    # return (currStamp + "\n" + resultStr)

if __name__ == "__main__":
    # main('DataFiles/transaction_export_po_search_POData884686266.csv')
    # main('/Users/kysgattu/FIS/ebCost/ebCOST_newAPI/DataFiles/KTest/transaction_export_buyer_invoice_search_InvoiceData-850308942.csv')
    # main('DataFiles/transaction_export_po_search_POData-656071530.csv')
    main("C:\\temp\\240106_PO_multiLineTest_nonFMPfirst.csv")
    # main()
