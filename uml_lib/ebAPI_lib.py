#!/usr/bin/env python
# coding: utf-8

import json
from pathlib import Path
from urllib.parse import urlencode
from typing import Optional
from uml_lib.ebAPI_config import eBuilderConfig, load_config
import concurrent.futures
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uml_lib.ebAPI_tokenresponse import eBuilderTokenResponse
from uml_lib.ebAPI_response import ebResponse, ResponseMeta

# """
# ebAPI_lib v2.0
##
#
# 3/13/2023
# Adding Code for a Method to use POST command to the API
#
# 3/9/2023
# Adding code for fetching POREQ, CommitmentItems, FundingSources
# Adding code to fetch data from Local Cache/Daily Data Imports
# 2/22/2023
# Modified the code to fetch the custom fields parallely instead of one by one to reduce the runtime
# 80 records are parallely fetched in each iteration as pulling large number of records parallely is overloading the API Connection
#
#
# 1/22/2023
# Rewrote the entire codebase to work with new Rest API of E-Builder
#
# """
# ebAPI_lib v1.0
##
#
# 5/2/2022
# - Adding a function to check commitment types, using previous commitments for vendors
#
# 1/8/2021
# adding invoice status (paid, approved)
# 5/21/2020
# Multi-line PO to test: L000766628
#
# 9/3/2021
# Adding FM Dept lead to projects for filtering POs
# And, with that, changing activePOs so that it takes ebProjs as input
# rather than calls get_ebProjs
#
# CommitmentItems has Funding Rule but not speedtypes
#
# We need EB commitment number and PS PO number
# WE need commitment item number
# We need Funding RUle
# """
# """
# Right now, we pull all POs and Invoices, regardless of status (Approved, Draft, etc)
# But, EB reports on approved only. Just a cautionary note for now.
# What next?
# 2 routes:
# 1. we just check what's in ebuilder against buyways. This should** be pretty easy,
# both coding and reality, since we have PO and Invoice numbers, brought in from buyways
# 2. We identify all FM related POs and Invoices in PS/buyways, then we check against
# eBuilder. Categories:
#     1. Facilities Project is in ebuilder or not
#     2. PO is in or not
#     3. Invoice is in or not
# Question: what is the PS or buyways report that yields all FM projects,
# POs, and/or invoices?
# """
#
# # Connection to the API

_APIToken: Optional[eBuilderTokenResponse] = None
_APIConfig: Optional[eBuilderConfig] = None

def get_config() -> eBuilderConfig:
    global _APIConfig

    if _APIConfig is not None:
        return _APIConfig

    _APIConfig = load_config(Path("config.ebuilder.json"))

    return _APIConfig

def get_ebToken(timeout: float = 30.0) -> eBuilderTokenResponse:
    global _APIToken

    if _APIToken is not None:
        return _APIToken

    cfg = get_config()
    url = cfg.hostname + "/api/v2/authenticate"

    form = {
        "grant_type": "password",
        "username": cfg.username,
        "password": cfg.password,
    }

    data = urlencode(form).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            text = resp.read().decode(charset)
    except HTTPError as e:
        # Optionally read error body for debugging
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise HTTPError(e.url, e.code, f"{e.reason}. Response body: {body}", e.headers, e.fp)
    except URLError:
        raise

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Expected JSON response, got: {text[:200]}") from e

    if not isinstance(payload, dict):
        raise ValueError("Expected JSON object at top level in token response")

    _APIToken = eBuilderTokenResponse.from_dict(payload)
    return _APIToken

def get_request(url: str, timeout: float = 30.0) -> str:
    """
    Perform a single GET request with auth + JSON headers and return decoded text.
    Adds the response body to HTTPError for easier troubleshooting.
    """
    token = get_ebToken()
    req = Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token.access_token}")
    req.add_header("Accept", "application/json")
    try:
        # Open the URL with timeout and decode using server-provided charset (default utf-8).
        with urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset)
    except HTTPError as e:
        # If the server returns an error status, try to include its body in the exception.
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        # Re-raise HTTPError with an augmented message that includes the body preview.
        raise HTTPError(e.url, e.code, f"{e.reason}. Response body: {body}", e.headers, e.fp)
    except URLError:
        # Propagate connection/transport errors as-is for the caller to handle.
        raise


