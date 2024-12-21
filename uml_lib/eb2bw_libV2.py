# -*- coding: cp1252 -*-
import os
from os.path import exists
import requests
from datetime import datetime
import lxml.etree
import xmltodict
from uml.uml_lib import ebAPI_lib as eb

Xdir = "X:\\_ebuilder\\POREQ\\_eb2bw\\"

def padstr(s):
    retVal = s
    if len(s) == 1:
        retVal = "0" + retVal
    return retVal

def tstamper():
    now = datetime.now()
    yr = padstr(str(now.year))
    mo = padstr(str(now.month))
    d = padstr(str(now.day))
    h = padstr(str(now.hour))
    mi = padstr(str(now.minute))
    s = padstr(str(now.second))
    tstamp = yr + '-' + mo + '-' + d + "_" + h + ':' + mi + ':' + s
    return (tstamp)


def tstamper2():
    now = datetime.now()
    mo = padstr(str(now.month))
    d = padstr(str(now.day))
    h = padstr(str(now.hour))
    mi = padstr(str(now.minute))
    s = padstr(str(now.second))
    tstamp = str(now.year)[2:] + mo + d + "_" + h + mi + s
    return (tstamp)


def xmlStart(s):
    retVal = "<"
    retVal += s
    return retVal

def xmlClose(s):
    retVal = "<"
    retVal += s
    return retVal

def fundingInfo(fieldName, splitIndex, amt, fieldValue):
    retVal = "<CustomFieldValueSet name=\"" + fieldName + "\" distributiontype=\"AmountOfPrice\">\n"
    retVal += "<CustomFieldValue distributionvalue=\"" + str(amt) + "\" splitindex=\"" + str(splitIndex) + "\">\n"
    retVal += "<Value>" + fieldValue + "</Value>\n"
    retVal += "</CustomFieldValue>\n</CustomFieldValueSet>\n"
    return retVal

# Need to add optional argument to fundingInfo to handle this
def speedTypeInfo(fieldName, splitIndex, amt, fieldValue, desc):
    retVal = "<CustomFieldValueSet name=\"" + fieldName + "\" distributiontype=\"AmountOfPrice\">\n"
    retVal += "<CustomFieldValue distributionvalue=\"" + str(amt) + "\" splitindex=\"" + str(splitIndex) + "\">\n"
    retVal += "<Value>" + fieldValue + "</Value>\n"
    retVal += "<Description>" + desc + "</Description>\n"
    retVal += "</CustomFieldValue>\n</CustomFieldValueSet>\n"
    return retVal

def xmlHeader(sendToPROD):
    xml = """<!DOCTYPE PurchaseRequisitionMessage SYSTEM "http://usertest-messages.sciquest.com/app_docs/dtd/requisition/PRImport.dtd"[]>
    <PurchaseRequisitionMessage version="1.0">
      <Header>
        <MessageId>{{$randomUUID}}</MessageId>
        <Timestamp>{{$isoTimestamp}}</Timestamp>
        <Authentication>
          <Identity>UMASS30000814</Identity>"""
    if sendToPROD:
        xml += "<SharedSecret>!Q@W1q2wPRImport</SharedSecret>"
    else:
        xml += "<SharedSecret>$$PRIMPORT$$</SharedSecret>"
    xml += """
            </Authentication>
          </Header>
          <PurchaseRequisition>
            <RequisitionHeader>"""
    return xml

def findPOREQs_TEST1(POREQjson, theStep): #Unused
    retVal = []
    i = len(POREQjson)
    for j in range(0, i):
        if POREQjson[j]["InstanceID"] == testPOReq:
            retVal.append(j)
    return retVal

def findPOREQsTest(POREQjson, theStep, theID):
    #testPOReq = "fdf1cbdf-7cb0-423f-8cb3-59e5c97ba05c"  -- marg, costello, 1 line
    testPOReq = "fa7f55f5-e9a3-4ae4-ae1f-bbfee04b529d" # Coburn parking 3 lines
    retVal = []
    i = len(POREQjson)
    for j in range(0,i):
        if POREQjson[j]['ProcessInstance']['CurrentStepName'] == theStep:
            retVal.append(j)
    return retVal

def findPOREQs(POREQjson, theStep):
    #testPOReq = "fdf1cbdf-7cb0-423f-8cb3-59e5c97ba05c"  -- marg, costello, 1 line
    testPOReq = "fa7f55f5-e9a3-4ae4-ae1f-bbfee04b529d" # Coburn parking 3 lines
    retVal = []
    i = len(POREQjson)
    for j in range(0,i):
        if POREQjson[j]['ProcessInstance']['CurrentStepName'] == theStep:
            retVal.append(POREQjson[j])
    return retVal


def findCommitment(COMMITjson, commitID):
    print("TBD")

def getItemData(commitmentItemData, mCostID):
    retVal = {} # Need list or dict? should try with multi line
    i = len(commitmentItemData)
    # CAREFUL: Can be more than one
    for j in range(0,i):
        if commitmentItemData[j]["commitmentID"] == mCostID:
            currLine = stripLeadingZeros(commitmentItemData[j]["itemNumber"])
            retVal[currLine] = commitmentItemData[j]
            print("\n\n?:?:?", retVal)
    return retVal

def getCommitmentData(commitmentsData, mCostID):
    retVal = "" # Need list or dict? should try with multi line
    i = len(commitmentsData)
    for j in range(0,i):
        if commitmentsData[j]["commitmentID"] == mCostID:
            retVal = commitmentsData[j]
    return retVal

def getSupplierNumber(companiesData, companyID):
    retVal = ""
    i = len(companiesData)
    for j in range(0,i):
        if companiesData[j]["companyId"] == companyID:
            retVal = companiesData[j]["companyNumber"]
    return retVal

