"""
9/3/2021: added FMlead for filtering POs (not importing O&S)
"""
#import uml_new.eb.ebAPI_lib as ebAPI
import uml_V2.uml_lib.ebAPI_lib as ebAPI
#import ebCOST_newAPI.eb.ebAPI_lib as ebAPI

def debugPrint(theStr):
    print("Debug print:", theStr)
    ignoreThis = 0

def padstr2(s, l):
    retVal = s
    if len(s) < l:
        for i in range(0,l-len(s)):
            retVal = "0" + retVal
    return retVal


#def write_PO_Cost_line(POrow,ebCompanies,fundRule, multST, budgTasks, ws, samePO, FMlead):
def write_PO_Cost_line(POrow):
    print("::::::HELL O")
    