def APIconnect(module: str, timeout: float = 30.0) -> ebResponse:
    cfg = get_config()

    # Build the base URL. `?$format=json` requests JSON output; pagination params get appended later.
    base_url = cfg.hostname + f"/api/v2/{module}?$format=json&limit=1"

    # Fetch the first page.
    text = get_request(base_url)

    # Parse the response as JSON, including a helpful preview on parse failure.
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        preview = text[:200] if isinstance(text, str) else ""
        raise ValueError(f"Response was not valid JSON (first 200 chars): {preview}") from e

    # Top-level must be an object (dict), not an array or primitive.
    if not isinstance(payload, dict):
        raise ValueError("Expected top-level JSON object")

    # Extract expected top-level fields (some may be optional depending on endpoint).
    query = payload.get("query")
    meta = payload.get("meta")
    records = payload.get("records")

    # Normalize query to a string; fallback to the module name if it's missing/non-string.
    if not isinstance(query, str):
        query = str(module)

    # Validate presence/type of the meta object.
    if not isinstance(meta, dict):
        raise ValueError("Expected 'meta' to be an object")

    # Ensure required meta keys exist.
    required_meta_keys = ("href", "offset", "limit", "size", "totalRecords")
    missing_meta = [k for k in required_meta_keys if k not in meta]
    if missing_meta:
        raise ValueError(f"Missing meta keys: {', '.join(missing_meta)}")

    # Parse and type-check meta fields, raising ValueError with the original exception chained.
    try:
        current_offset = int(meta["offset"])
        limit = int(meta["limit"])
        size = int(meta["size"])
        total_records = int(meta["totalRecords"])
        href = str(meta["href"])
    except Exception as e:
        raise ValueError(f"Invalid 'meta' field types: {e}") from e

    # The 'records' field may be:
    #   - None: no data yet (treat as empty list)
    #   - list: standard list of records (typical for paginated collections)
    #   - other (e.g., dict): a single object response; return early in that case
    if records is None:
        all_records = []
    elif isinstance(records, list):
        # Copy to avoid mutating the original list from the parsed payload.
        all_records = list(records)
    else:
        # Single-object response: construct meta and return immediately.
        meta_obj = ResponseMeta(
            href=href,
            offset=current_offset,
            limit=limit,
            size=size,
            totalRecords=total_records,
        )
        return ebResponse(query=query, meta=meta_obj, records=records)

    # Auto-pagination loop: continue requesting pages until we've collected all records.
    while total_records > len(all_records):
        # Compute next offset; guard against non-progressing offsets (to avoid infinite loops).
        next_offset = current_offset + limit
        if next_offset <= current_offset:
            break  # Safety guard: something is wrong with pagination numbers.

        # If we've already pulled 'size' records and totalRecords == size, there's nothing more.
        if len(all_records) >= size and total_records == size:
            break  # Nothing more to fetch

        # Request next page by appending &offset.
        page_url = f"{base_url}&offset={next_offset}"
        page_text = get_request(page_url)

        # Parse the subsequent page; include preview on parse failure.
        try:
            page_payload = json.loads(page_text)
        except json.JSONDecodeError as e:
            preview = page_text[:200] if isinstance(page_text, str) else ""
            raise ValueError(f"Subsequent page was not valid JSON (first 200 chars): {preview}") from e

        if not isinstance(page_payload, dict):
            raise ValueError("Expected top-level JSON object for subsequent page")

        # Extract meta and records for the page; meta may adjust iteration variables.
        page_meta = page_payload.get("meta")
        page_records = page_payload.get("records")

        if isinstance(page_meta, dict):
            try:
                # Use page-provided values when present; otherwise fall back to prior ones.
                page_offset = int(page_meta.get("offset", next_offset))
                page_limit = int(page_meta.get("limit", limit))
                page_size = int(page_meta.get("size", 0))

                # Update iteration state with the page's meta.
                current_offset = page_offset
                limit = page_limit
                size = page_size  # size of the last fetched page
                href = str(page_meta.get("href", href))

                # totalRecords should be stable across pages; if provided, keep it consistent.
                pr_total = page_meta.get("totalRecords")
                if pr_total is not None:
                    total_records = int(pr_total)
            except Exception as e:
                raise ValueError(f"Invalid 'meta' field types on subsequent page: {e}") from e
        else:
            # If no meta present, at least advance our offset based on what we requested.
            current_offset = next_offset

        # Handle no/empty records cases and enforce list type for subsequent pages.
        if page_records is None:
            break  # No more data available from the server.
        if not isinstance(page_records, list):
            raise ValueError("Expected 'records' to be a list on subsequent page")
        if not page_records:
            break  # Empty page -> stop.

        # Accumulate records and stop if we've reached the advertised total.
        all_records.extend(page_records)
        if len(all_records) >= total_records:
            break

    # Build final meta reflecting the aggregation we performed.
    final_meta = ResponseMeta(
        href=href,
        offset=current_offset,
        limit=limit,
        size=len(all_records),  # number of records actually aggregated
        totalRecords=total_records,
    )

    # Return the structured response with the full dataset.
    return ebResponse(query=query, meta=final_meta, records=all_records)

def postTOAPI(URL, data, timeout: float = 30.0) -> Any:
    token = get_ebToken()
    request = Request(method='POST', url=URL, data=data)
    request.add_header('Content-Type', 'application/json')
    request.add_header('Authorization', 'Bearer ' + token.access_token)

    try:
        with urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            response = resp.read().decode(charset)
            data = json.loads(response)
            if 'records' not in data:
                print ('Data Import Failed!')
            else:
                print("Data imported Successfully!!!")

            return data
    except HTTPError as e:
        # Optionally read error body for debugging
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise HTTPError(e.url, e.code, f"{e.reason}. Response body: {body}", e.headers, e.fp)
    except URLError:
        raise

# # Projects

def write_FMP(proj_data):
    #ofile = open("D:\\arcgisserver\\directories\\arcgispub\\securedoc\\panos\\active_TDactive_FMPs.json","w")
    # Now, loop through eB Object, build rows with desired data plucked
    # How do iterate on unique values for campus, building?
    # Like utilization? We need to loop once and build data structure, indices to eb data
    OnS = []
    Planning = []
    PM = []
    i = len(proj_data)

    for j in range(0,i):
        # Need to check if there's data
        #currName = proj_data[j]["Name"]
        currLead = proj_data[j]["FM Department Lead"]
        #print ">>>>",currLead, proj_data[j]["Status"]
        if (proj_data[j]["status"] == "Active") or (proj_data[j]["status"] == "TD Active"):
            if currLead == "O&S":
                OnS.append(proj_data[j]["FMP Number"])
            if currLead == "Planning":
                Planning.append(proj_data[j]["FMP Number"])
            if currLead == "Project Management":
                PM.append(proj_data[j]["FMP Number"])

    activeFMPs = {"OnS":OnS,"Planning":Planning,"PM":PM}

    #ofile.write(json.JSONEncoder().encode(activeFMPs))
    #ofile.close()

def get_project_data(record):
    cfg = get_config()

    project_id = record["projectId"]
    theURL = cfg.hostname + "/api/v2/Projects/" + project_id + "/customfields"
    response = get_request(theURL)
    custom_fields_raw = json.loads(response)
    custom_fields_details = custom_fields_raw['details']
    dict_custom_fields_details = {}
    for j in range(len(custom_fields_details)):
        dict_custom_fields_details[custom_fields_details[j]['name']] = custom_fields_details[j]['value']
    project_data = record | dict_custom_fields_details
    return project_data