def getSTdata(FSjson, currST):
    """
    currSTdata = getFundingSourceData(FSjson, "111841")
    STdata = {"PC Business Unit":"none","Fund":currSTdata["Fund"],
              "Department":currSTdata["Dept. ID"],"Account":"735100-L","Speedtype":"111841-L",
                   "Program":"G00-L","Project":"none","Activity Id":"none","Campus PO Number Prefix":"L0"}
  
    print("Business Unit (substitute -none-:\t",currSTdata["Business Unit"])
    print("Fund, strip desc. add -L:\t\t",currSTdata["Fund"])
    print("Department, strip description:\t\t",currSTdata["Dept. ID"])
    print("Program:\t\t\t\t", currSTdata["Program"])
    print("Project:\t\t\t\t", currSTdata["Project ID"])
    print("Activity ID - not in ST custom fields??? - always none?")
    print("Campus PO Number Prefix - not in ST custom fields??? - always L0?")
    """
    retVal = {"PC Business Unit":"none","Fund":"","Department":"","Account":"","Speedtype":(currST + "-L"),"Program":"","Project":"",
              "Activity Id":"none","Campus PO Number Prefix":"L0"}
    print("*****************>>>>?????",retVal)
    errors = 0
    STdata = getFundingSourceData(FSjson, currST)
    #for d in STdata:
        #print(">>>>?????", d, STdata[d])
    #1. Business Unit: hard coded
    #2. Fund
    try:
        #print("*****************>>>>?????", STdata["Fund"])
        theFund = STdata["Fund"][:5]
        #print("*****************>>>>?????", theFund)
        theFund += "-L"
        #print("*****************>>>>?????", theFund)
        retVal["Fund"] = theFund
    except:
        retVal["Fund"] = "ERROR: FUND"
        errors += 1
    #3. Department
    try:
        theDept = STdata["Dept. ID"][:10] + "-L"
        print("***", theDept)
        retVal["Department"] = theDept
    except:
        retVal["Department"] = "ERROR: DEPT. ID"
        errors += 1

    #4. Account
    # need to pull from PO line? "Line Item" : varies by line
    retVal["Account"] = "735100-L"
    
    #5. Speedtype
    
    #6. Program
    try:
        theProgram = STdata["Program"] + "-L"
        retVal["Program"] = theProgram
    except:
        retVal["Program"] = "ERROR: PROGRAM"
        errors += 1
    #7. Project
    try:
        if currST == "111842" or currST == "111841":
            retVal["Project"] = "none"
        else:
            retVal["Project"] = STdata["Project ID"]
    except:
        retVal["Project"] = "ERROR: PROJECT ID"
        errors += 1
    #8. Activity: hard coded
    #9. Campus PO Number Prefix: hard coded
        
    if errors > 0:
        print("Speedtype data errors", retVal)
    return retVal

# There can be more than fs related to a speedtype??
# Use ID
def getFundingSourceData(FSjson, Speedtype):
    retVal = "No Speedtype Found"
    #print Speedtype
    #print "????", Speedtype
    i = len(FSjson)
    for j in range(0,i):
        #print ">>>",FSjson["d"][j]["Name"], "<<<",Speedtype, (Speedtype in FSjson["d"][j]["Name"])
        if Speedtype.encode("utf-8") in FSjson[j]["name"].encode("utf-8"):
            retVal = FSjson[j]
            #print "Found", retVal
    #print "returning ", retVal
    return retVal

def getFundingSourceData_ID(FSjson, FSid):
    retVal = "No ID found"
    #print Speedtype
    #print "????", Speedtype
    i = len(FSjson)
    for j in range(0,i):
        #print ">>>",FSjson["d"][j]["Name"], "<<<",Speedtype, (Speedtype in FSjson["d"][j]["Name"])
        if FSid.encode("utf-8") in FSjson[j]["fundingSourceID"].encode("utf-8"):
            retVal = FSjson[j]
            #print "Found", retVal
    #print("returning ", retVal)
    return retVal


def getFMP(PROJjson, projID):
    retVal = ""
    i = len(PROJjson)
    for j in range(0,i):
        if PROJjson[j]["projectId"] == projID:
            retVal = PROJjson[j]["FMP Number"]
    return retVal

def padProc(s):
    retVal = s
    for c in range(0, (5 - len(s))):
        retVal = "0" + retVal
    return retVal

def stripLeadingZeros(lineNum):
    while lineNum[0] == "0":
        lineNum = lineNum[1:]
    return lineNum

