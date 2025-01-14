import tkinter as tk
from tkinter import *
from tkinter import messagebox as mb
from tkinter import filedialog as filedialog
from tkinter import Tk, Label, Button
from tkinter import ttk
import uml_python.uml_lib.ebAPI_lib as eb
import uml_python.moStat as moStat
import uml_python.ebTimeAlloc as timeAlloc
import uml_python.ebFMP as ebFMP
import uml_python.bw2eb.bw2eb as bw2eb
import uml_python.bw2eb.bw2ebXML as bw2ebXML
import uml_python.bw2eb.bw2ebJoined as bw2ebJoined
import uml_python.bw2eb.bw2ebXMLJoined as bw2ebXMLJoined
import uml_python.uml_lib.dailyDataImport as ebData

import os
import datetime

ydPad = 1
xdPad = 10
fypad = ydPad
dWidth = 70
eWidth = 20
CSVfile = ""
timeAllocCSV = ""

# fundRules = eb.get_FundingRules()
# ebProjs = eb.get_Projects()
# activePOs = eb.get_activePOs(ebProjs)
#
# vendorTypes = {}
# eb.build_commitTypes(activePOs)

import os
import glob
import datetime

def get_latest_modified_time(directory_path, extension='.json'):
    json_files = glob.glob(os.path.join(directory_path, f'*{extension}'))

    if not json_files:
        print(f"No {extension} files found in the directory.")
        return None

    latest_modified_time = None

    for json_file in json_files:
        modification_time = os.path.getmtime(json_file)
        modified_date = datetime.datetime.fromtimestamp(modification_time)

        # print(f"{json_file} was last modified on: {modified_date}")

        if latest_modified_time is None or modification_time > latest_modified_time:
            latest_modified_time = modification_time

    latest_modified_date = datetime.datetime.fromtimestamp(latest_modified_time)
    # print(f"\nThe latest modification time is: {latest_modified_date}")
    return latest_modified_date.strftime("%Y-%b-%d %H:%M:%S")

def run_bw2eb():
    global supportFile, CSVfile
    # clear results, in case we already ran
    lblResults.config(text="Results\nRunning Buyways to e-Builder")
    if CSVfile == "":
        mb.showwarning(title=None, message="No CSV file selected: can't run bw2eb")
    else:
        res = bw2eb.main(CSVfile)
        print(res)
        if type(res) == dict:
            lblResults.config(text=("Complete. Excel files are saved in: " + res['ImportFile']))
        else:
            lblResults.config(text=("Complete. Excel files are saved in: " + res))

def run_monthStat():
    res = moStat.main()
    resStr = "Monthly Status Complete for: " + res["Month"]
    resStr += "\nProjects for report: " + str(res["ProjCount"]) + "\n"
    resStr += "No Updates: " + str(res["No Updates"]) + ". Not Active or TDactive: " + str(res["Not Active"])
    resStr += ". JSON Length: " + str(res["obj length"]) + " - " + str(res["ProjCount"]+res["No Updates"]+res["Not Active"]) + "\n"
    resStr += "Saved to: " + res["ofile"]
    lbl_moStatResults.config(text=resStr)

def run_timeAlloc():
    if timeAllocCSV == "":
        mb.showwarning(title=None, message="No Report CSV file selected: can't run timeAlloc")
    else:
        res = timeAlloc.main(timeAllocCSV)
        lbl_timeAllocResults.config(text="Complete. XLSX Files saved in " + res)

def run_ebFMP():
    res = ebFMP.main()
    lbl_ebFMPresults.config(text="Complete. HTMl file in "+ res)

def run_ebData():
    res = ebData.main()
    lbl_ebDataresults.config(text=res+"\nEB Data last Imported on:" + get_latest_modified_time("/Users/kysgattu/FIS/ebData/"))

def run_bw2ebJoined():
    res = bw2ebJoined.main()
    # print(res)
    # print(type(res["POImport"]))
    resStr = "Complete. BW Reports extracted and imported" + "\n"
    for i in res:
        resStr += str(i) + "\n"
    # resStr += "PO Import Report saved at: " + str(res["POImport"]) + "\n"
    # resStr += "Invoice Import Report saved at: " + str(res["InvoiceImport"]) + "\n"
    # resStr += "PO Import Totals saved at: " + str(res["POTotals"]) + "\n"
    # resStr += "Invoice Import Totals saved at: " + str(res["InvoiceTotals"])
    lbl_bwebJoinedresults.config(text=resStr)