def get_project_allData():
    response = APIconnect("Projects")
    records = response.records
    project_all_data = []
    i = 0
    while i < len(records):
        record_batch = records[i:i+80]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_invoice = {executor.submit(get_project_data, record): record for record in record_batch}
            for future in concurrent.futures.as_completed(future_to_invoice):
                project_data = future.result()
                project_all_data.append(project_data)
        i += 80
    return project_all_data

def get_active_project_all_data():
    records = APIconnect("Projects")['records']
    active_records = [record for record in records if record['status'] in ["Active", "TD Active"]]
    active_project_all_data = []
    i = 0
    while i < len(records):
        record_batch = active_records[i:i+80]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_invoice = {executor.submit(get_project_data, record): record for record in record_batch}
            for future in concurrent.futures.as_completed(future_to_invoice):
                project_data = future.result()
                active_project_all_data.append(project_data)
        i += 80
    return active_project_all_data

def get_Projects():
    #proj_data = get_project_allData()
    proj_data = getDataFromCache("Projects")
    i = len(proj_data)
    write_FMP(proj_data)
    ebProjs = {}
    # Build FMP dictionary
    for j in range(0,i):
        try:
            # strip trailing white space?
            currProjName = proj_data[j]["name"].encode("utf-8")
            currFMP = proj_data[j]["FMP Number"].encode("utf-8")
            currStatus = proj_data[j]["status"]
            currLeadDept = proj_data[j]["FM Department Lead"]

            # NOT INCLUDING "TD ACTIVE": these should not have Cost enabled in EB
            #if currStatus == "Active" or currStatus == "TD Active":
            ebProjs[currFMP] = {"status":currStatus,"Project Name": \
                                currProjName,"projectId":proj_data[j]["projectId"],"FMlead":currLeadDept}
        except:
            print ("no go", proj_data[j]["name"])
    return(ebProjs)

def get_active_Projects():
    #proj_data = get_active_project_all_data()
    proj_data = getDataFromCache("ActiveProjects")
    i = len(proj_data)
    write_FMP(proj_data)
    ebProjs = {}
    # Build FMP dictionary
    for j in range(0,i):
        try:
            # strip trailing white space?
            currProjName = proj_data[j]["name"].encode("utf-8")
            currFMP = proj_data[j]["FMP Number"].encode("utf-8")
            currStatus = proj_data[j]["status"]
            currLeadDept = proj_data[j]["FM Department Lead"]

            # NOT INCLUDING "TD ACTIVE": these should not have Cost enabled in EB
            #if currStatus == "Active" or currStatus == "TD Active":
            ebProjs[currFMP] = {"status":currStatus,"Project Name": \
                                currProjName,"projectId":proj_data[j]["projectId"],"FMlead":currLeadDept}
        except:
            print ("no go", proj_data[j]["name"])
    return(ebProjs)

def get_FMP_from_EB_projID(i, ebProjs):
    theFMP = "NOT FOUND"
    for fmp in ebProjs:
        if ebProjs[fmp]["projectId"] == i:
            theFMP = fmp
            break
    return theFMP

# # Budgets

def get_budget_data(record):
    cfg = get_config()

    budget_id = record["budgetId"]
#    theURL = "https://api2.e-builder.net/api/v2/Budgets/" + budget_id + "/customfields"
#    response = requests.get(theURL, auth=BearerAuth(ebTok))

    theURL = cfg.hostname + "/api/v2/Budgets/" + budget_id + "/customfields"
    response = get_request(theURL)

    #custom_fields_raw = json.loads(response.content)
    custom_fields_raw = json.loads(response)
    custom_fields_details = custom_fields_raw['details']
    dict_custom_fields_details = {}
    for j in range(len(custom_fields_details)):
        dict_custom_fields_details[custom_fields_details[j]['name']] = custom_fields_details[j]['value']
    budget_data = record | dict_custom_fields_details
    return budget_data

def get_budget_all_data():
    records = APIconnect("Budgets")['records']
    budget_all_data = []
    i = 0
    while i < len(records):
        record_batch = records[i:i+80]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_budget = {executor.submit(get_budget_data, record): record for record in record_batch}
            for future in concurrent.futures.as_completed(future_to_budget):
                budget_data = future.result()
                budget_all_data.append(budget_data)
        i += 80
    return budget_all_data

def get_Budgets():
    #budg_data = get_budget_all_data()
    budg_data = getDataFromCache("Budgets")
    i = len(budg_data)

    ebBudgets = {}
    for j in range(0,i):
        try:
            # strip trailing white space?
            #print budg_data[j]["ProjectID"].encode("utf-8")
            #print budg_data[j]["Status"].encode("utf-8")
            #print budg_data[j]["CurrentBudget"].encode("utf-8")
            ebBudgets[budg_data[j]["projectId"].encode("utf-8")] = {"status":budg_data[j]["status"].encode("utf-8")\
                                                                    ,"Current Approved Budget":budg_data[j]["Current Approved Budget"].encode("utf-8")}
        except:
            print ("no go")
    return ebBudgets

# # Commitments

def get_commitment_data(record):

    cfg = get_config()

    commitment_id = record["commitmentID"]
   #theURL = "https://api2.e-builder.net/api/v2/Commitments/" + commitment_id + "/customfields"
    #response = requests.get(theURL, auth=BearerAuth(ebTok))

    theURL = cfg.hostname + "/api/v2/Commitments/" + commitment_id + "/customfields"
    response = get_request(theURL)

    #custom_fields_raw = json.loads(response.content)
    custom_fields_raw = json.loads(response)

    custom_fields_details = custom_fields_raw['details']
    dict_custom_fields_details = {}
    for j in range(len(custom_fields_details)):
        dict_custom_fields_details[custom_fields_details[j]['name']] = custom_fields_details[j]['value']
    commitment_data = record | dict_custom_fields_details
    return commitment_data

def get_commitment_all_data():
    records = APIconnect("Commitments")['records']
    commitment_all_data = []
    i = 0
    while i < len(records):
        record_batch = records[i:i+80]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_commitment = {executor.submit(get_commitment_data, record): record for record in record_batch}
            for future in concurrent.futures.as_completed(future_to_commitment):
                commitment_data = future.result()
                commitment_all_data.append(commitment_data)
        i += 80
    return commitment_all_data