def xmlShippingAddress(currData):
    # currData is for POREQ process
    # (if BW requires) TemplateName, AddressCode, or both
    """
    2022-01-19
    - Works with a phony AddressCode
    - Works with phony values for AddressLine, City, State, Postal Code
    - all get replaced by values on BW side for given TemplateName
     <TemplateName>150 Wilder Street</TemplateName>
    <AddressCode>150 Wilder Street</AddressCode>
     <d:DataField_Address_Line>600 Suffolk Street</d:DataField_Address_Line>
        <d:DataField_City>Lowell</d:DataField_City>
        <d:DataField_State>MA</d:DataField_State>
        <d:DataField_Zip_Code>01854</d:DataField_Zip_Code>
          # ANSWERED: POREQ Process, <d:DataField_Shipping_Address>OTHER-UMLOW: OTHER-UMLOW</d:DataField_Shipping_Address>
            # We also need ATTN and Room/Floor/Suite - check if they are null
            # d:DataField_Attention m:null="true" />
            #<d:DataField_RoomFloorSuite m:null="true" />
            # For TEST, we should check if code exists.
            # Need to handle OTHER
            <AddressLine linenumber="1"> </AddressLine>
                <City>NOT-NEEDED</City>
                <State>NOT-NEEDED </State>
                <PostalCode>NOT-NEEDED </PostalCode>
                <Country isocountrycode="US">United States</Country>
                <d:DataField_Shipping_Address>150 Wilder Street: 150 Wilder Street: Lowell, MA 01854</d:DataField_Shipping_Address>
<d:DataField_Attention>Renee</d:DataField_Attention>
        <d:DataField_RoomFloorSuite>450</d:DataField_RoomFloorSuite>
    """
    currAddressCode = currData['ProcessInstance']['DataFields']["Shipping Address"]
    currAttention = currData['ProcessInstance']['DataFields']["Attention"]
    currRoomFloorSuite = "" #currData["DataField_RoomFloorSuite"]
    # These are only needed for "OTHER"
    try:
        currAddressLine = ""
        currAddressLine += currData['ProcessInstance']['DataFields']["Address Line"]
    except:
        currAddressLine = " "
    try:
        currCity = ""
        currCity += currData['ProcessInstance']['DataFields']["City"]
    except:
        currCity = " "
    try:
        currState = ""
        currState += currData['ProcessInstance']['DataFields']["State"]
    except:
        currState = " "
    try:
        currZip = ""
        currZip += currData['ProcessInstance']['DataFields']["Zip Code"]
    except:
        currZip = " "
    # This is DataField_Attention
    if currAttention == None:
        currAttention = "-"
    # This is DatField_RoomFloorSuite
    if currRoomFloorSuite == None:
        currRoomFloorSuite = "-"
    toks = currAddressCode.split(":")
    # THIS IS WRONG. NEED TO UDPATE.
    # I believe XML should have Buyways Nickname for Template name
    # and Buyways Address Code for Address Code. Need an example
    # where they differ (Wannalancit? but it has its street adddress?)
    currTemplate = toks[0]
    #Should we check if Address Line is empty/exists?
    if currTemplate == "OTHER-UMLOW":
        currCode = currTemplate
    else:
        toks2 = (toks[2].lstrip()).split(",")
        currCode = toks2[0]

    #print ">>>>",currTemplate,"<<<<>>>>", currCode,"<<<<"
    #currTemplate = "150 Wilder Street"
    retVal = """<ShipTo>
    <Address>
    <TemplateName>"""
    retVal += currTemplate + "</TemplateName>\n"
    retVal += "\t<AddressCode>" + currCode + "</AddressCode>\n"
    #retVal += "<AddressCode>150 Wilder Street</AddressCode>"
    #retVal += """<Contact label="Attn:" linenumber="1">LEB-TESTER</Contact>"""
    retVal += """\t<Contact label="Attn:" linenumber="1">"""
    if currAttention == "":
        retVal += "-" # doesn't like this to be empty?
    else:
        retVal += currAttention
    # We are ignoring contact??
    retVal += """</Contact>
    <Contact label="Department:" linenumber="2">"""
    retVal += currRoomFloorSuite
    retVal += "-</Contact>\n"
    if currTemplate == "OTHER-UMLOW":
        # !!! Need multiline example, loop solution here
        retVal += """<AddressLine linenumber="1">""" + currAddressLine + "</AddressLine>\n"
        retVal += "<City>" + currCity + "</City>\n"
        retVal += "<State>" + currState + "</State>\n"
        retVal += "<PostalCode>" + currZip + "</PostalCode>\n"
    else:
        retVal += """\t<AddressLine linenumber="1">NOT-NEEDED</AddressLine>\n"""
        retVal += "\t<City>NOT-NEEDED</City>\n"
        retVal += "\t<State>NOT-NEEDED</State>\n"
        retVal += "\t<PostalCode>NOT-NEEDED</PostalCode>\n"
    retVal +="""\t<Country isocountrycode="US">United States</Country>
    </Address>
    </ShipTo>
    """
    return retVal

def xmlCustomValSet(theName, theAmount, theValue):
    #NOTE: will needs list of names and amounts with split amounts for split funding
    retVal = "<CustomFieldValueSet name=\"" + theName + "\" distributiontype=\"AmountOfPrice\">\n"
    retVal += "\t<CustomFieldValue distributionvalue=\"" + str(theAmount) + "\" splitindex=\"0\">\n"
    retVal += "\t\t<Value>" + theValue + "</Value>\n"
    retVal += "\t</CustomFieldValue>\n"
    retVal += "</CustomFieldValueSet>\n"
    return retVal