def run_bw2ebXML():
    res = bw2ebXML.main()
    resStr = "Complete. BW Reports extracted and imported" + "\n"
    resStr += "PO Import Report saved at: " + str(res["POReport"]) + "\n"
    resStr += "Invoice Import Report saved at: " + str(res["InvoiceReport"]) + "\n"
    resStr += "PAYAP Invoice Import Report saved at: " + str(res["PAYAPInvoiceReport"]) + "\n"
    resStr += "PO Import Totals saved at: " + str(res["POStats"]) + "\n"
    resStr += "Invoice Import Totals saved at: " + str(res["InvoiceStats"])
    lbl_bwebXMLresults.config(text=resStr)

def run_bw2ebXMLJoined():
    res = bw2ebXMLJoined.main()
    resStr = "Complete. BW Reports extracted and imported" + "\n"
    resStr += "PO Import Report saved at: " + str(res["POReport"]) + "\n"
    resStr += "Invoice Import Report saved at: " + str(res["InvoiceReport"]) + "\n"
    resStr += "PAYAP Invoice Import Report saved at: " + str(res["PAYAPInvoiceReport"]) + "\n"
    lbl_bwebXMLresultsJoined.config(text=resStr)

def browseCSV():
    global CSVfile
    filename = filedialog.askopenfilename(initialdir="/", title="Select a File", filetypes=(("Text files", "*.csv*"), ("all files", "*.*")))
    # Change label contents
    csv_File = filename.split('/')[-1]
    label_csv.configure(text="File Opened: "+csv_File)
    CSVfile = filename
    # print(filename.split('/')[-1])

def browseTAcsv():
    global timeAllocCSV
    filename = filedialog.askopenfilename(initialdir="/", title="Select a File", filetypes=(("Text files", "*.csv*"), ("all files", "*.*")))
    csv_File = filename.split('/')[-1]
    label_TAcsv.configure(text="File Opened: "+csv_File)
    timeAllocCSV = filename

def run_eb2bw():
    # res = eb2bw.main()
    # print (res)
    # successStr = str(res[0]) + " sent successfully\n"
    # failedStr = str(res[1]) + " failed\n"
    # dupStr = str(res[2]) + " not sent, sent previously"
    # statusStr = "Complete.\nLogs in C:\\temp\\POREQ\\_eb2bw\n"+ successStr + failedStr + dupStr
    lbl_eb2bw_results.config(text="WARNING:Under Development for New API")

def on_mousewheel(event):
    canvas.yview_scroll(-int(event.delta/120), "units")
    # canvas.xview_scroll(-int(event.delta / 120), "units")

main_window = tk.Tk()
main_window.title("EB Python Dashboard")
main_window.geometry('1260x900')
# hsb = ttk.Scrollbar(window, orient='horizontal')

# Create a canvas with scrollbars
canvas = tk.Canvas(main_window)
canvas.pack(fill=tk.X, expand=True)

# Bind mousewheel event to canvas
canvas.bind_all("<MouseWheel>", on_mousewheel)

# Create a vertical scrollbar and attach it to the canvas
vscrollbar = Scrollbar(main_window, command=canvas.yview)
vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.configure(yscrollcommand=vscrollbar.set)



title = ttk.Label(canvas, text="UMass Lowell Facilities EB Dashboard", style='Head.TLabel')
# title.grid(column=1, row=0, padx=xdPad, pady=ydPad, sticky=tk.W)
title.pack()

# Create a frame to hold all the elements
window = ttk.Frame(canvas)
window.pack()

style = ttk.Style()
style.configure('Head.TLabel', font=('Arial', 22, 'bold', 'underline'), foreground = 'black', align ='center')
style.configure('Warning.TLabel', font=('Arial', 9, 'italic', ), foreground = 'red', align ='left')
style.configure('TButton', font=('Arial', 10, 'bold'), width=dWidth)
style.configure('TLabel', font=('Arial', 9), foreground = 'blue', )
style.configure('TLabelframe.Label', font=('Consolas', 14, 'bold', 'underline'), foreground = 'black', justify='center')
style.configure('Centered.TLabelframe.Label', font=('Consolas', 16, 'bold', 'underline'), foreground='black', justify='center')


