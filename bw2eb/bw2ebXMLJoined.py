import os
import datetime
import glob
import uml_python.uml_lib.ebCostLib as ebCost
import uml_python.bw2eb.bw2eb as bw2eb

def main():
    currStamp = bw2eb.tstamper2()
    joinedPOImportFiles = []
    joinedinvImportFiles = []
    joinedPAYAPinvImportFiles = []
    oDir = "/Users/kysgattu/FIS/BDrive/dailyImports/_XML_"
    # poXMLReports = glob.glob(oDir + "*_POcostImport.xlsx")
    poXMLReports = [file for file in glob.glob(oDir + "*_POcostImport.xlsx") if "_JOINED_" not in file]
    invoiceXMLReports = [file for file in glob.glob(oDir + "*_InvoicecostImport.xlsx") if "_JOINED_" not in file]
    payapInvoiceXMLReports = [file for file in glob.glob(oDir + "*_PAYAP_InvoicecostImport.xlsx") if "_JOINED_" not in file]

    files = {"POReport":poXMLReports,
             "InvoiceReport":invoiceXMLReports,
             "PayapInvoiceReport":payapInvoiceXMLReports}

    if len(poXMLReports) > 0:
        poWorkBook = ebCost.joinReports(list(set(poXMLReports)))
        joinedPOReport = oDir + currStamp + "_JOINED_POcostImport.xlsx"
        poWorkBook.save(joinedPOReport)
        print('Report Saved at:', joinedPOReport)
        joinedPOImportFiles.append(joinedPOReport)

    if len(invoiceXMLReports)>0:
        invWorkBook = ebCost.joinReports(list(set(invoiceXMLReports)))
        joinedinvReport = oDir + currStamp + "_JOINED_invcostImport.xlsx"
        invWorkBook.save(joinedinvReport)
        print('Report Saved at:', joinedinvReport)
        joinedinvImportFiles.append(joinedinvReport)

    if len(payapInvoiceXMLReports)>0:
        PAYAPinvWorkBook = ebCost.joinReports(list(set(payapInvoiceXMLReports)))
        joinedPAYAPinvReport = oDir + currStamp + "_JOINED_PAYAPinvcostImport.xlsx"
        PAYAPinvWorkBook.save(joinedPAYAPinvReport)
        print('Report Saved at:', joinedPAYAPinvReport)
        joinedPAYAPinvImportFiles.append(joinedPAYAPinvReport)

    files = {"POReport": joinedPOImportFiles,
             "InvoiceReport": joinedinvImportFiles,
             "PAYAPInvoiceReport": joinedPAYAPinvImportFiles}
    return files

if __name__ == '__main__':
    main()