def xmlLineItem(currLineNum, itemData, FSjson, headerDesc):
    # item data is a single line from the Cost Commitment Items API object
    # itemData = eb2bw.getItemData(CITEMSjson,HCMAPPEDCOSTID)
    # FSjson is EB API funding source data
    #for d in itemData:
        #print("????", d)
    print("???? fr name", itemData["fundingRuleName"])
    lineItemSuccess = True
    xml = "<RequisitionLine linenumber=\"" + str(currLineNum) + "\">\n"
    #print "7: Line Number", currLineNum

    xml += """<Item>
        <CatalogNumber>No Catalog</CatalogNumber>"""
    xml += """<Description>"""
    #xml += itemData["Description"]
    xml += headerDesc
    # This works for Quantity/UOM
    #<MeasurementAmount>20</MeasurementAmount> but it shows weirdly in BW
    # But not working with Quantity > 1 (July 2022)
    xml += """</Description>
          <ProductUnitOfMeasure type="buyer">
            <Measurement>
                <MeasurementAmount>1</MeasurementAmount>
              <MeasurementUnit>EA</MeasurementUnit>
              <MeasurementValue>EA</MeasurementValue>
            </Measurement>
          </ProductUnitOfMeasure>"""
    #xml += "<CommodityCode>" + itemData["Custom_Commodity_Code1"] + "</CommodityCode>\n"
    xml += "<CommodityCode>Const/Reno/Prev Wage Work, includes CFS</CommodityCode>\n"
    xml += """
          <ProductType>NonCatalogItem</ProductType>
        </Item>"""
    currQuantity = itemData["quantity"]
    print(itemData["quantity"],itemData["unitCost"],itemData["amount"])
    # 230714 NEED TO REWORK THIS LOGIC
    # changing to None
    if currQuantity == None: #it's lump sum
        currQuantity = 1 #CAREFUL: WHY DO WE HAVE QUANTITY ZERO!????
        currAmount = itemData["amount"]
        currUnitPrice = currAmount
    else:
        print(itemData["unitCost"])
        print(currUnitPrice)
        currUnitPrice = itemData["unitCost"]
        currAmount = float(currQuantity)*float(currUnitPrice)
        #print "??:UOM. Unit price:", currUnitPrice

    xml += "<Quantity>" + str(currQuantity) + "</Quantity>"
    # GOOD TO KNOW: IT CHECKS VALUES IN SPLIT LINES AGAINST AMOUNT FOR LINE



    #print "14 (alt). Amount (line total, extended price):", currAmount
    xml += """<LineCharges>
          <UnitPrice>
            <Money currency="USD">"""
    #xml += str(currAmount)
    xml += str(currUnitPrice)
    xml += """</Money>
          </UnitPrice>
        </LineCharges>"""
    #16 Campus: always "UMLOW"
    #currCampus = "UMLOW"
    #xmlCustomValSet("Campus", currAmount, currCampus)
    #print "15. Campus", currCampus



    # Now, funding/speedtype info, including provisions for split funding (ugh)
    currFundingRuleName = itemData["fundingRuleName"]
    print("***",currFundingRuleName,"***", type(currFundingRuleName))
    if currFundingRuleName  == "111841":
        currSpeedtype = "111841"
    elif currFundingRuleName.encode("utf-8") == "111842":
        currSpeedtype = "111842"
    else:
        currSpeedtype =  currFundingRuleName[-6:]
        print("!!!!", currSpeedtype)
    # Need to get this from funding rule
    #currSpeedtype = "111841"
    print ("::::", currSpeedtype)
    #print "??????>>>>>", currSpeedtype
    # NEED ERROR CHECKING: WHAT IF FUNDING RULE NAME IS BAD, DOES NOT HAVE SPEEDTYPE?
    #print "***",currSpeedtype,"***", len(currSpeedtype)
    # Reworked so this is called from def getSTdata(FSjson, currST)
    # 230711
    currSTdata = getFundingSourceData_ID(FSjson, currSpeedtype)
    #print "currSTdata??????>>>>>", currSTdata
    if currSTdata == "No Speedtype Found":
        lineItemSuccess = False
        print ("ST Failed to send")
        xml = "eb2bw failed::: No Speedtype found"
    else:
        ignoreThis = 1

    CRPhardwire = {"PC Business Unit":"none","Fund":"51003-L","Department":"L630400000-L","Account":"741980-L","Speedtype":"112976-L",
                   "Program":"A00-L","Project":"none","Activity Id":"none","Campus PO Number Prefix":"L0"}

    # Project and Actiity ID need to change? need to test "real" ST with PS project id. Skipping "CLASS"!?
    TESThardwire = {"PC Business Unit":"none","Fund":"51161-L","Department":"L300603000-L","Account":"735100-L","Speedtype":"111841-L",
                   "Program":"G00-L","Project":"none","Activity Id":"none","Campus PO Number Prefix":"L0"}

    RIZKhardwire = {"PC Business Unit":"none","Fund":"51105-L","Department":"L120100000-L","Account":"761600-L","Speedtype":"120936-L",
                   "Program":"E00-L","Project":"none","Activity Id":"none","Campus PO Number Prefix":"L0"}

    FMPhardwire = {"PC Business Unit":"none","Fund":"51425-L","Department":"L300600000-L","Account":"735100-L","Speedtype":"120604-L",
                   "Program":"G00-L","Project":"M50230FMP393372","Activity Id":"none","Campus PO Number Prefix":"L0"}
    # 230714
    #STvalues = getSTdata(FSjson, currSpeedtype)
    STvalues = FMPhardwire
    #STvalues = TESThardwire
    
    # Problem with test ST, 111841. Hardcoding - remove for other tests!!!!
    #STvalues["Department"] = "L300603000-L"

    # 230710
    # MUCH cleaner: replaces dozens of lines of repetitive code. Need to make sure ok to omit Class (none). Need to address Project and Activity
    # Need to get values from POREQ process rather than hardwired dictionary. Change EB values for 111841 to these working/correct values, change
    # code to pull values from POREQ, and rerun
    for v in STvalues:
        xml += xmlCustomValSet(v,currAmount,STvalues[v])


    # Close this line (should work in loop for multiple line POs
    if lineItemSuccess:
        xml += "</RequisitionLine>\n"
    return xml

def parseResponse(theResponse):
    root = lxml.etree.fromstring(theResponse)
    currStatCode = ((root.find('ResponseMessage/Status/StatusCode')).text).strip()
    # print currStatCode
    currStatText = ((root.find('ResponseMessage/Status/StatusText')).text).strip()

    try:
        toks = theResponse.split("requisitionId=\"")
        toks2 = toks[1].split("\"")
        currReqID = toks2[0]

        toks = theResponse.split("requisitionName=\"")
        toks2 = toks[1].split("\"")
        currReqName = toks2[0]
    except:
        currReqID = 0

    # print "Status Code: ", currStatCode, " BW req ID: ", currReqID, " with Req Name\n", currReqName

    return currReqID

def makeBasename(currFMP, processPrefix, processCounter):
    return (currFMP + "_" + processPrefix + "-" + processCounter)

# This Can be removed - Logic and Functionality Rewritten
def createDupErrorFile(basename):
    currFile = Xdir + "failed\\" + tstamper2() + "_" + basename + "_ALREADY_SENT.txt"
    logFile = open(currFile, "w")
    logFile.write(basename)
    logFile.close()

# This Can be removed - Logic and Functionality Rewritten
def checkIfAlreadySent(basename):
    global Xdir
    retVal = False

    files = os.listdir(Xdir + "success\\")
    for f in files:
        if basename in f:
            retVal = True
            break
    return retVal

# This Can be removed - Logic and Functionality Rewritten
def createLogFile(basename, resp):
    global Xdir
    resp = resp.encode("utf-8")
    currReqNum = parseResponse(resp)
    if currReqNum > 0:
        currFilename = (Xdir + "success\\" + basename + "_" + currReqNum + ".txt")
        # print currFilename
    else:
        currFilename = (Xdir + "failed\\" + basename + ".txt")
    return currFilename
    # Need to create file, write response to file, save and close

