# Is this in 2 places? RESOLVE
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

def write_Invoice_Process_line(InvRow, ws):
    # now invoices are dictionary
    global ebPOs
    #print "!!!!!!!!!!!Invoice Process!!!!!!!!!!!!!!!!!!!!"
   
    """
    {1:"FMP Number",2:"Process Counter",3:"Step",4:"Status",5:"Commitment Number",6:"Vendor Invoice #",7:"Voucher ID"}
    """
    
    # 1: FMP Number - not in CSV, we looked up the speedtype to get it and changed CSV field Project
    outCell = ws.cell(row=write_Invoice_Process_line.counter,column=1)
    outCell.value = InvRow["Project"]

    # 2: Process Counter
    outCell = ws.cell(row=write_Invoice_Process_line.counter,column=2)
    outCell.value = "NEED FROM EB REPORT - TO BE DEVELOPED"
    
    # 3: Step: always "Finish"
    # 210124 Changing back to Finish step - PAYAPs will move to Finish,
    #       keep at Approved, wait for "Paid" from BW, which will be done
    #       by Invoice Update
    # 200925 Updating to also handle Buyways "Payable" status. EB process now has an FIS Hold Step for
    # Payable invoices, so PMs can see the Invoice has moved in BW
    # FIS HOLD - Payable
    # FIS HOLD - Paid  = "Finish" step?
    #print "????????????????????", InvRow["Invoice Status"]
    outCell = ws.cell(row=write_Invoice_Process_line.counter,column=3)
    #if InvRow["Invoice Status"] == "Payable":
        #outCell.value = "FIS HOLD - Payable"
    #else:
    outCell.value = "Finish"

    # 4: Status: Always Approved? Is this EB or BW status? What are the options. BW field is Invoice Status 
    
    outCell = ws.cell(row=write_Invoice_Process_line.counter,column=4)
    if InvRow["Invoice Status"] == "Payable":
        outCell.value = "Approved"
    else:
        outCell.value = "Paid" # Other statuses??
    #outCell.value = "Paid" # NEED TO CONFIRM, pull from Buyways? Do we want in process? What are BW statuses?

    # 5: Commitment Number - from EB Support Report
    # NO! BW has this in External Req # field!!!
    outCell = ws.cell(row=write_Invoice_Process_line.counter,column=5)
    outCell.value = InvRow["External Req #"]

    # 6:  always "Vendor Invoice #"
    
    outCell = ws.cell(row=write_Invoice_Process_line.counter,column=6)
    outCell.value = InvRow["Supplier Invoice No"]

    # 7: Voucher ID
    outCell = ws.cell(row=write_Invoice_Process_line.counter,column=7)
    outCell.value = InvRow["Invoice No"]
    #print "write process line complete"
    
    write_Invoice_Process_line.counter += 1
    
def write_Invoice_Process_lines(Inv, ws):
    if len(Inv)== 1:
        write_Invoice_Process_line(Inv[0], ws)
    else:
        for i in BWinv:
            write_Invoice_Process_line(i, ws)
