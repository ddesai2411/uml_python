import glob,os,shutil
import zipfile

import uml_python.bw2eb.bw2eb as bw2eb
import uml_python.uml_lib.ebCostLib as ebCost
import uml_python.uml_lib.web_lib as UMLweb

# Purpose: Get the Buyways Reports in the form of "ZIP" files in the directory.
# Extract the Zip Files to get the .CSV Reports
# Check for Buyways Reports of all the POs and Invoices in the directory
# and process them to an Excel Sheet Report for importing to EBuilder
# and return HTML Pages with counts of POs and Invoices of each category
# This code uses bw2eb for  translating POs and Invoices,
# ebCostLib for joining the reports and creating HTML page


def main():
    currStamp = UMLweb.tstamper2()

    # Modify Paths below accordingly
    # theDir = 'C:\\Users\\K_Gattu\\PycharmProjects\\uml_python\\uml\\DataFiles\\fromBuyways_reports\\'
    # processed_Dir = theDir + 'processed\\'
    # ofilebase = 'C:\\Users\\K_Gattu\\PycharmProjects\\uml_python\\uml\\outputfiles\\' + currStamp + "_"

    
    theDir = "B:\\dailyImports\\fromBuyways_reports\\"
    processed_Dir = theDir + "processed\\"
    ofilebase = "B:\\dailyImports\\_CSV-ZIP_" + currStamp + "_"

    zip_files = []
    for file in os.listdir(theDir):
        if file.endswith('.zip'):
            zip_files.append(os.path.join(theDir, file))

    for zip_file in zip_files:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(theDir)
        # os.remove(zip_file)
        zip_filename = os.path.basename(zip_file)
        move_dest = os.path.join(processed_Dir, zip_filename)

        # if not os.path.exists(move_dest):
        #     shutil.move(zip_file, processed_Dir)
        # else:
        #     os.remove(zip_file)

    POFiles = glob.glob(theDir + "*po_search*.csv")
    invFiles = glob.glob(theDir + "*invoice_search*.csv")

    bw2ebPOs = []
    for i in POFiles:
        print("Translating ", i)
        POImport = bw2eb.main(i)
        bw2ebPOs.append(POImport)
        os.remove(i)

    bw2ebInvs = []
    for i in invFiles:
        print("Translating ", i)
        invImport = bw2eb.main(i)
        bw2ebInvs.append(invImport)
        os.remove(i)
    print('------------')
    print(bw2ebPOs,"\n",bw2ebInvs)
    print('------------')
    # for i in range(len(bw2ebInvs)):
    #     print(i)
    POCounts = {"Timestamp":"",
                "Source": "CSV_ZIP",
                "EBprocess": 0,
                # "EBcostST": 0,
                # "EBcostFMP": 0,
                "EBcost": 0,
                "EBexists": 0,
                "EBexistsCO?": 0,
                "nonEB": 0,
                "nonUML":0}
    COs = {'PO Number':'FMP Number'}
    importPOFiles = []
    for i in range(len(bw2ebPOs)):
        if type(bw2ebPOs[i]) == dict:
            # print(">>",bw2ebPOs[i]['Stats'])
            try:
                POCounts["Timestamp"] = bw2ebPOs[i]['Stats']['Timestamp']
            
                POCounts["EBprocess"] += bw2ebPOs[i]['Stats']['EBprocess']
                # POCounts["EBcostST"] += bw2ebPOs[i]['Stats']['EBcostST']
                # POCounts["EBcostFMP"] += bw2ebPOs[i]['Stats']['EBcostFMP']
                POCounts["EBexists"] += bw2ebPOs[i]['Stats']['EBexists']
                POCounts["EBexistsCO?"] += bw2ebPOs[i]['Stats']['EBexistsCO?']
                POCounts["nonEB"] += bw2ebPOs[i]['Stats']['nonEB']
                POCounts["nonUML"] += bw2ebPOs[i]['Stats']['nonUML']
                # print(">>",bw2ebPOs[i]['ChangeOrders'])
                if bw2ebPOs[i]['ChangeOrders'] != 'No changeOrders':
                    COs.update(bw2ebPOs[i]['ChangeOrders'])
            except:
                print("Timestamp failed")
                
            if bw2ebPOs[i]['ImportFile'].endswith('.xlsx'):
                importPOFiles.append(bw2ebPOs[i]['ImportFile'])
            
        # print("<<",COs)

    InvoiceCounts = {"Timestamp":"",
                     "Source":"CSV_ZIP",
                     "EBcost":0,
                     "EBprocess": 0,
                     "EBcostType2(PAYAPs)":0,
                     "InProcess":0,
                     "Payable": 0,
                     "AlreadyInEB": 0,
                     "Other":0,
                     "nonEB":0}
    importInvFiles = []
    for i in range(len(bw2ebInvs)):
        if type(bw2ebInvs[i]) == dict:
            InvoiceCounts["EBcost"] += bw2ebInvs[i]['Stats']['EBcost']
            InvoiceCounts["EBprocess"] += bw2ebInvs[i]['Stats']['EBprocess']
            InvoiceCounts["EBcostType2(PAYAPs)"] += bw2ebInvs[i]['Stats']['EBcostType2']
            InvoiceCounts["InProcess"] += bw2ebInvs[i]['Stats']['InProcess']
            InvoiceCounts["Payable"] += bw2ebInvs[i]['Stats']['Payable']
            InvoiceCounts["AlreadyInEB"] += bw2ebInvs[i]['Stats']['AlreadyInEB']
            InvoiceCounts["Other"] += bw2ebInvs[i]['Stats']['Other']
            InvoiceCounts["nonEB"] += bw2ebInvs[i]['Stats']['nonEB']

            if bw2ebInvs[i]['ImportFile'].endswith('.xlsx'):
                importInvFiles.append(bw2ebInvs[i]['ImportFile'])

    print(importPOFiles,"\n----\n",importInvFiles)
    # if len(importPOFiles)>0:
    #     POWorkBook = ebCost.joinReports(importPOFiles)
    #     importPOFile = ofilebase + 'POcostImportJoinedData.xlsx'
    #     POWorkBook.save(importPOFile)
    #     print('Report Saved at:',importPOFile)
    # else:
    #     importPOFile = ""
    #     print('No Cost PO Import Files Found')
    #
    # if len(importInvFiles)>0:
    #     InvWorkBook = ebCost.joinReports(importInvFiles)
    #     importInvFile = ofilebase + 'InvoicecostImportJoinedData.xlsx'
    #     InvWorkBook.save(importInvFile)
    #     print('Report Saved at:',importInvFile)
    # else:
    #     importInvFile = ""
    #     print('No Invoice Import Files Found')

    importFiles = {"POCost":[],
                 "POProcess":[],
                 "InvoiceCost":[],
                 "InvoiceProcess":[]
                 }

    if len(importPOFiles) > 0:
        for i in importPOFiles:
            if i.endswith('POcostImport.xlsx'):# and i not in importFiles["POCost"]:
                importFiles["POCost"].append(i)
            elif i.endswith('POprocessImport.xlsx'):
                importFiles["POProcess"].append(i)

    if len(importInvFiles) > 0:
        for i in importInvFiles:
            if i.endswith('InvoiceCostImport.xlsx'):
                importFiles["InvoiceCost"].append(i)
            elif i.endswith('InvoiceProcessImport.xlsx'):
                importFiles["InvoiceProcess"].append(i)

    print(">>>\n",importFiles,"\n>>>")
    joinedImportFiles = []
    for i in importFiles:
        if len(importFiles[i]) > 0:
            importFiles[i] = list(set(importFiles[i]))
            print("|",importFiles[i],"|")
            WorkBook = ebCost.joinReports(importFiles[i])
            JoinedimportFile = ofilebase + str(i) +'ImportJoinedData.xlsx'
            WorkBook.save(JoinedimportFile)
            print('Report Saved at:',JoinedimportFile)
            joinedImportFiles.append(JoinedimportFile)
        else:
            JoinedimportFile = ""
            print('No ' + str(i) + ' Import Files Found')

    # July 7, 2023 Changing to use web_lib version, which outputs
    # to a single HTML page for PO and Invoices, instead of 1 page
    # per run

    try:
        currTime = UMLweb.tstamper2()
    except:
        currTime = "NO_CURR_TIME"
    
    
    POCounts["Timestamp"] = currTime
    InvoiceCounts["Timestamp"] = currTime

    print('------------------------------------------------------------')
    print('Stats of Cost Invoices:',InvoiceCounts)
    print('Stats of Cost POs:',POCounts)


    #POHTMLData = ebCost.makeStatsHTML(POCounts, "PO Data Counts")
    # thePath = "B:\\dailyImports\\TEST\\_TEST_PODataTotals.html"
    thePath = "/Users/kysgattu/FIS/BDrive/dailyImports/TEST/_TEST_PODataTotals.html"
    # COs = bw2ebPOs[]
    TestCOs = {
        "12345678":"123456",
        "12345690":"246800"
    }
    # print(COs)

    print("????",POCounts["EBexistsCO?"])
    UMLweb.outputHTML("PO", currTime, POCounts,COs)
    """
    POHTML = ofilebase + "POCostDataCounts.html"
    POHTMLFile = open(POHTML,"w")
    POHTMLFile.write(POHTMLData)
    """
    #UMLweb.outputHTML("PO", POHTMLData)
    #InvoiceHTMLData = ebCost.makeStatsHTML(InvoiceCounts, "Invoice Data Counts")
    thePath = "/Users/kysgattu/FIS/BDrive/dailyImports/TEST/_TEST_InvoiceDataTotals.html"
    # thePath = "B:\\dailyImports\\TEST\\_TEST_InvoiceDataTotals.html"
    print(InvoiceCounts)
    UMLweb.outputHTML("Invoice", currTime, InvoiceCounts, COs)
    
    """
    InvoiceHTML = ofilebase + "InvoiceCostDataCounts.html"
    InvoiceHTMLFile = open(InvoiceHTML,"w")
    InvoiceHTMLFile.write(InvoiceHTMLData)
    
    POHTMLFile.close()
    InvoiceHTMLFile.close()
    """
    # files = {"POImport": importPOFile,
    #          "InvoiceImport": importInvFile,
    #          "POTotals": "REPLACED",
    #          "InvoiceTotals": "REPLACED"
    #          }

    files = joinedImportFiles
    print(files)
    return files


if __name__ == "__main__":
    main()