"""
Superceded: old functions, hardwired dev versions
"""
def xmlShippingAddress_HARDWIRED(templateName):
    # Hardwired for now. DANGER. Need to figure out if we need to use
    # (if BW requires) TemplateName, AddressCode, or both
    """
    2022-01-19
    - Works with a phony AddressCode
    - Works with phony values for AddressLine, City, State, Postal Code
    - all get replaced by values on BW side for given TemplateName
    """
    retVal = """
    <ShipTo>
    <Address>
    <TemplateName>150 Wilder Street</TemplateName>
    <AddressCode>150 Wilder Street</AddressCode>
    <Contact label="Attn:" linenumber="1">LEB-TESTER</Contact>
    <Contact label="Department:" linenumber="2">PDC-TESTER</Contact>
    <AddressLine linenumber="1">NOT-NEEDED</AddressLine>
    <City>NOT-NEEDED</City>
    <State>NOT-NEEDED</State>
    <PostalCode>NOT-NEEDED</PostalCode>
    <Country isocountrycode="US">United States</Country>
    </Address>
    </ShipTo>
    """
    return retVal

def testResponseSuccess():
    retVal = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE PurchaseRequisitionMessage SYSTEM "https://usertest-messages.sciquest.com/app_docs/dtd/requisition/PRImport.dtd">
<PurchaseRequisitionMessage version="1.0">
	<Header>
		<MessageId>
			01dbeefe-b5f8-466c-9cc0-017f1e1c22f5
		</MessageId>
		<Timestamp>
			2022-02-21T16:07:14.805-05:00
		</Timestamp>
	</Header>
	<ResponseMessage>
		<Status>
			<StatusCode>
				200
			</StatusCode>
			<StatusText>
				Success (Counts:  Total documents attempted=1, Total documents completed=1.  Documents successful without warnings=1)
			</StatusText>
		</Status>

		<ObjectErrors>
			<RequisitionRef requisitionId="3466726" requisitionName="UMLOW-IT-COPR-DEV-0000054 (, ) - Dell Latitude 5480 Bundle" requisitionPosition="1" username="10157067">
				<RequisitionCreationStatus result="success">
					<RequisitionInitialState>
						Pending
					</RequisitionInitialState>
				</RequisitionCreationStatus>
			</RequisitionRef>
		</ObjectErrors>
	</ResponseMessage>
</PurchaseRequisitionMessage>"""
    return retVal

def testResponseError():
    retVal = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE PurchaseRequisitionMessage SYSTEM "https://usertest-messages.sciquest.com/app_docs/dtd/requisition/PRImport.dtd">
<PurchaseRequisitionMessage version="1.0">
	<Header>
		<MessageId>
			01dbeefe-b5f8-466c-9cc0-017f1e1c22f5
		</MessageId>
		<Timestamp>
			2022-02-21T16:07:14.805-05:00
		</Timestamp>
	</Header>
	<ResponseMessage>
		<Status>
			<StatusCode>
				500
			</StatusCode>
			<StatusText>
				Success (Counts:  Total documents attempted=1, Total documents completed=1.  Documents successful without warnings=1)
			</StatusText>
		</Status>

		<ObjectErrors>
			<RequisitionRef requisitionId="3466726" requisitionName="UMLOW-IT-COPR-DEV-0000054 (, ) - Dell Latitude 5480 Bundle" requisitionPosition="1" username="10157067">
				<RequisitionCreationStatus result="success">
					<RequisitionInitialState>
						Pending
					</RequisitionInitialState>
				</RequisitionCreationStatus>
			</RequisitionRef>
		</ObjectErrors>
	</ResponseMessage>
</PurchaseRequisitionMessage>"""
    return retVal


