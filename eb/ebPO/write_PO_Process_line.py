def write_PO_Process_line(POrow, multST, ws):

    """
    write_PO_Process_line(r, multipleST, processWS)
    May 22, 2020
    Removing "Status" field: no required, causing problems
    May 19, 2020
    Errors from real example May 18:
    FMP number (PS Project ID is showing)
    Commitment has "L-" prefix
    Status should be "Finish"
    Speedtype has "-L" at end
    New PO Process headers
    {1:"FMP Number",2:"Process Counter",3:"Commitment Number",4:"PeopleSoft PO#",5:"PeopleSoft PO Amount",\
                        6:"Step",7:"Speedtype",8:"Origin Code"}
    """
    # Key here, pun intended, is to cull the fields we want from the PO data dictionary and write them in the right order to Excel
    print ("PO Process Line")

    # 1: FMP Number - not in CSV, we looked up the speedtype to get it
    outCell = ws.cell(row=write_PO_Process_line.counter,column=1)
    outCell.value = POrow["Project"]

    # NEW BW Field: External Req #
    # 2: Process Counter - integer part of cart name
    # Need to confirm External Req # is in Buyways. Can we also add similar for Invoice?
    # 200925 Req # is in Buyways, confirmed. Updating to handle revised process POs, eg "POREQ - 00001 - 2"

    outCell = ws.cell(row=write_PO_Process_line.counter,column=2)
    try:
        toks = POrow["External Req #"].split(" -")
        #print ">>>>>>>>>>>>>>>>>>>>>", toks
        processCounter = str(int(toks[1]))
        #print ">>>", processCounter
    except:
        processCounter = ""
    outCell.value = processCounter # to match EB commitment name

    # 3: Commitment number - this may be for EB, in which case cart name, "POREQ - 23" etc
    #   remove "L-"
    outCell = ws.cell(row=write_PO_Process_line.counter,column=3)
    outCell.value = POrow['External Req #'][2:] # to match EB commitment name

    # 4: PeopleSoft PO # - PO number, confirmation we got approved
    outCell = ws.cell(row=write_PO_Process_line.counter,column=4)
    outCell.value = POrow['PO #']

    # 5: PeopleSoft PO Amount - $ value, confirmation, custom data field. Multi-line POs???
    outCell = ws.cell(row=write_PO_Process_line.counter,column=5)
    amt = f = float(POrow["Extended Price"].replace(',',''))
    outCell.value = str(amt)

    # 6: Step: Not in Buyways, always "Finish", to allow Process to complete
    outCell = ws.cell(row=write_PO_Process_line.counter,column=6)
    outCell.value = "Finish"

    # 7: Speedtype - confirmation, not imported
    outCell = ws.cell(row=write_PO_Process_line.counter,column=7)
    outCell.value = POrow['Speedtype']

    # 8: Origin Code - confirmation, not imported
    outCell = ws.cell(row=write_PO_Process_line.counter,column=8)
    outCell.value = POrow['Origin Code']

    # 9: Comments
    outCell = ws.cell(row=write_PO_Process_line.counter,column=9)
    outCell.value = multST

    write_PO_Process_line.counter += 1