def get_POs():
    #po_data = get_commitment_all_data()
    po_data = getDataFromCache("Commitments")
    i = len(po_data)
    ebPOs = {}
    # Check if this is for an Active project?
    for j in range(0,i):
        currProjID = po_data[j]["projectID"]
        currPOnum = po_data[j]["commitmentNumber"]

        currPOdata = {"Status":po_data[j]["status"],"CurrValue":po_data[j]["currentCommitmentValue"],\
                        "CommitmentID":po_data[j]["commitmentID"],"PS_PO":po_data[j]["PeopleSoft PO#"],\
                      "CompanyName":po_data[j]["companyName"],"CommitmentType":po_data[j]["commitmentType"],\
                      "Description":po_data[j]["description"]
                      }
        # Need Custom Field for PS PO
        """
        Commitment Items has funding rules!!! And speedtypes? And type?
        <d:FundingRuleID m:type="Edm.Guid">e1c27547-b798-410c-ad8b-84e447c81c72</d:FundingRuleID>
        <d:FundingRuleName>Rule 1 Campus Cash</d:FundingRuleName>
        Commitments has:
        <d:Custom_PeopleSoft_PO>L000978851</d:Custom_PeopleSoft_PO>
        <d:CommitmentType>1. Purchase Order</d:CommitmentType>
        """
        # check if FMP (Project ID is secure/non-human readable version)
        if currProjID in ebPOs: # we have at least 1 PO for this one already so update
            ebPOs[currProjID]["POs"].update({currPOnum:currPOdata})
        else:
            # first PO for this one Project ID
            ebPOs[currProjID] = {"POs":{currPOnum:currPOdata}}

    return(ebPOs)

def isPOinEB(p, ebPOs):
    retVal = False
    for c in ebPOs:
        if p in ebPOs[c]["POs"]:
            retVal = True
    return retVal

def get_activePOs(ebProjs):
    # August 10, 2022 adding "description" to dictionary, for multi line invoice imports
    #ebProjs = get_Projects()
    ebPOs = get_POs()
    activePOs = {}
    #problemPOs = ["L000836996", "L000838482", "L000838484","L000838488","L000838492","L000838493","L000838496","L000927106"]

    for p in ebPOs:
        isActive = False
        # VALID: EB may think PO is Active/approved but, unless we have PS PO number back (L000XXXXXX), it's not approved for real
        theFMP = get_FMP_from_EB_projID(p,ebProjs) # projID is lookup for EB "anonymous/non-human readable" Project ID
        if theFMP != "NOT FOUND":
            if ebProjs[theFMP]["status"] == "Active" or ebProjs[theFMP]["status"] == "Inactive" :
                isActive = True
                #print "Active in EB", theFMP
                for q in ebPOs[p]["POs"]:
                        # Add each PeopleSoft PO # (eb custom field) to dictionary, with FMP
                        # Oct. 20, 2021: Check if PO is closed!
                        if ebPOs[p]["POs"][q]["Status"] != "Closed":
                            activePOs[ebPOs[p]["POs"][q]["PS_PO"]] = {"FMP":theFMP,"Value":ebPOs[p]["POs"][q]["CurrValue"],\
                                                                  "Vendor":ebPOs[p]["POs"][q]["CompanyName"],\
                                                                      "PO_ID":ebPOs[p]["POs"][q]["CommitmentID"],\
                                                                      "CommitmentType":ebPOs[p]["POs"][q]["CommitmentType"],
                                                                      "Description":ebPOs[p]["POs"][q]["Description"]}
                        #else:
                            #print "Closed PO", ebPOs[p]["POs"][q]["PS_PO"]
                        # Add the value?
                #else:
                    #print "Not Active in EB", theFMP
            #else:
                #"FMP not found"
        #for p in activePOs:
            #print "****************", p, activePOs[p]["FMP"], activePOs[p]["Value"]
    build_commitTypes(activePOs)

    return(activePOs)

vendorTypes = {}

def get_commitType(currVendor):
    #global vendorTypes
    retVal = "NOT FOUND"
    #print type(currVendor)
    if currVendor in vendorTypes:
        #print "Found!", currVendor
        #print "+++++++++++++++++++++++++++++++++", vendorTypes[currVendor]
        try:
            if len(vendorTypes[currVendor]) == 1:
                retVal = vendorTypes[currVendor][0]
            else:
                retVal = "CHECK: MULTIPLE VALUES"
        except:
            ignoreThis = 1
            #print ".......failed on vendorTypes"
    """
    try:
        retVal = vendorTypes[v]
        if len(vendorTypes[v]) > 1:
            retVal = "CHECK TYPE: MULTIPLE VALUES"
    except:
        print ">?>?", currVendor
        retVal = "VENDOR NOT FOUND"
    """
    #print "from get_commitType:\n", retVal
    return retVal

