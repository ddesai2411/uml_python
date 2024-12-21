#!/usr/bin/env python3
import mmap, glob, os

# August 24, 2023
# Next version should move potential EB POs and potential EB Invoices to a different folder

"""
with open("B:\\fromBW\\Jaggaer_Invoice_X2179730.xml") as f:
    s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    if s.find(b'<Value>UMBOS</Value>') != -1:
        print("True")
    else:
        print("Nope")
"""
nonUML_POs = 0
nonUML_Invoices = 0
potential_EB_POs = 0
potential_EB_Invoices = 0

toDelete = []
toMove = []

basePath = "B:\\fromBW\\"
basePathlen = len(basePath)

def checkInvoice(theFile):
    global toDelete, toMove, potential_EB_Invoices
    with open(theFile) as f:
        s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        if s.find(b'<Value>UMLOW</Value>') == -1:
            toDelete.append(theFile)
        else:
            potential_EB_Invoices += 1
            toMove.append(theFile)
            
            

thePOs = glob.glob(basePath + "Jaggaer_PO*.xml")
for p in thePOs:
    if p.find("_PO_L") == -1:
        os.remove(p)
        nonUML_POs += 1
    else:
        potential_EB_POs += 1
        os.rename(p,(basePath + "2process\\" + p[basePathlen:]))
        
print ("Non UML POs:", nonUML_POs)
print ("Potential EB POs:", potential_EB_POs)

theInvoices = glob.glob("B:\\fromBW\\Jaggaer_Invoice_X*.xml")
for i in theInvoices:
    checkInvoice(i)

for d in toDelete:
    os.remove(d)

for m in toMove:
    try:
        os.rename(m,(basePath + "2process\\" + m[basePathlen:]))
    except:
        print("Unable to move - alreay exists?", m)


nonUML_Invoices = len(toDelete)
print("Non UML Invoices:", nonUML_Invoices)
print ("Potential EB Invoices:", potential_EB_Invoices)