def process_POREQ(currData, currBasename, COMMITjson, CITEMSjson, COMPANIESjson, FSjson, PROJjson, filePath, sendXML,sendToPROD):
    # currFile = eb2bw.tstamper2() + "_debug.xml"
    eb2bwSuccess = True
    xml = xmlHeader(sendToPROD)
    commitData = getCommitmentData(COMMITjson, currData["MappedCostID"])
    ######################################################## HEADER DATA ###############################################
    # 1. Requisition Name
    # print POREQjson["d"][p]["ProcessCounter"]# Need to pad to 5 digits
    pCount = padProc(currData["ProcessInstance"]["InstanceCounter"])
    # print POREQjson["d"][p]["ProcessPrefix"] # Append " - " plus padded Counter
    currReqName = currData["ProcessPrefix"] + " - " + pCount + "| LEB"
    xml += "<RequisitionName>" + currReqName + "</RequisitionName>\n"
    # print "1: Req Name", currReqName

    # 2. description Is there a character limit?
    currDesc = currData["DataField_Description"] + " via UML FIS LEB App"
    # print "2: Description", currDesc
    xml += "<Description>" + currDesc + "</Description>\n"

    # 3 Username (Buyways x digits)
    # print "Buyways User id", POREQjson["d"][p]["DataField_username"]
    currUsername = currData["DataField_username"]
    # currUsername = "10157067" # CAREFUL! HARDCODING BECAUSE OF PERMISSIONS ERROR, NON CATALOG ITEM
    xml += "<Requestor>\n<UserProfile username=\"" + currUsername + "\"/>\n</Requestor>\n"
    # print "3: Username", currUsername

    # 4a Shipping Address: where do we find Address Code in e-builder?
    # which means getting and sending address details to function

    # xml += eb2bw.xmlShippingAddress("150 Wilder Street","Peter Brigham","FIS")
    xml += xmlShippingAddress(currData)
    # xml+= eb2bw.xmlShippingAddress_HARDWIRED("")

    # 4b Must be after shipping address
    # Example: 310255|POREQ - 00012||1. Purchase Order
    currProjID = currData["ProjectID"]
    currFMP = getFMP(PROJjson, currProjID)
    # Commitment Type has an & in it, which is a reserved character in XML. We need a safeify function but for now:
    if commitData["CommitmentType"] == "4. Purchase Order-House Doctors & OPM's":
        print("Caught type 4, &, replaced")
        currCommitType = "4. Purchase Order-House Doctors and OPMs"
    else:
        currCommitType = commitData["CommitmentType"]
    currInternalNote = currFMP + "|" + currData["ProcessPrefix"] + " - " + pCount + "||" + currCommitType
    xml += "<InternalInfo><Note>" + currInternalNote + "</Note></InternalInfo>"
    # print "4 Internal Note:", currInternalNote

    # 5 origin code
    currOriginCode = "LEB"  # always LEB, Lowell e-builder
    xml += """<CustomFieldValueSet name="Origin Code">\n<CustomFieldValue>\n<Value>"""
    xml += currOriginCode + "</Value>\n</CustomFieldValue>\n</CustomFieldValueSet>\n"
    # print "5: Origin code", currOriginCode

    # 6 External Req #
    currExtReq = "L-" + currData["ProcessPrefix"] + " - " + pCount
    xml += "<CustomFieldValueSet name=\"External Req #\"><CustomFieldValue>"
    xml += "<Value>" + currExtReq + "</Value>"
    # print "5: External Req #", currExtReq
    xml += """
            </CustomFieldValue>
          </CustomFieldValueSet>
        </RequisitionHeader>"""

    # 7 Supplier Number - commitment has company ID, use that to lookup company number in Company data

    # print "CompanyID", commitData["CompanyID"]
    currSupplierNumber = getSupplierNumber(COMPANIESjson, commitData["CompanyID"])
    print("????", currSupplierNumber, commitData["CompanyID"])
    xml += """
        <RequisitionSupplierGroup>
          <RequisitionSupplierGroupInfo>
            <Supplier>
              <SupplierNumber>"""
    # currSupplierNumber = "0000106655" # HARDCODED: Supplier in example doesn't exist in TEST
    # add: if sendtoPROD, use real supplier number
    xml += currSupplierNumber

    xml += """</SupplierNumber>
            </Supplier>
          </RequisitionSupplierGroupInfo>"""
    # print "6: Supplier Number", currSupplierNumber

    # C HANGE THIS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # get we need to pass in CITEMS and FSjson
    # or, call them from here
    # or, pass in itemData
    itemData = getItemData(CITEMSjson, currData["MappedCostID"])
    print("!!!>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>!", itemData)

    # !!!!!! This is where the loop goes
    # How do we know how many line items? Data Structure, hold them, count them
    ########################################### LOOP FOR LINE ITEMS ################################################
    print("Going to xmlLine")
    print("Current speedtype is:", currSpeedtype)
    
    
    for lNum in sorted(itemData):
        print(lNum)
        lineResult = xmlLineItem(lNum, itemData[lNum], FSjson, currData["DataField_Description"])
        print(lineResult)
        if lineResult[:15] == "eb2bw failed:::":
            # print "break here"
            eb2bwSuccess = False
            xml = lineResult
        else:
            xml += lineResult
    # Close the Req
    if eb2bwSuccess:
    
        xml += """</RequisitionSupplierGroup>
              </PurchaseRequisition>
            </PurchaseRequisitionMessage>
            """


        # NOW, send xml and capture/log response
        # 220121 Moving this inside the loop
        currFile = tstamper2() + "_debug.xml"
        ofile = open((filePath + currFile), "w")
        ofile.write(xml)
        ofile.close()
        if sendXML:
            headers = {'Content-Type': 'application/xml'}  # set what your server accepts
            if sendtoPROD:
                theResponse = requests.post('https://integrations.sciquest.com/apps/Router/PRXMLImport', data=xml,
                                            headers=headers).text
                print("????", theResponse)
                resultsFilename = createLogFile(currBasename, theResponse)
                print("????", resultsFilename)
                resultsFile = open((filePath + resultsFilename), "w")
                resultsFile.wrtite(theResponse)
                resultsFile.close()
            else:
                theResponse = requests.post('https://usertest-messages.sciquest.com/apps/Router/PRXMLImport', data=xml,
                                            headers=headers).text
                # PARSE for 200/not 200
                # print theResponse
                # resultsFilename = createLogFile(currBasename,theResponse)
                # print currBasename
                resultsFilename = createLogFile(("TEST_" + currBasename), theResponse)
                print("    ", resultsFilename)
                resultsFile = open(resultsFilename, "w")
                resultsFile.write(theResponse)
                resultsFile.close()
        else:
            ignoreThis = 1
            # print xml
    return eb2bwSuccess


