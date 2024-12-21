import shutil, os
from pathlib import Path
import pandas as pd


def makeHTMLHead(InvOrPO):
    htmlHead = "<!DOCTYPE html>\n<html>\n<head>\n<title>"
    if "InvOrPO" == "Invoice":
        htmlHead += "Invoice Data Totals"
    else:
        # assuming it's PO
        htmlHead += "Purchase Order"
    htmlHead += "</title>\n</head>\n"
    return htmlHead


def makeHTMLStyle():
    htmlStyle = "<style>\n"
    htmlStyle += "table {font-family: Open Sans, sans-serif; border-collapse: collapse; width: 100%; margin-bottom: 20px;}\n"
    htmlStyle += "td, th {border: 1px solid #ddd; padding: 8px; text-align: left;}\n"
    htmlStyle += "th {background-color: #0463a7; color: white;}\n"
    htmlStyle += "tr:nth-child(even) {background-color: #f9f9f9;}\n"
    htmlStyle += "body{ font-family: 'Open Sans',sans-serif;}\n"
    htmlStyle += "</style>\n"
    return htmlStyle


def makeHTMLbody(tableData, InvOrPO, COs):
    htmlBody = "<body>\n"
    if "InvOrPO" == "Invoice":
        htmlBody += "Invoice Data Totals"
    else:
        # assuming it's PO
        htmlBody += "Purchase Order" 
    htmlBody += "<h2>PO Data Totals</h2>\n"
    htmlBody += tableData
    htmlBody += "\n</body>\n</html>"
    return htmlBody

def addToHTML(HTMLfile,tabledata, InvOrPO, COs):
    print("addToHTML", HTMLfile, InvOrPO, COs)
    with open(HTMLfile, "r") as f:
        contents = f.readlines()
    if InvOrPO == "Invoice":
        print("****************************************Invoice", InvOrPO)
        index = 14 # HARDCODED!!!
        contents.insert(index, tabledata)
    else:
        
        # assuming it's PO
        index = 13 # HARDCODED!!!
        #print("Why did we get HERE?")
        insertData = makeHTMLbody(tableData, InvOrPO)
        insertData += makeHTMLCOs(COs)
        contents.insert(index, insertData)
    

    with open(HTMLfile, "w") as f:
        contents = "".join(contents)
        f.write(contents)
        f.close()
        
def makeHTMLCOs(COs):
    htmlBody = '<h2>PO Numbers with Change Orders</h2>\n'
    htmlBody += '<table>\n'
    for index, (key, value) in enumerate(COs.items()):
        if index == 0:  # Check if it's the first iteration
            htmlBody += "<tr>\n<th>" + key + "</th>\n"
            htmlBody += "<th>" + value + "</th>\n</tr>\n"
        else:
            htmlBody += "<tr>\n<td>" + key + "</td>\n"
            htmlBody += "<td>" + value + "</td>\n</tr>\n"
    htmlBody += '</table><br><br>' # adding br's for space between tables (1 table per day/per run instead of 1 HTML
                                    # per day or run
    return htmlBody

def closeHTML():
    closehtml = "\n</body>\n</html>"
    return closehtml

def checkHTMLfile(theFile, tabledata, InvOrPO, COs):
    # needs pandas???
    currFile = Path(theFile)
    DataTotals = pd.DataFrame(tabledata, index=[0])
    # htmlTableData = PODataTotals.to_html()
    htmlTableData = DataTotals.to_html(index=False)
    if currFile.is_file():
        print("ok: html exists")
        addToHTML(theFile, htmlTableData, InvOrPO, COs)
    else:
        print("need to create html")
        f = open(theFile, "w")
        f.write(makeHTMLHead(InvOrPO))
        f.write(makeHTMLStyle())
        f.write(makeHTMLbody(htmlTableData, InvOrPO, COs))
        if InvOrPO == "PO":
            f.write(makeHTMLCOs(COs))
        f.close()