# run this once, when POs list created
def build_commitTypes(activePOs):
    global vendorTypes
    #print('imhere')

    for p in activePOs:
        #print('checl')
        currVendor = activePOs[p]["Vendor"]#.encode("utf-8")
        currType = activePOs[p]["CommitmentType"]#.encode("utf-8")

        if currVendor not in vendorTypes:
            vendorTypes[currVendor] = [currType]
        else:
            if currType not in vendorTypes[currVendor]:
                vendorTypes[currVendor].append(currType)
    vendorTypes["DAEDALUS PROJECTS INC"] = ["4. Purchase Order-House Doctors & OPM's"]
    vendorTypes["DIAMOND RELOCATION INC"] = ["3. Purchase Order-Master Service Vendor/Contractor"]
    vendorTypes["EXPRESS SIGN & GRAPHICS INC"] = ["3. Purchase Order-Master Service Vendor/Contractor"]
    vendorTypes["MILLER DYER SPEARS INC"] = ["4. Purchase Order-House Doctors & OPM's"]
    vendorTypes["MODULEX NEW ENGLAND"] = ["3. Purchase Order-Master Service Vendor/Contractor"]
    vendorTypes["R-SQUARED OFFICE PANELS & FURNITURE INC"] = ["3. Purchase Order-Master Service Vendor/Contractor"]
    vendorTypes["STATE ELECTRIC CORPORATION"] = ["3. Purchase Order-Master Service Vendor/Contractor"]
    vendorTypes["TRC ENVIRONMENTAL CORPORATION"] = ["1. Purchase Order"]
    vendorTypes["TRIUMVIRATE ENVIRONMENTAL INC"] = ["1. Purchase Order"]
    vendorTypes["VAV INTL INC"] = ["4. Purchase Order-House Doctors & OPM's"]
    vendorTypes["WILLIAM LOWE & SONS CORP"] = ["3. Purchase Order-Master Service Vendor/Contractor"]

    return vendorTypes

    # For some vendors, we now have a set type that overrules previous multiple types used
    # print "From build commitTypes:\n", vendorTypes

# Commitment Items


def get_commitmentItems_data(record):
    cfg = get_config()

    commitment_id = record['commitmentID']

    #theURL = "https://api2.e-builder.net/api/v2/Commitments/" + commitment_id + "/items"
    #response = requests.get(theURL, auth=BearerAuth(ebTok))
    theURL = cfg.hostname + "/api/v2/Commitments/" + commitment_id + "/items"
    response = get_request(theURL)

    #item_data_raw = json.loads(response.content)
    item_data_raw = json.loads(response)

    item_data_details = item_data_raw['details']
    return item_data_details

def get_commitmentItems_allData():
    records = APIconnect("Commitments")['records']
    commitmentItemdata = []

    i = 0
    while i < len(records):
        record_batch = records[i:i+80]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_commitment = {executor.submit(get_commitmentItems_data, record): record for record in record_batch}
            for future in concurrent.futures.as_completed(future_to_commitment):
                commitment_data = future.result()
                commitmentItemdata.append(commitment_data)
        i += 80
        commitmentItemsAllData = []
        for i in range(len(commitmentItemdata)):
            for j in range(len(commitmentItemdata[i])):
                #print(commitmentItemdata[i][j])
                commitmentItemsAllData.append(commitmentItemdata[i][j])
    return commitmentItemsAllData

# # Invoices

def get_invoice_data(record):
    cfg = get_config()

    invoice_id = record["invoiceId"]

    #theURL = "https://api2.e-builder.net/api/v2/commitmentinvoices/" + invoice_id + "/customfields"
    #response = requests.get(theURL, auth=BearerAuth(ebTok))
    theURL = cfg.hostname + "/api/v2/commitmentinvoices/" + invoice_id + "/customfields"
    response = get_request(theURL)

    #custom_fields_raw = json.loads(response.content)
    custom_fields_raw = json.loads(response)

    custom_fields_details = custom_fields_raw['details']
    dict_custom_fields_details = {}
    for j in range(len(custom_fields_details)):
        dict_custom_fields_details[custom_fields_details[j]['name']] = custom_fields_details[j]['value']
    invoice_data = record | dict_custom_fields_details
    return invoice_data

def get_invoice_allData():
    records = APIconnect("commitmentinvoices")['records']
    invoice_all_data = []
    i = 0
    while i < len(records):
        record_batch = records[i:i+80]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_invoice = {executor.submit(get_invoice_data, record): record for record in record_batch}
            for future in concurrent.futures.as_completed(future_to_invoice):
                invoice_data = future.result()
                invoice_all_data.append(invoice_data)
        i += 80
    return invoice_all_data

def get_Invoices():
    #FILTER FOR ACTIVE PROJECTS ONLY!
    # TURN RETURN STATEMENT BACK ON: CHECK IT
    #<d:InvoiceNumber>X1388872</d:InvoiceNumber>
    #invoice_data = get_invoice_allData()
    invoice_data = getDataFromCache("Invoices")
    i = len(invoice_data)

    ebAPI_Invoices = []
    # Check if this is for an Active project?
    for j in range(0,i):
        if invoice_data[j]["Voucher ID"] is not None:
            if invoice_data[j]["Voucher ID"][0] == "X":
                ebAPI_Invoices.append(invoice_data[j]["Voucher ID"])
        #else:
            #print "No custom field... Status?", invoice_data[j]["status"]
    #print(ebAPI_Invoices)
    return ebAPI_Invoices

def isInvoiceInEB(voucherID, ebInvoices):
    retVal = False
    for v in range(0,len(ebInvoices)):
        if ebInvoices[v]["Voucher ID"] == voucherID:
            retVal = True
            break
    return retVal

def get_Invoices_dict():
    # FILTER FOR ACTIVE PROJECTS ONLY!
    # TURN RETURN STATEMENT BACK ON: CHECK IT
    # invoice_data = get_invoice_allData()
    invoice_data = getDataFromCache("Invoices")
    i = len(invoice_data)
    ebAPI_Invoices = {}
    # Check if this is for an Active project?
    for j in range(0,i):
        currInvNum = invoice_data[j]["invoiceNumber"]

        if invoice_data[j]["Voucher ID"] is not None:
            if invoice_data[j]["Voucher ID"][0] == "X":
                # DO we need VOID also? To avoid bringing in voided - they will throw exception
                if invoice_data[j]["status"] == "Approved" or invoice_data[j]["status"] == "Paid":
                    ebAPI_Invoices[invoice_data[j]["Voucher ID"]] = {"Status":invoice_data[j]["status"],"Source":"BW",\
                                                                         #"PO_ID":invoice_data[j]["CommitmentID"]
                                                                     }
        elif currInvNum[:5] == "PAYAP": # we need to check project for admin/test invoices?
            if invoice_data[j]["Status"] == "Approved" or invoice_data[j]["Status"] == "Paid":
                ebAPI_Invoices[invoice_data[j]["InvoiceNumber"]] = {"Status":invoice_data[j]["Status"],"Source":"EB",\
                                                                 #"PO_ID":invoice_data[j]["CommitmentID"],"InvAmt":invoice_data[j]["InvoiceAmount"]
                                                                    }
        # else:
            # print "No custom field... Status?", invoice_data[j]["Status"]
    # print(ebAPI_Invoices)
    return ebAPI_Invoices
