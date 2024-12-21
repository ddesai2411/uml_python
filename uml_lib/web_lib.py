import time, shutil
from datetime import datetime
from pathlib import Path



# IMPORTANT:
# Make sure that you have necessary Styling (table3.css) and Scripting(table3.js) files
# in the directory where outputs will be saved

def namify(s):
    retVal = ""
    badChars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*", " ", ","]
    # we are also replacing any spaces and commas
    for c in range(0, len(s)):
        if s[c] in badChars:
            retVal += "_"
        else:
            retVal += s[c]
    return retVal


def padstr(s):
    retVal = s
    if len(s) == 1:
        retVal = "0" + retVal
    return retVal

def tstamper():
    now = datetime.now()
    tstamp = now.strftime("%Y-%b-%d %H:%M:%S")
    return tstamp

def tstamper2():
    now = datetime.now()
    mo = padstr(str(now.month))
    d = padstr(str(now.day))
    h = padstr(str(now.hour))
    mi = padstr(str(now.minute))
    s = padstr(str(now.second))
    tstamp = str(now.year)[2:] + mo + d + "_" + h + mi + s
    return tstamp


def makeHTMLtop(title, tstamp, headerStr):
    retVal = "<!DOCTYPE html>\n<html>\n<head>\n"
    retVal += "<title>" + title + "</title>\n"
    retVal += """
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" type="text/css" href="table3.css" />"""
    retVal += """
    <link
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css"
      rel="stylesheet"
      integrity="sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65"
      crossorigin="anonymous"
    />
"""
    retVal += "<h2>" + headerStr + "</h2>\n"
    # retVal += "<p class='i'><span style='color:#00549F'>Last updated: " + tstamp + "</span></p><p></p>"
    retVal += "</head>\n"

    return retVal

# These are functions related to EBProj
def makeHTMLHead(POorInvoice):
    htmlHead = "<!DOCTYPE html>\n<html>\n<head>\n<title>" + POorInvoice + "</title>\n</head>\n"
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

def startHTMLbody(POorInvoice):
    htmlBody = "<body>\n"
    htmlBody += "<h2>" + POorInvoice + " Data Totals</h2>\n"
    return htmlBody

def makeHTMLtableHeader(POorInvoice):
    if POorInvoice == "Invoice":
        retVal = """
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>Timestamp</th>
      <th>Source</th>
      <th>EBcost</th>
      <th>EBprocess</th>
      <th>EBCost Type 2.0(PAYAPs)</th>
      <th>InProcess</th>
      <th>Payable</th>
      <th>Already In EB</th>
      <th>Other</th>
      <th>Non EB</th>
    </tr>
  </thead>
"""
    else:
        retVal = """
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>Timestamp</th>
      <th>Source</th>
      <th>EBprocess</th>
      <th>EBcost</th>
      <th>EBexists</th>
      <th>EBexistsCO?</th>
      <th>nonEB</th>
      <th>Not UML POs</th>  
    </tr>
  </thead>
"""
    return retVal

def makeRow(rowData):
    retVal = "<tr>"
    # print("???", rowData)
    for c in rowData:
        retVal += "\n<td>" + c + "</td>"
    retVal += "\n</tr>"
    return retVal

def closeTable():
    retVal = "</table>"
    return retVal

def closeBody():
    retVal = "</body>"
    return retVal

def closeHTML():
    retVal = "</html>"
    return retVal

def makeCOtable():
    retVal =  """
    <h2>Possible Change Orders</h2>\n
    <table border="1" class="dataframe">
      <thead>
    <tr style="text-align: right;">
      <th>Timestamp</th>
      <th>PO Number</th>
      <th>FMP</th>
      </tr>
  </thead>
"""
    return retVal

def findCOtableStart(contents):
    # search for table header, return index + 1?
    i = 0
    for c in contents:
        if "Possible Change Orders" in c:
            break
        i += 1
    return (i+8)

def makeCOtabledata(currTime, COs):
    retVal = ""
    print(COs)
    if list(COs.keys())[0] == 'PO Number':
        # Remove the first entry
        del COs['PO Number']
    for c in COs:
        currRow = makeRow([currTime, c,COs[c]])
        retVal += currRow
        retVal += "\n"
    return retVal

def addToHTML(theHTML, currTime, POorInvoice, tableRow, COs):
    COindex = 0
    
    with open(theHTML, "r") as f:
        contents = f.readlines()
    if POorInvoice == "Invoice":
        index = 29 # HARDCODED!!!
    else:
        index = 29
        COindex = findCOtableStart(contents)
        CO_HTML = makeCOtabledata(currTime, COs)
        
        # need another index for CO table
        
    if COindex > 0:
        # print(">>>>> got here\n")
        contents.insert(COindex,CO_HTML)
    rowHTML = makeRow(tableRow)
    contents.insert(index, rowHTML)
   
    with open(theHTML, "w") as f:
        contents = "".join(contents)
        f.write(contents)
        f.close()
        
def outputHTML(POorInvoice, currTime, theData, COs):
    if POorInvoice == "Invoice":
        #thePath = "B:\\dailyImports\\TEST\\_TEST_InvoiceDataTotals.html"
        thePath = "B:\\dailyImports\\_InvoiceDataTotals.html"
        #thePath = "/Users/kysgattu/FIS/BDrive/dailyImports/_InvoiceDataTotals.html"
        
    else:
        #thePath = "B:\\dailyImports\\TEST\\_TEST_PODataTotals.html"
        thePath = "B:\\dailyImports\\_PODataTotals.html"
        #thePath = "/Users/kysgattu/FIS/BDrive/dailyImports/_PODataTotals.html"

    theHTML = Path(thePath)
    tableData = []    
    for k in theData:
        tableData.append(str(theData[k]))
    # print("?>?>?>?>",tableData)

    if theHTML.is_file():
        #print("ok: html exists")
        addToHTML(theHTML, currTime, POorInvoice, tableData, COs)
    else:
        print("need to create html")
        f = open(theHTML, "w")
        f.write(makeHTMLHead(POorInvoice))
        f.write(makeHTMLStyle())
        f.write(startHTMLbody(POorInvoice))
        f.write(makeHTMLtableHeader(POorInvoice))
        f.write(makeRow(tableData))
        f.write(closeTable())
        f.write(closeBody())
        f.write(closeHTML())
        
        if POorInvoice == "PO":
            f.write(makeCOtable()) # this is header, not content
            f.write(makeCOtabledata(currTime, COs))
        f.close()