# Add empty space after the title
empty_space = ttk.Label(window, text="", width=dWidth)
empty_space.grid(column=1, row=1)  # Adjust the row number as needed

empty_space = ttk.Label(window, text="", width=dWidth)
empty_space.grid(column=1, row=2)  # Adjust the row number as needed


left_frame = ttk.LabelFrame(window,text="Timely Imports",)
left_frame.grid(column=1, row=3, padx=xdPad, pady=fypad*5, sticky=tk.W)

# E-Builder Data Import
frame_ebData = ttk.LabelFrame(left_frame,text="E-Builder JSON Data Import",)
frame_ebData.grid(column=1, row=4, padx=xdPad, pady=fypad*5, sticky=tk.W)

btn_ebData = ttk.Button(frame_ebData, text="Run ebData", command=run_ebData, width=dWidth)
btn_ebData.grid(column=1, row=5, padx=xdPad, pady=ydPad, sticky=tk.W)

lbl_ebDataresults = ttk.Label(frame_ebData, text="EB Data last Imported on:" + get_latest_modified_time("/Users/kysgattu/FIS/ebData/") + "\neb Data Results:\n...\n...\n...\n...\n...\n...", anchor="w")
lbl_ebDataresults.grid(column=1, row=6, padx=xdPad, pady=(2 * ydPad), sticky=tk.W)


# Time Allocation
frame_timeAlloc = ttk.LabelFrame(left_frame, text="Time Alocation Reports")
frame_timeAlloc.grid(column=1, row=7, padx=xdPad, pady=fypad, sticky=tk.W)

btn_TAcsv = ttk.Button(frame_timeAlloc, text="Browse for Speedtype, PS Project Report CSV", command=browseTAcsv, width=dWidth)
btn_TAcsv.grid(column=1, row=8, padx=xdPad, pady=ydPad, sticky=tk.W)

label_TAcsv = ttk.Label(frame_timeAlloc, text="No file selected")
label_TAcsv.grid(column=1, row=9, padx=xdPad, sticky=tk.W)

btn_timeAlloc = ttk.Button(frame_timeAlloc, text="Run timeAlloc", command=run_timeAlloc, width=dWidth)
btn_timeAlloc.grid(column=1, row=10, padx=xdPad, pady=ydPad, sticky=tk.W)

lbl_timeAllocResults = ttk.Label(frame_timeAlloc, text="Time Allocation Results:\n...", anchor="w")
lbl_timeAllocResults.grid(column=1, row=11, padx=xdPad, pady=(2 * ydPad), sticky=tk.W)

# ebFMP
frame_FMP = ttk.LabelFrame(left_frame, text="FMP Reports")
frame_FMP.grid(column=1, row=12, padx=xdPad, pady=fypad, sticky=tk.W)

btn_ebFMP = ttk.Button(frame_FMP, text="Run ebFMP", command=run_ebFMP, width=dWidth)
btn_ebFMP.grid(column=1, row=13, padx=xdPad, pady=ydPad, sticky=tk.W)

lbl_ebFMPresults = ttk.Label(frame_FMP, text="eb FMP Results:\n...", anchor="w")
lbl_ebFMPresults.grid(column=1, row=14, padx=xdPad, pady=(2 * ydPad), sticky=tk.W)

# Monthly Status
frame_moStat = ttk.LabelFrame(left_frame, text="Monthly Status Reports")
frame_moStat.grid(column=1, row=15, padx=xdPad, pady=fypad, sticky=tk.W)

btn_monthStat = ttk.Button(frame_moStat, text="Run for Monthly Status", command=run_monthStat, width=dWidth)
btn_monthStat.grid(column=1, row=16, padx=xdPad, pady=ydPad, sticky=tk.W)

lbl_moStatResults = ttk.Label(frame_moStat, text="Monthly Status Report:\n...", anchor="w")
lbl_moStatResults.grid(column=1, row=17, padx=xdPad, pady=(2 * ydPad), sticky=tk.W)