#print(get_Invoices_dict())

def get_Invoices_for_Projs():
    # invoice_data = get_invoice_allData()
    invoice_data = getDataFromCache("Invoices")
    i = len(invoice_data)

    ebProjInvoices = {}
    # Check if this is for an Active project?
    for j in range(0,i):
        if invoice_data[j]["Voucher ID"] is not None:
            if invoice_data[j]["Voucher ID"][0] == "X":
                # What other values? PO anon id, voucher total - we really only need total for Project
                # InvoiceAmount
                # CommitmentID
                # ProjectID (anonymous)
                if invoice_data[j]["projectId"] in ebProjInvoices:
                    #print "add to existing"
                    ebProjInvoices[invoice_data[j]["projectId"]]["VoucherID"] = invoice_data[j]["Voucher ID"]
                    ebProjInvoices[invoice_data[j]["projectId"]]["Status"] = invoice_data[j]["status"]
                    ebProjInvoices[invoice_data[j]["projectId"]]["InvoiceAmt"] = invoice_data[j]["invoiceAmount"]
                    #ebProjInvoices[invoice_data[j]["projectId"]]["CommitmentID"] = invoice_data[j]["CommitmentID"]
                    ebProjInvoices[invoice_data[j]["projectId"]]["CompanyName"] = invoice_data[j]["companyName"]
                else:
                    #print "create new"
                    ebProjInvoices[invoice_data[j]["projectId"]] = {"VoucherID":invoice_data[j]["Voucher ID"],
                        "Status":invoice_data[j]["status"],"InvoiceAmt":invoice_data[j]["invoiceAmount"],\
                        #"CommitmentID":invoice_data[j]["CommitmentID"],"CompanyName":invoice_data[j]["companyName"]
                                                                    }

        #else:
            #print "No custom field... Status?", invoice_data[j]["Status"]
    # we need the PO and the anon PO id - to tie back to PO and FMP
    # print(ebProjInvoices)
    return ebProjInvoices

# print(get_Invoices_for_Projs())

# Not used
def get_Invoices_for_PAYAP_match():
    #invoice_data = get_invoice_allData()
    invoice_data = getDataFromCache("Invoices")
    i = len(invoice_data)

    ebInv = {}
    # Check if this is for an Active project?
    for j in range(0,i):
        ebInv[invoice_data[j]["invoiceNumber"]] = {#"Commitment":invoice_data[j]["CommitmentID"],
                                                   "VoucherID":invoice_data[j]["Voucher ID"],
                        "InvoiceAmt":invoice_data[j]["invoiceAmount"],"CompanyName":invoice_data[j]["companyName"], "ProjectID":invoice_data[j]["projectId"]}

    """
    allInv = 0
    payapInv = 0
    for p in ebInv:
        allInv += 1
        #print ">>>>>>>>>>>>", p
        if "PAYAP" in p:
            payapInv += 1
            print ">>>>>>>>>>>>>>>", p
            for k in ebInv[p]:
                print k, ebInv[p][k]
    print "Counts: all ", allInv, " and PayAp ", payapInv
    """
    return ebInv
#print (get_Invoices_for_PAYAP_match())

def getPOs_for_Invoices():
    # po_data = get_commitment_all_data()
    po_data = getDataFromCache("Commitments")
    i = len(po_data)
    # print "Got it:", i
    ebPOs = {}
    for j in range(0,i):
        currPOnum = po_data[j]["commitmentNumber"]
        # print "***",currPOnum
        # print ">>>", po_data[j]["Description"],"<<<"
        currPOdata = {"Status":po_data[j]["status"],"Desc":po_data[j]["description"]}
        ebPOs[currPOnum] = currPOdata
    # for k in ebPOs:
        # print k, ebPOs[k]["Desc"]
    # print(ebPOs)
    return ebPOs

# # Funding Rules

def get_fundingRules_allData():
    # Funding Rules does not have any custom fields; hence the all the data can be pulled from records field of APIconnect
    fundingRules_all_data = APIconnect("FundingRules")['records']
    return fundingRules_all_data
#print(get_fundingRules_allData())

def get_FundingRules():
    # 201216 Adding FMP, using parsing of description
    # 201211 We used to use an EB report, Excel format, to get this info. We need dictionary
    # with speedtype as key and funding rule name as value

    #fundRules_data = get_fundingRules_allData()
    fundRules_data = getDataFromCache("FundingRules")
    i = len(fundRules_data)
    #print "Got it:", i
    ebFundRules = {}
    for j in range(0,i):
        #currFundRuleID = fundRules_data[j]["FundingRuleID"]
        #print "***",currFundRuleID
        currFRdata = {"Name":fundRules_data[j]["name"],"Description":fundRules_data[j]["description"],"CreateBy":fundRules_data[j]["createdBy"]}
        #print currFRdata
        #if "FMP" in currFRdata["Description"]:
            #print "FMP: ", currFRdata["Description"]
        if "-" in currFRdata["Name"]:
            toks = currFRdata["Name"].split("-")
            #print toks
            # watch out: some have spaces around the "-"
            #toks[0] = toks[0].strip()
            if toks[1][0] == " ":
                currRule = str(toks[1][1:])
                # print ("OK, rule", currRule)
            else:
                currRule = str(toks[1])
            if "FMP" in currFRdata["Description"]:
                #print currFRdata["Description"]
                toks2 = currFRdata["Description"].split(" ")
                #currFMP = toks2[1].encode("ASCII","ignore")
                currFMP = str(toks2[1])
            else:
                currFMP = "XXXXXX"
            #print "Speedtype ", toks[1]
            if currRule in ebFundRules:
                #print "length",ebFundRules[currRule]["FMP"],len(ebFundRules[currRule]["FMP"])
                #print "ebAPI funding rule, FMP already in funding rules", currRule, ebFundRules[currRule], currFMP
                try:
                    ebFundRules[currRule]["FMP"].append(currFMP)
                    #print "*********************ebAPI funding rule, FMP already in funding rules", toks[1], ebFundRules[currRule]["FMP"]
                except:
                    print ("Failed to append currFMP")
            else:
                #ebFundRules[currRule] = {"Name":currFRdata["Name"],"FMP":[currFMP.encode("ASCII","ignore")]}
                ebFundRules[currRule] = {"Name":currFRdata["Name"],"FMP":[currFMP]}
                #print "new one", currRule,ebFundRules[currRule]["Name"],ebFundRules[currRule]["FMP"]
    #print (ebFundRules)
    return ebFundRules
