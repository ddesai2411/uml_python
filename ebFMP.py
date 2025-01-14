#!/usr/bin/python

import uml_python.uml_lib.ebAPI_lib as eb
from datetime import datetime

def main():
    projs = eb.getDataFromCache("Projects")
    # project_data = ebAPI.getDataFromCache("ActiveProjects")
    print("Projects Data Imported")
    keys = list(projs[1].keys())
    i = len(projs)

    hStr = "h5"
    strOnS = "<" + hStr + ">"
    strPlanning = strOnS
    strPM = strOnS
    inActOnS = "<" + hStr + ">"
    inActPlanning = strOnS
    inActPM = strOnS
    completeOnS = "<" + hStr + ">"
    completePlanning = strOnS
    completePM = strOnS

    theFields = ["Campus","Building","Planned Occupant","FM Department Lead","Project Planner","Project Manager"]
    n = 0

    for j in range(0,i):
        # Need to check if there's data
        currRow = [projs[j]["FMP Number"]]
        currName = projs[j]["name"]
        currLead = projs[j]["FM Department Lead"]
        #print ">>>>",currLead, projs[j]["Status"]
        # This is where we filter for Status.
        # 200923 Adding new strings for Inactive
        if (projs[j]["status"] == "Active") or (projs[j]["status"] == "TD Active"):
            if currLead == "O&S":
                strOnS += projs[j]["FMP Number"] + ","
            if currLead == "Planning":
                strPlanning += projs[j]["FMP Number"] + ","
            if currLead == "Project Management":
                strPM += projs[j]["FMP Number"] + ","
            # strip last comma, replace with new line
        elif (projs[j]["status"] == "Inactive"):
            if currLead == "O&S":
                inActOnS += projs[j]["FMP Number"] + ","
            if currLead == "Planning":
                inActPlanning += projs[j]["FMP Number"] + ","
            if currLead == "Project Management":
                inActPM += projs[j]["FMP Number"] + ","
            # strip last comma, replace with new line
        elif (projs[j]["status"] == "Complete"):
            if currLead == "O&S":
                completeOnS += projs[j]["FMP Number"] + ","
            if currLead == "Planning":
                completePlanning += projs[j]["FMP Number"] + ","
            if currLead == "Project Management":
                completePM += projs[j]["FMP Number"] + ","
            # strip last comma, replace with new line

    strOnS += ("</" + hStr + ">")
    strPlanning += ("</" + hStr + ">")
    strPM += ("</" + hStr + ">")

    # get date and time to stamp file
    now = datetime.now()
    # print now.year, now.month, now.day, now.hour, now.minute, now.second
    tstamp = str(now.year) + str(now.month) + str(now.day) + "_"
    tstamp += str(now.hour) + str(now.minute) + str(now.second)

    # ofile = open("/Users/kysgattu/Desktop/ebFMP.html","w")
    # filebase = "C:\\Users\\K_Gattu\\PycharmProjects\\uml_python\\uml\\outputfiles\\ebFMP.html"
    # filebase = "C:\\inetpub\\wwwroot\\ebProj\\ebFMP.html"
    # filebase = "C:\\FISPython\\ebFMP.html"
    filebase = "/Users/kysgattu/FIS/BDrive/ebFMP.html"
    ofile = open(filebase,"w")
    ofile.write("<html><head>\n<style>h5{color: blue;font-family: verdana;font-size: 70%}\n")
    ofile.write("h4{color: red;font-family: verdana;font-size: 80%}</style><body>\n")
    ofile.write("<" + hStr + ">Last updated:" + tstamp + "</" + hStr + ">\n")
    ofile.write("<h4>ACTIVE AND TD ACTIVE PROJECTS</" + hStr + ">\n")
    ofile.write("<" + hStr + ">PM</" + hStr + ">\n")
    ofile.write(strPM)
    ofile.write("<" + hStr + ">Planning</" + hStr + ">\n")
    ofile.write(strPlanning)
    ofile.write("<" + hStr + ">O&S</" + hStr + ">\n")
    ofile.write(strOnS)
    ofile.write("<h4>INACTIVE PROJECTS</" + hStr + ">\n")
    ofile.write("<" + hStr + ">PM</" + hStr + ">\n")
    ofile.write(inActPM)
    ofile.write("<" + hStr + ">Planning</" + hStr + ">\n")
    ofile.write(inActPlanning)
    ofile.write("<" + hStr + ">O&S</" + hStr + ">\n")
    ofile.write(inActOnS)
    ofile.write("<h4>COMPLETE PROJECTS</" + hStr + ">\n")
    ofile.write("<" + hStr + ">PM</" + hStr + ">\n")
    ofile.write(completePM)
    ofile.write("<" + hStr + ">Planning</" + hStr + ">\n")
    ofile.write(completePlanning)
    ofile.write("<" + hStr + ">O&S</" + hStr + ">\n")
    ofile.write(completeOnS)
    ofile.write("</body></html>\n")
    ofile.close()
    return filebase

if __name__ == "__main__":
    main()
