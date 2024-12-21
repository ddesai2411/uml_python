#!/usr/bin/env python
# coding: utf-8

import xmltodict, glob
import os, shutil

# Removing the XML Files belonging to Purchase Orders of Non UML POS
# Removing the XML Files belonging to Invoices of Non UML POS
# Removing the XML Files belonging to Cancelled Invoices

def getFieldFromSourceFromInvoice(source,field):
    retval = ''
    if source != 'Field Not Found in XML' and field in source:
        retval = source[field]
        return retval
    else:
        retval = retval + 'Field Not Found in XML'
        return retval

def get_customFieldFromInvoice(theData,theField):
    retVal = "NOT FOUND"
    for f in theData:
        if f["@name"] == theField:
            try:
                retVal =  f["CustomFieldValue"]["Value"]
            except:
                retVal = "MULTIPLE"
    return retVal

def getCurrPONum(datasource):
    currOriginCode = get_customFieldFromInvoice(datasource["CustomFieldValueSet"],"Origin Code")
    currExtReq = get_customFieldFromInvoice(datasource["CustomFieldValueSet"],"External Req #")
    # Dropping LEB origin code: eb2bw won't work because of burden on FM procurement to down/upload files
    #if currOriginCode == "LEB":
        #currPONum = currExtReq[:2]
    #else:
        #currPONum =  getFieldFromSourceFromInvoice(datasource,'PONumber')
    # Do we need try/except?
    currPONum =  getFieldFromSourceFromInvoice(datasource,'PONumber')
    return currPONum

def filterUMLPO(theDir):
    POFiles = glob.glob(theDir + "*_PO_*.xml")
    PO_dict = {'UMLPOFiles': [], 'nonUMLPOFiles': []}
    # UMLPOFiles = []
    # nonUMLPOFiles = []
    for i in range(len(POFiles)):
        if POFiles[i].startswith(theDir + 'Jaggaer_PO_L'):
            PO_dict['UMLPOFiles'].append(POFiles[i])
            #print("******", POFiles[i])
            # UMLPOFiles.append(POFiles[i])
        else:
            PO_dict['nonUMLPOFiles'].append(POFiles[i])

    return PO_dict

def filterUMLInv(theDir):
    InvoiceFiles = glob.glob(theDir + "*_Invoice_*.xml")
    #print(InvoiceFiles)
    Inv_dict = {'CancelledInvFiles':[], 'UMLInvFiles': [], 'nonUMLInvFiles': []}
    for f in InvoiceFiles:
        #print(f)
        theFile = open(f,encoding='utf-8')
        xml_content = theFile.read()
        bwdata = xmltodict.parse(xml_content,encoding='utf-8')
        headerData = bwdata['BuyerInvoiceExportMessage']['Invoice']['InvoiceHeader']
        if 'InvoiceLine' not in bwdata['BuyerInvoiceExportMessage']['Invoice']:
            Inv_dict['CancelledInvFiles'].append(f)
            # print("Invoice Status Cancelled in ", f)
            # count +=1
            # if os.path.exists(f):
            #     os.remove(f)
            #     print(f, " File deleted successfully!")
            # else:
            #     print("The file does not exist.")
        else:
            Invlinedata = bwdata['BuyerInvoiceExportMessage']['Invoice']['InvoiceLine']
            if type(Invlinedata) == dict:
                currPONumber = getCurrPONum(Invlinedata) #getFieldFromSource(InvoiceLinedata,'PONumber')
                if currPONumber.startswith('L'):
                    Inv_dict['UMLInvFiles'].append(f)
                # filterUMLInvoice(currPONumber,f)
                else:
                    Inv_dict['nonUMLInvFiles'].append(f)
            else:
                for k in Invlinedata:
                    currPONumber = getCurrPONum(k) #getFieldFromSource(InvoiceLinedata,'PONumber')
                    if currPONumber.startswith('L'):
                        Inv_dict['UMLInvFiles'].append(f)
                    # filterUMLInvoice(currPONumber,f)
                    else:
                        Inv_dict['nonUMLInvFiles'].append(f)
    return Inv_dict

# theDir = "DataFiles/testdata/"
# theDir = "/Users/kysgattu/FIS/XMLFromBWToExcel/uml/fromBW/"
theDir = "B:\\fromBW\\"
# Change the directory path accordingly
print(theDir)

# POFiles = glob.glob(theDir + "*_PO_*.xml")
PO_dict = filterUMLPO(theDir)
Inv_dict = filterUMLInv(theDir)
#print(PO_dict['UMLPOFiles'])
#print(Inv_dict['UMLInvFiles'])
# PO_dict['nonUMLPOFiles']
# Inv_dict['CancelledInvFiles']
# Inv_dict['nonUMLInvFiles']

nonUML = PO_dict['nonUMLPOFiles'] + Inv_dict['nonUMLInvFiles'] + Inv_dict['CancelledInvFiles']
# nonUML
#print(nonUML)

for f in nonUML:
    # print(f)
    if os.path.exists(f):
        # Delete the file
        os.remove(f)
        print(f, " File deleted successfully!")
    else:
        print("The file does not exist.")
# we still need to move the possible EB files???!!!
for f in PO_dict['UMLPOFiles']:
    shutil.move(f, "B:\\fromBW\\2process\\")
for f in Inv_dict['UMLInvFiles']:
    try:
        shutil.move(f, "B:\\fromBW\\2process\\")
    except:
        print("Already exists: ", f)
# Now, move all the remaining (EB/potential eb) to 2process
print("Total XML files processed: ", str( len(PO_dict['nonUMLPOFiles']) + len(PO_dict['UMLPOFiles']) + len(Inv_dict['UMLInvFiles']) + len(Inv_dict['nonUMLInvFiles'])))
print("Possible UML PO files: ", str(len(PO_dict['UMLPOFiles'])))
print("NON UML PO files: ", str(len(PO_dict['nonUMLPOFiles'])))
print("UML Invoice files: ", str(len(Inv_dict['UMLInvFiles'])))
print("NON UML Invoice files: ", str(len(Inv_dict['nonUMLInvFiles'])))


# get_ipython().system('jupyter nbconvert --to script FilterXMLFiles.ipynb')