def write_currPOREQ(COMMITjson, currData,PROJjson, COMPANIESjson, CITEMSjson, FSjson, FRjson, sendToPROD):

    xml = xmlHeader(sendToPROD)
    #for d in currData["LineItems"]:
        #print("|||||", d, type(d))
    print(currData["LineItems"][0]["CommitmentItem"]["CommitmentId"])
    HCMAPPEDCOSTID = currData["LineItems"][0]["CommitmentItem"]["CommitmentId"]
    
    #print(currData["LineItems"]["CommitmentItem"]["CommitmentId"])
    # 230713 Hi, it's me... I'm the problem, it's me
    # how do we get this ID? It's currData field "CommitmentId" but it's in line items which is a list of dicts
    #HCMAPPEDCOSTID = 'fbbf98a7-3b1a-47b1-bf87-61e964df0fd0'
    # what if it's multiline? do this at the line level???
    #HCMAPPEDCOSTID = currData['LineItems'][0]['CommitmentId']

    #230713 problem here. We got new HCMAPPEDCOSTID but commitData has bad data
    commitData = getCommitmentData(COMMITjson, HCMAPPEDCOSTID)
    ######################################################## HEADER DATA ###############################################
    #1. Requisition Name
    #print POREQjson["d"][p]["ProcessCounter"]# Need to pad to 5 digits
    pCount = padProc(currData["ProcessInstance"]["InstanceCounter"])
    #print POREQjson["d"][p]["ProcessPrefix"] # Append " - " plus padded Counter
    currReqName = currData["Process"]["Prefix"] + " - " + pCount + "| LEB"
    xml += "<RequisitionName>" + currReqName + "</RequisitionName>\n"
    #print ("1: Req Name", currReqName)

    #2. description Is there a character limit?
    currDesc = currData['ProcessInstance']['DataFields']['Description'] + " via UML FIS LEB App"
    #print ("2: Description", currDesc)
    xml += "<Description>" + currDesc + "</Description>\n"

    #3 Username (Buyways x digits)
    #print "Buyways User id", POREQjson["d"][p]["DataField_username"]
    currUsername = currData['ProcessInstance']['DataFields']['username']
    currUsername = "10157067" # CAREFUL! HARDCODING BECAUSE OF PERMISSIONS ERROR, NON CATALOG ITEM
    xml += "<Requestor>\n<UserProfile username=\"" + currUsername + "\"/>\n</Requestor>\n"
    #print ("3: Username", currUsername)

    #4a Shipping Address
    #xml += eb2bw.xmlShippingAddress("150 Wilder Street","Peter Brigham","FIS")
    xml += xmlShippingAddress(currData)

    #4b Must be after shipping address
    # Example: 310255|POREQ - 00012||1. Purchase Order
    currProjID = currData["ProcessInstance"]["PortalId"]
    currFMP = getFMP(PROJjson, currProjID)
    #230713 - problem with commitData???
    print(commitData["commitmentType"])
    currInternalNote = currFMP + "|" + currData["Process"]["Prefix"] + " - " + pCount + "||" + commitData["commitmentType"]
    if "&" in currInternalNote:
        currInternalNote = currInternalNote.replace("&","and")
    ##### Jul 29, 2022 NEED TO SAFEIFY THE COMMITMENT TYPE BECAUSE TYPE 4 has an "&"
    xml += "<InternalInfo><Note>" + currInternalNote + "</Note></InternalInfo>\n"
    #print ("4 Internal Note:", currInternalNote)


    #5 origin code
    currOriginCode = "LEB" # always LEB, Lowell e-builder
    xml += """<CustomFieldValueSet name="Origin Code">\n<CustomFieldValue>\n<Value>"""
    xml += currOriginCode + "</Value>\n</CustomFieldValue>\n</CustomFieldValueSet>\n"
    #print ("5: Origin code", currOriginCode)

    #6 External Req #
    currExtReq = "L-" + currData["Process"]["Prefix"] + " - " + pCount
    xml += "<CustomFieldValueSet name=\"External Req #\"><CustomFieldValue>"
    xml += "<Value>" + currExtReq + "</Value>"
    #print ("6: External Req #", currExtReq)
    xml += """
        </CustomFieldValue>
      </CustomFieldValueSet>
    </RequisitionHeader>"""

    #7 Supplier Number - commitment has company ID, use that to lookup company number in Company data

    #print "CompanyID", commitData["CompanyID"]
    currSupplierNumber = getSupplierNumber(COMPANIESjson, commitData["companyID"])
    xml += """
    <RequisitionSupplierGroup>
      <RequisitionSupplierGroupInfo>
        <Supplier>
          <SupplierNumber>"""
    #currSupplierNumber = "0000049797" # HARDCODED: Supplier in example doesn't exist in TEST
    xml += currSupplierNumber

    xml += """</SupplierNumber>
        </Supplier>
      </RequisitionSupplierGroupInfo>"""
    #print ("7: Supplier Number", currSupplierNumber)

    itemData = getItemData(CITEMSjson,HCMAPPEDCOSTID)

    # Speedtype data
    # need error checking on all
    # this should be a function!!!!!
    """
    currSTdata = getFundingSourceData(FSjson, "111841")
    STdata = {"PC Business Unit":"none","Fund":currSTdata["Fund"],
              "Department":currSTdata["Dept. ID"],"Account":"735100-L","Speedtype":"111841-L",
                   "Program":"G00-L","Project":"none","Activity Id":"none","Campus PO Number Prefix":"L0"}
  
    print("Business Unit (substitute -none-:\t",currSTdata["Business Unit"])
    print("Fund, strip desc. add -L:\t\t",currSTdata["Fund"])
    print("Department, strip description:\t\t",currSTdata["Dept. ID"])
    print("Program:\t\t\t\t", currSTdata["Program"])
    print("Project:\t\t\t\t", currSTdata["Project ID"])
    print("Activity ID - not in ST custom fields??? - always none?")
    print("Campus PO Number Prefix - not in ST custom fields??? - always L0?")
    """
    # !!!!!! This is where the loop goes
    # How do we know how many line items? Data Structure, hold them, count them
    ########################################### LOOP FOR LINE ITEMS ################################################
    for lNum in sorted(itemData):
        xml += xmlLineItem(lNum, itemData[lNum], FSjson, currData['ProcessInstance']["DataFields"]["Description"])
    # Close the Req

    xml += """</RequisitionSupplierGroup>
      </PurchaseRequisition>
    </PurchaseRequisitionMessage>
    """

    return xml

# This Can be removed - Logic and Functionality Rewritten
def makeLogFilename(currData, PROJjson):
    currProjID = currData['ProcessInstance']["PortalId"]
    currFMP = getFMP(PROJjson, currProjID) # Error checking?
    currIDnote = currFMP + "_" + currData['Process']['Prefix'] + " - " + str(currData['ProcessInstance']["InstanceCounter"])
    currLogFilename =  currIDnote + ".xml"
    return currLogFilename
# This Can be removed - Logic and Functionality Rewritten
def checkSuccessLogs(currSuccessFilename):
    retVal = exists(currSuccessFilename)
    return retVal
# This Can be removed - Logic and Functionality Rewritten
def logSuccess(currSuccessFilename, currResponse):
    successFile = open((currSuccessFilename), "w")
    successFile.write(currResponse)
    successFile.close()
    return "LOGGED"
# This Can be removed - Logic and Functionality Rewritten
def logError(errorPath, currResponse):
    errorFile = open(errorPath, "w")
    errorFile.write(currResponse)
    errorFile.close()
    return "ERROR LOGGED"


# The Below Methods are for the modified Workflow of Code