#print(get_FundingRules())

def get_FundingRules2():
    # 201216 Adding FMP, using parsing of description
    # 201211 We used to use an EB report, Excel format, to get this info. We need dictionary
    # with speedtype as key and funding rule name as value

    #fundRules_data = get_fundingRules_allData()
    fundRules_data = getDataFromCache("FundingRules")
    i = len(fundRules_data)
    #print "Got it:", i
    ebFundRules = {}
    for j in range(0,i):
        #currFundRuleID = fundRules_data[j]["FundingRuleID"]
        #print "***",currFundRuleID
        currFRdata = {"Name":fundRules_data[j]["name"],"Description":fundRules_data[j]["description"],"CreateBy":fundRules_data[j]["createdBy"]}
        #print currFRdata
        #if "FMP" in currFRdata["Description"]:
            #print "FMP: ", currFRdata["Description"]
        if "-" in currFRdata["Name"]:
            toks = currFRdata["Name"].split("-")
            # watch out: some have spaces around the "-"
            #toks[0] = toks[0].strip()
            if toks[1][0] == " ":
                toks[1] = toks[1][1:]
            #print "Speedtype ", toks[1]
            ebFundRules[toks[1]] = currFRdata["Name"]
    #print (ebFundRules)
    return ebFundRules
#print(get_FundingRules2())

def get_FundingRules_FMP():
    fundRules_data = getDataFromCache("FundingRules")
    i = len(fundRules_data)
    ebFundRules = {}
    for j in range(0,i):
        #currFundRuleID = fundRules_data[j]["FundingRuleID"]
        currFRdata = {"Name":fundRules_data[j]["name"],"Description":fundRules_data[j]["description"],"CreateBy":fundRules_data[j]["createdBy"]}
        # print(currFRdata)
        if "-" in currFRdata["Name"]:
            toks = currFRdata["Name"].split("-")
            # print(toks)
            #toks[0] = toks[0].strip()
            if toks[1][0] == " ":
                currRule = str(toks[1][1:])
                print ("OK, rule", currRule)
            else:
                currRule = str(toks[1])
            # print(currRule)
            if "FMP" in currFRdata["Description"]:
                #print currFRdata["Description"]
                toks2 = currFRdata["Description"].split(" ")
                #currFMP = toks2[1].encode("ASCII","ignore")
                currFMP = str(toks2[1])
            else:
                currFMP = "XXXXXX"
            # print(currFMP)
            currName = currFRdata["Name"]
            if currFMP in ebFundRules:
                try:
                    ebFundRules[currFMP]["SpeedType"].append(currRule)
                    # print("*********************ebAPI funding rule, FR already in funding rules", toks[1], ebFundRules[currFMP]["SpeedType"])
                except:
                    print("Failed to append currRule")
                try:
                    # print(ebFundRules[currFMP]["Name"])
                    ebFundRules[currFMP]["Name"].append(currName)
                    # print("*********************ebAPI funding rule, FR already in funding rules", toks[1], ebFundRules[currFMP]["Name"])
                except:
                    print("Failed to append currName")
            else:
                # ebFundRules[currFMP] = {"SpeedType":currFRdata[currRule],"Name":currFRdata["Name"]}
                ebFundRules[currFMP] = {"SpeedType":[currRule], "Name":[currName]}
                # ebFundRules[currRule] = {"Name":currFRdata["Name"],"FMP":[currFMP]}
    # print(ebFundRules)
    return ebFundRules


# # Companies

def get_companies_data(record):
    cfg = get_config()

    company_id = record["companyId"]
    #theURL = "https://api2.e-builder.net/api/v2/companies/" + company_id + "/customfields"
    #response = requests.get(theURL, auth=BearerAuth(ebTok))

    theURL = cfg.api_url + "/api/v2/companies/" + company_id + "/customfields"
    response = get_request(theURL)

    #custom_fields_raw = json.loads(response.content)
    custom_fields_raw = json.loads(response)

    custom_fields_details = custom_fields_raw['details']
    dict_custom_fields_details = {}
    for j in range(len(custom_fields_details)):
        dict_custom_fields_details[custom_fields_details[j]['name']] = custom_fields_details[j]['value']
    company_data = record | dict_custom_fields_details
    return company_data

def get_companies_allData():
    records = APIconnect("companies")['records']
    company_all_data = []
    i = 0
    while i < len(records):
        record_batch = records[i:i+80]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_company = {executor.submit(get_companies_data, record): record for record in record_batch}
            for future in concurrent.futures.as_completed(future_to_company):
                company_data = future.result()
                company_all_data.append(company_data)
        i += 80
    return company_all_data

def get_Companies_dict():
    #company_data = get_companies_allData()
    company_data = getDataFromCache("Companies")
    i = len(company_data)

    ebCompanies = {}
    for j in range(0,i):
        try:
            ebCompanies["CompanyID"] = {"CompanyName":company_data[j]["companyName"],"CompanyNumber":company_data[j]["companyNumber"]}
        except:
            "Failed on: ", company_data[j]
    return ebCompanies
#print(get_Companies_dict())