right_frame = ttk.LabelFrame(window,text="E-Builder <=====> Buyways",)
right_frame.grid(column=2, row=3, padx=xdPad, pady=fypad*5, sticky=tk.W)


# Buyways to E-Builder Import
frame_bw2eb = ttk.LabelFrame(right_frame,text="Buyways to E-Builder Import",)
frame_bw2eb.grid(column=2, row=4, padx=xdPad, pady=fypad*5, sticky=tk.W)

btn_csv = ttk.Button(frame_bw2eb, text="Browse Buyways CSV input file", command=browseCSV, width=dWidth)
btn_csv.grid(column=2, row=5, padx=xdPad, pady=ydPad, sticky=tk.W)

label_csv = ttk.Label(frame_bw2eb, text="No file selected")
label_csv.grid(column=2, row=6, padx=xdPad, pady=ydPad, sticky=tk.W)

btn_run = ttk.Button(frame_bw2eb, text="Run bw2eb", command=run_bw2eb, width=dWidth)
btn_run.grid(column=2, row=7, padx=xdPad, pady=ydPad, sticky=tk.W)

lblResults = ttk.Label(frame_bw2eb, text="Buyways File import Results:\n...", anchor="w")
lblResults.grid(column=2, row=8, padx=xdPad, pady=(2 * ydPad), sticky=tk.W)

btn_bwebJoined = ttk.Button(frame_bw2eb, text="Run bwebJoined", command=run_bw2ebJoined, width=dWidth)
btn_bwebJoined.grid(column=2, row=9, padx=xdPad, pady=ydPad, sticky=tk.W)

lbl_bwebJoinedresults = ttk.Label(frame_bw2eb, text="Buways Files Import Results:\n...\n...\n...", anchor="w")
lbl_bwebJoinedresults.grid(column=2, row=10, padx=xdPad, pady=(2 * ydPad), sticky=tk.W)

btn_bwebXML = ttk.Button(frame_bw2eb, text="Run bweb XML", command=run_bw2ebXML, width=dWidth)
btn_bwebXML.grid(column=2, row=11, padx=xdPad, pady=ydPad, sticky=tk.W)

lbl_bwebXMLresults = ttk.Label(frame_bw2eb, text="Buways Files Import Results:\n...\n...\n...", anchor="w")
lbl_bwebXMLresults.grid(column=2, row=12, padx=xdPad, pady=(2 * ydPad), sticky=tk.W)

btn_bwebXMLJoined = ttk.Button(frame_bw2eb, text="Join bweb XML Reports", command=run_bw2ebXMLJoined, width=dWidth)
btn_bwebXMLJoined.grid(column=2, row=13, padx=xdPad, pady=ydPad, sticky=tk.W)

lbl_bwebXMLresultsJoined = ttk.Label(frame_bw2eb, text="Buways Files Import Results:\n...\n...\n...", anchor="w")
lbl_bwebXMLresultsJoined.grid(column=2, row=14, padx=xdPad, pady=(2 * ydPad), sticky=tk.W)


# eb2bw POREQ
frame_eb2bw = ttk.LabelFrame(right_frame, text="E-Builder to Buyways")
frame_eb2bw.grid(column=2, row=15, padx=xdPad, pady=fypad, sticky=tk.W)

btn_eb2bw = ttk.Button(frame_eb2bw, text="Run eb2bw",command=run_eb2bw,width=dWidth)
btn_eb2bw.grid(column=2,row=16, padx=xdPad, pady=ydPad,sticky=W)
lbl_eb2bw_results = ttk.Label(frame_eb2bw, text="eb2bw Results:\n...\n...\n...", anchor="w")
lbl_eb2bw_results.grid(column=2,row=17,padx=xdPad, pady=(2*ydPad),sticky=W)
warning = ttk.Label(frame_eb2bw, text="WARNING!!! eb2bw Not completely developed in New API", style='Warning.TLabel')
warning.grid(column=2, row=18, padx=xdPad, pady=ydPad, sticky=tk.W)

# Exit Button
btn_exit = ttk.Button(window, text="Exit", width=eWidth, command=exit)
btn_exit.grid(column=1, row=33, padx=xdPad, pady=xdPad, sticky=tk.W)


sizegrip = ttk.Sizegrip(window)
# sizegrip.grid(column=)

main_window.mainloop()