def checkStatusCode(xml):
    respXML = xmltodict.parse(xml)
    retVal = ""
    try:
        statusCode = respXML["PurchaseRequisitionMessage"]["ResponseMessage"]["Status"]["StatusCode"]
        print(type(statusCode))
        if statusCode == 200 or statusCode == "200":
            retVal = "Success"
        else:
            retVal = "Error_" + str(statusCode)
    except:
        retVal = "Error - unreadable status code"
        print("WARNING: checkStatusCode failed, unreadable status code in response message")
    return retVal


def checkExternalComments(POREQdata):
    extCmnts = POREQdata['ProcessInstance']['DataFields']['External Comments']
    if extCmnts.startswith("Successfully Sent to Buyways on"):
        return "alreadySent"
    elif extCmnts.startswith("Error when tried to Buyways on"):
        return "errorWhenTried"
    else:
        return "toBeSent"

def updateExternalComments(POREQdata, status):
    projectName = POREQdata['Project']['ProjectName']
    processPrefix = POREQdata['Process']['Prefix']
    processCounter = POREQdata['ProcessInstance']['InstanceCounter']
    currTimeStamp = tstamper()
    if status == "Success":
        comments = "Successfully Sent to Buyways on " + str(currTimeStamp)
    elif status.startswith("Error"):
        comments = "Error when tried to Buyways on " + str(currTimeStamp)
    else:
        comments = ''
    data =\
        {
        "options": {
            "projectIdentifier": "ProjectName",
            "processPrefix": "POREQ",
            "importMode": "Entity"
        },
        "data": [
            {
                    "projectIdentifier": projectName,
                    "processCounter": processCounter,
                    "trackingPrefix": processPrefix,

                    "processDataFields": {
                        "External Comments": comments

                },
                    "status": "Submitted"
            }
        ]
    }
    theURL = 'https://api2.e-builder.net/api/v2/noncostprocesses/import'
    eb.postTOAPI(theURL,data)
    print("External Comments of ", processPrefix, "- ", processCounter, "is Changed to ", comments )

def getPOREQnum(POREQdata):
    pCount = POREQdata["ProcessInstance"]["InstanceCounter"]
    POREQnum = POREQdata["Process"]["Prefix"] + " - " + pCount
    return POREQnum

def createErrorLogFile(currResponse,logErrorPath):
    #responsefile = open('Error_500_APP200_POREQ - 58.xml')
    #responseContent = responsefile.read()
    # The above lines need to be replaced with the next line when sending data to actual server
    responseContent = currResponse
    responseData = xmltodict.parse(responseContent, encoding='utf-8')
    errorStatusCode = str(responseData['PurchaseRequisitionMessage']['ResponseMessage']['Status']['StatusCode'])
    errorStatusMessage = str(responseData['PurchaseRequisitionMessage']['ResponseMessage']['Status']['StatusText'])
    errorMessage = str(responseData['PurchaseRequisitionMessage']['ResponseMessage']['ObjectErrors']['RequisitionRef']['Error']['ErrorMessage'])
    errorLog = 'Error Status Code: ' + errorStatusCode + '\nError Status Message: ' + errorStatusMessage + '\nError Message: ' + errorMessage
    POREQnum = str(responseData['PurchaseRequisitionMessage']['ResponseMessage']['ObjectErrors']['RequisitionRef']['@requisitionName']).split('|')[0]
    #errorFile = open(logErrorPath + POREQnum + '_Error_Log.txt','w')
    errorFile = open(logErrorPath + POREQnum + '_Error_Log.txt', 'w')
    errorFile.write(errorLog)
    errorFile.close()

def createErrorLogFileTest(POREQdata, logErrorPath):
    responsefile = open('Error_500_APP200_POREQ - 58.xml')
    responseContent = responsefile.read()
    # The above lines need to be replaced with the next line when sending data to actual server
    #responseContent = response
    responseData = xmltodict.parse(responseContent, encoding='utf-8')
    errorStatusCode = str(responseData['PurchaseRequisitionMessage']['ResponseMessage']['Status']['StatusCode'])
    errorStatusMessage = str(responseData['PurchaseRequisitionMessage']['ResponseMessage']['Status']['StatusText'])
    errorMessage = str(responseData['PurchaseRequisitionMessage']['ResponseMessage']['ObjectErrors']['RequisitionRef']['Error']['ErrorMessage'])
    errorLog = 'Error Status Code: ' + errorStatusCode + '\nError Status Message: ' + errorStatusMessage + '\nError Message: ' + errorMessage
    #POREQnum = str(responseData['PurchaseRequisitionMessage']['ResponseMessage']['ObjectErrors']['RequisitionRef']['@requisitionName']).split('|')[0]
    POREQnum = str(POREQdata['Process']['Prefix']) + '-' + str(POREQdata['ProcessInstance']['InstanceCounter'])
    filename = 'Error' + errorStatusCode + '_' + POREQnum + '_Error_Log.txt'
    #errorFile = open(logErrorPath + POREQnum + '_Error_Log.txt','w')
    errorFile = open(logErrorPath + filename , 'w')
    errorFile.write(errorLog)
    errorFile.close()

def resetExternalComments(POREQdata):
    projectName = POREQdata['Project']['ProjectName']
    processPrefix = POREQdata['Process']['Prefix']
    processCounter = POREQdata['ProcessInstance']['InstanceCounter']
    currTimeStamp = eb2bw.tstamper()
    comments = 'None'
    data =\
        {
        "options": {
            "projectIdentifier": "ProjectName",
            "processPrefix": "POREQ",
            "importMode": "Entity"
        },
        "data": [
            {
                    "projectIdentifier": projectName,
                    "processCounter": processCounter,
                    "trackingPrefix": processPrefix,

                    "processDataFields": {
                        "External Comments" : comments

                },
                    "status": "Submitted"
            }
        ]
    }
    theURL = 'https://api2.e-builder.net/api/v2/noncostprocesses/import'
    eb.postTOAPI(theURL,data)
    print('External Comments of POREQ - ', processCounter, 'has been reset')