def get_Companies_dict2():
    #company_data = get_companies_allData()
    company_data = getDataFromCache("Companies")
    i = len(company_data)

    ebCompanies = {}
    for j in range(0,i):
        #print j, company_data[j]["CompanyName"], company_data[j]["CompanyNumber"]
        currNumber = str(company_data[j]["companyNumber"]).rstrip()
        #print currNumber[0], currNumber[len(currNumber)-1], currNumber
        try:
            ebCompanies[currNumber] = str(company_data[j]["companyName"]).rstrip()
        except:
            "Failed on: ", company_data[j]
    return ebCompanies

## Funding Sources

def get_fundingSources_data(record):
    cfg = get_config()

    fundingSource_id = record["fundingSourceID"]

    #theURL = "https://api2.e-builder.net/api/v2/fundingSources/" + fundingSource_id + "/customfields"
    #response = requests.get(theURL, auth=BearerAuth(ebTok))

    theURL = cfg.api_url + "/api/v2/fundingSources/" + fundingSource_id + "/customfields"
    response = get_request(theURL)

    #custom_fields_raw = json.loads(response.content)
    custom_fields_raw = json.loads(response)

    custom_fields_details = custom_fields_raw['details']
    dict_custom_fields_details = {}
    for j in range(len(custom_fields_details)):
        dict_custom_fields_details[custom_fields_details[j]['name']] = custom_fields_details[j]['value']
    fundingSource_data = record | dict_custom_fields_details
    return fundingSource_data

def get_fundingSources_allData():
    records = APIconnect("fundingSources")['records']
    fundingSource_all_data = []
    i = 0
    while i < len(records):
        record_batch = records[i:i+80]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_fundingSource = {executor.submit(get_fundingSources_data, record): record for record in record_batch}
            for future in concurrent.futures.as_completed(future_to_fundingSource):
                fundingSource_data = future.result()
                fundingSource_all_data.append(fundingSource_data)
        i += 80
    return fundingSource_all_data

## PO Requisitions

def getPOREQDataNonCostProcess():
    POREQdatafields = {
        "selectedFields": [
            "Project/ProjectName",
            "Process/Prefix",
            "ProcessInstance/CurrentStepName",
            "ProcessInstance/PortalId",
            "ProcessInstance/Subject",
            "ProcessInstance/InstanceCounter",
            "ProcessInstance/DataFields/Description",
            "ProcessInstance/DataFields/Blanket Order",
            "ProcessInstance/CurrentStepName",
            "ProcessInstance/DataFields/username",
            "ProcessInstance/DataFields/Shipping Address",
            "ProcessInstance/DataFields/Attention",
            "ProcessInstance/DataFields/Address Line",
            "ProcessInstance/DataFields/City",
            "ProcessInstance/DataFields/State",
            "ProcessInstance/DataFields/Zip Code",
            "ProcessInstance/DataFields/Room Floor Suite",
            "ProcessInstance/DataFields/External Comments"

        ],
        "Filters": [
            {
                "Field": "ProcessInstance/CurrentStepName",
                "Operation": "=",
                "Value": "Python Hold: Send to BW"
            },
        ],
    }
    #theURL = 'https://api2.e-builder.net/api/v2/noncostprocesses/query?processprefix=POREQ'
    cfg =  get_config()
    theURL = cfg.api_url + "/api/v2/noncostprocesses/query?processprefix=POREQ"

    print('Getting POREQ data')
    POREQjson = postTOAPI(theURL, POREQdatafields)['records']
    return POREQjson

def getPOREQData():
    POREQdatafields = {"selectedFields": [
            "Project/ProjectName",
            "Process/Prefix",
            "ProcessInstance/CurrentStepName",
            "ProcessInstance/PortalId",
            "ProcessInstance/Subject",
            "ProcessInstance/InstanceCounter",
            "ProcessInstance/DataFields/Description",
            "ProcessInstance/DataFields/Blanket Order",
            "ProcessInstance/CurrentStepName",
            "ProcessInstance/DataFields/username",
            "ProcessInstance/DataFields/Shipping Address",
            "ProcessInstance/DataFields/Attention",
            "ProcessInstance/DataFields/Address Line",
            "ProcessInstance/DataFields/City",
            "ProcessInstance/DataFields/State",
            "ProcessInstance/DataFields/Zip Code",
            "ProcessInstance/DataFields/Room Floor Suite",
            "ProcessInstance/DataFields/External Comments",
            "CommitmentType/CommitmentType",
            "Company/CompanyId",
            "LineItems/CommitmentItem/UnitCost",
            "LineItems/CommitmentItem/Amount",
            "LineItems/CommitmentItem/Quantity",
            "LineItems/CommitmentItem/FundingRuleId",
            "LineItems/CommitmentItem/ItemNumber"
        ],
        "Filters":[
            {
                "Field" : "ProcessInstance/CurrentStepName",
                "Operation" : "=",
                "Value" : "Python Hold: Send to BW"
                }
               ]
    }
    #theURL = 'https://api2.e-builder.net/api/v2/CommitmentProcesses/query?processprefix=POREQ'
    cfg =  get_config()
    theURL = cfg.api_url + "/api/v2/CommitmentProcesses/query?processprefix=POREQ"
    print('Getting POREQ data')
    POREQjson = postTOAPI(theURL, POREQdatafields)['records']
    return POREQjson


## Getting Data from JSON files in local cache

def getDataFromCache(module):
    # print("Getting ",module," data from Cache to reduce load on API. Run the commented lines instead to get fresh data")
    #dir = '/Users/kysgattu/FIS/ebData/'
    dir = "B:\\ebData\\"
    file = dir + module + '.json'
    with open(file, 'r') as f:
        module_data = json.loads(f.read())
    return module_data

#fundingRules_data = getDataFromCache('FundingRules')
#print(fundingRules_data) # Print data of all fundingRules as a list of dictionaries
#print(fundingRules_data[1]) # Print data of first fundingRule as a dictionary




#print(get_Companies_dict2())

#get_ipython().system('jupyter nbconvert --to script ebAPI_lib.ipynb')