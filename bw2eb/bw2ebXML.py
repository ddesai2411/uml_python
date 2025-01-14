import uml_python.uml_lib.ebAPI_lib as eb
import uml_python.eb.ebPO.POCostXMLtoExcelExport as POXML
import uml_python.eb.ebInv.InvoiceCostXMLtoExcelExport as InvXML

# print(files)

"""
Imports data from the XML Files and returns the Excel Reports of the POs and Invoices
Creates HTML Files too??
"""

def main():
    fundRules = eb.get_FundingRules()
    ebProjs = eb.get_Projects()
    activePOs = eb.get_activePOs(ebProjs)

    vendorTypes = {}
    eb.build_commitTypes(activePOs)
    print("PROCESSING PO XML REPORTS....")
    PO_Report = POXML.main()
    print("PROCESSING INVOICE XML REPORTS....")
    Inv_Report = InvXML.main()
    files = {"POReport": PO_Report['po_report_excel'],
             "InvoiceReport": Inv_Report['invoice_report_excel'],
             "PAYAPInvoiceReport": Inv_Report['PAYAP_report_excel'],
             "POStats": PO_Report['stats_html'],
             "InvoiceStats": Inv_Report['stats_html']
             }
    return files

if __name__ == "__main__":
    main()