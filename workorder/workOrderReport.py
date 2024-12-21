#!/usr/bin/env python
# coding: utf-8

import csv
import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import warnings
warnings.filterwarnings("ignore") #removes warnings like version deprecation etc.,

def getEmailAddrsFromName(name):
    domain = "uml.edu"
    email = name.lower().replace(" ", "_") + "@" + domain
    email = "kamalyeshodharshastry_gattu@uml.edu" # Comment this line when a way to find email address from name is figured out
    return email

def sendEmail(recipient,requestId,requestStatus,message):
    # Set up the SMTP server and login credentials
    smtp_server = 'smtp.office365.com'
    smtp_port = 587
    # Enter Credentials of Sender Mail Client
    smtp_username = ''
    smtp_password = ''
    smtp_sender = ''

    # Set up the email message
    email_subject = 'Your Work Order Request '+ str(requestId) + ' ' + str(requestStatus)
    email_body = message
    email_recipients = recipient

    # Define EMail
    msg = MIMEMultipart()
    msg['From'] = smtp_sender
    msg['To'] = email_recipients
    msg['Subject'] = email_subject
    msg.attach(MIMEText(email_body, 'html'))
    #msg.attach(MIMEText(email_body, 'text'))

    # Send the email
    try:
        smtp_conn = smtplib.SMTP(smtp_server, smtp_port)
        smtp_conn.starttls()
        smtp_conn.login(smtp_username, smtp_password)
        smtp_conn.sendmail(smtp_sender, email_recipients, msg.as_string())
        smtp_conn.quit()
        #print("Email sent successfully! \n" + email_subject + '\n')
    except Exception as e:
        print("Error: ", e)

def recievedResponse(req_id, req_desc):
    html_content = """
    <html>
    <body>
    <h2>Work Order Request - {0}</h2>
    <p>Thanks for using UMass Lowell Facilities Management’s Workorder Request system. Your workorder request, summarized below, has been received. We will email again when it has been assigned and/or completed. If you have questions or comments, please email <a href="mailto:facilities@uml.edu">facilities@uml.edu</a>.</p>
    <p><b>Request ID:</b> {0}</p>
    <p><b>Request Description:</b> {1}</p>
    </body>
    </html>
    """.format(req_id, req_desc)
    return html_content

def assignedNoUpdateResponse(req_id, req_desc):
    html_content = """
    <html>
    <body>
    <h2>Work Order Request - {0}</h2>
    <p>Thanks for using UMass Lowell Facilities Management’s Workorder Request system. Your workorder request, summarized below, has been assigned. We will email again when it has been received and/or completed. If you have questions or comments, please email <a href="mailto:facilities@uml.edu">facilities@uml.edu</a>.</p>
    <p><b>Request ID:</b> {0}</p>
    <p><b>Request Description:</b> {1}</p>
    </body>
    </html>
    """.format(req_id, req_desc)
    return html_content

def assignedUpdateResponse(req_id, req_desc, update_notes):
    html_content = """
    <html>
    <body>
    <h2>Work Order Request - {0}</h2>
    <p>Thanks for using UMass Lowell Facilities Management’s Workorder Request system. Your workorder request, summarized below, has been assigned. We will email again when it has been received and/or completed. If you have questions or comments, please email <a href="mailto:facilities@uml.edu">facilities@uml.edu</a>.</p>
    <p><b>Request ID:</b> {0}</p>
    <p><b>Request Description:</b> {1}</p>
    <p><b>Update Notes:</b> {2}</p>
    <p></p>
    </body>
    </html>
    """.format(req_id, req_desc,update_notes)
    return html_content

def completedResponse(req_id, req_desc):
    html_content = """
    <html>
    <body>
    <h2>Work Order Request - {0}</h2>
    <p>Thanks for using UMass Lowell Facilities Management’s Workorder Request system. If you have questions or comments, please email <a href="mailto:facilities@uml.edu">facilities@uml.edu</a>.</p>
    <p><b>Request ID:</b> {0}</p>
    <p><b>Request Description:</b> {1}</p>

    <p>Also, please complete this 1 question survey:</p>
    <p>How satisfied were you with this workorder experience?</p>
    <form action="">
        <input type="radio" id="very-satisfied" name="satisfaction" value="very-satisfied">
        <label for="very-satisfied">Very Satisfied</label><br>
        <input type="radio" id="satisfied" name="satisfaction" value="satisfied">
        <label for="satisfied">Satisfied</label><br>
        <input type="radio" id="not-satisfied" name="satisfaction" value="not-satisfied">
        <label for="not-satisfied">Not Satisfied</label><br>
        <p>Comments:</p>
        <textarea name="comments" rows="4" cols="50"></textarea>
        <br>
        <input type="submit" value="Submit">
    </form>
    </body>
    </html>
    """.format(req_id, req_desc)
    return html_content


# *EMail with text body intead of html*
# def recievedResponse(req_id,req_desc):
#     recieved_response = "Thanks for using UMass Lowell Facilities Management’s Workorder Request system. Your workorder request, summarized below, has been received. We will email again when it has been assigned and/or completed. If you have questions or comments, please email <facilities@uml.edu>. \n"
#     response_string = recieved_response + 'Request ID: ' + str(req_id) + '\n' + 'Request Description: ' +str(req_desc) + '\n'
#     return response_string
# 
# def assignedNoUpdateResponse(req_id, req_desc):
#     assigned_response = "Thanks for using UMass Lowell Facilities Management’s Workorder Request system. Your workorder request, summarized below, has been assigned. We will email again when it has been received and/or completed. If you have questions or comments, please email <facilities@uml.edu>. \n"
#     response_string = assigned_response + 'Request ID: ' + str(req_id) + '\n' + 'Request Description: ' +str(req_desc) + '\n'
#     return response_string
# 
# def assignedUpdateResponse(req_id, req_desc, update_notes):
#     assigned_response = "Thanks for using UMass Lowell Facilities Management’s Workorder Request system. Your workorder request, summarized below, has been assigned. We will email again when it has been received and/or completed. If you have questions or comments, please email <facilities@uml.edu>. \n"
#     response_string = assigned_response + 'Update Notes: ' + str(update_notes) + '\n' + 'Request ID: ' + str(req_id) + '\n' + 'Request Description: ' +str(req_desc) + '\n'
#     return response_string
# 
# def completedResponse(req_id,req_desc):
#     completed_response = "Thanks for using UMass Lowell Facilities Management’s Workorder Request system. If you have questions or comments, please email <facilities@uml.edu>. \nAlso, please complete this 1 questions survey: \nHow satisfied were you with this workorder experience: \nVery Satisfied \nSatisfied \nNot Satisfied \nComments: \n"
#     response_string = completed_response + 'Request ID: ' + str(req_id) + '\n' + 'Request Description: ' +str(req_desc) + '\n'
#     return response_string

# # Create a Master Work Order Reports directory that store all the Work Orders

master_report = 'Master_Work_Orders_Directory.csv'
columns = ['Request Id', 'Description', 'Assignment Status','Requested For', 'Resource Name', 'Update Notes']
if not os.path.exists(master_report):
    with open(master_report, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
master_report_df = pd.read_csv(master_report)
print("Master Report:")
print(master_report_df[['Request Id', 'Assignment Status']])
master_report_df['Request Id'] = master_report_df['Request Id'].astype(str)

master_requestids = master_report_df['Request Id'].to_list()
master_descriptions = master_report_df['Description'].to_list()
master_assignment_status = master_report_df['Assignment Status'].to_list()
master_service_requested = master_report_df['Requested For'].to_list()
master_resource_names = master_report_df['Resource Name'].to_list()
master_update_notes = master_report_df['Update Notes'].to_list()

# # 1st Test File - Posing to be first day report

#daily_report = 'workorder/testReports/TEST1 Open WO - Projects.xlsx'
daily_report = 'workorder/testReports/TEST2 Open WO - Projects.xlsx'
current_report_df = pd.read_excel(daily_report)
current_report_df = current_report_df.dropna(subset=['Request Id'])
current_report_df = current_report_df.loc[:,['Request Id', 'Description', 'Assignment Status', 'Requested For', 'Resource Name', 'Update Notes']]
for i in range(len(current_report_df['Request Id'])):
    current_report_df['Request Id'][i] = str(int(current_report_df['Request Id'][i]))
print('Current Report')
print(current_report_df[['Request Id', 'Assignment Status']])

#print(master_report_df['Request Id'])
for i, row in current_report_df.iterrows():
    print('Request Id: ' + str(row['Request Id']))
    #print(row['Request Id'])
    #print(master_report_df['Request Id'])
    if not master_report_df['Request Id'].eq(row['Request Id']).any():
        #print('here')
        #master_report_df = master_report_df.append(row)
        #print(row['Request Id'])
        curr_req_id = row['Request Id']
        curr_req_desc = row['Description']
        curr_req_status = row['Assignment Status']
        curr_requested_for = row['Requested For']
        #recipient = getEmailAddrsFromName(curr_requested_for)
        recipient = 'kamalyeshodharshastry_gattu@uml.edu' # Comment this line when a way to find email address from name is figured out
        if curr_req_status == 'Received':
            message = recievedResponse(curr_req_id,curr_req_desc)
            sendEmail(recipient, curr_req_id,curr_req_status,message)
        elif curr_req_status == 'Assigned':
            message = assignedNoUpdateResponse(curr_req_id,curr_req_desc)
            sendEmail(recipient, curr_req_id,curr_req_status,message)
        elif curr_req_status == 'Completed':
            message = completedResponse(curr_req_id,curr_req_desc)
            sendEmail(recipient, curr_req_id,curr_req_status,message)
        # print(response_string)
    else:
        row_in_master = master_report_df.loc[master_report_df['Request Id'] == row['Request Id']]
        curr_req_id = row['Request Id']
        curr_req_desc = row['Description']
        curr_update_notes = row['Update Notes']
        curr_req_status = row['Assignment Status']
        curr_requested_for = row['Requested For']
        #recipient = getEmailAddrsFromName(curr_requested_for)
        recipient = 'kamalyeshodharshastry_gattu@uml.edu' # Comment this line when a way to find email address from name is figured out
        #print(curr_req_status)
        if curr_req_status == 'Received':
            message = recievedResponse(curr_req_id,curr_req_desc)
            sendEmail(recipient, curr_req_id,curr_req_status,message)
        elif curr_req_status == 'Completed':
            message = completedResponse(curr_req_id,curr_req_desc)
            sendEmail(recipient, curr_req_id,curr_req_status,message)
        else:
            if pd.isna(row['Update Notes']):
                message = assignedNoUpdateResponse(curr_req_id,curr_req_desc)
                sendEmail(recipient, curr_req_id,curr_req_status,message)

            else:
                #print(row['Update Notes'])
                #print(row_in_master['Update Notes'])
                if row['Update Notes'] == row_in_master['Update Notes'].iloc[0]:
                    message = assignedNoUpdateResponse(curr_req_id,curr_req_desc)
                    sendEmail(recipient, curr_req_id,curr_req_status,message)
                else:
                    message = assignedUpdateResponse(curr_req_id,curr_req_desc,curr_update_notes)
                    sendEmail(recipient, curr_req_id,curr_req_status,message)
                    #print(curr_req_id)

#        if row_in_master['Assignment Status'].iloc[0] != row['Assignment Status']:
#            master_report_df.loc[row_in_master.index, 'Assignment Status'] = row['Assignment Status']
#            print('Assignment Status for ' + str(row['Request Id']) + ' is changed today')
#        if row_in_master['Update Notes'].iloc[0] != row['Update Notes']:
#            master_report_df.loc[row_in_master.index, 'Update Notes'] = row['Update Notes']
#            print('Update Status for ' + str(row['Request Id']) + ' is changed today')
    print("------------------------------------------------------------\n")

# Updating Master Report with changes in work order
master_report_df.set_index('Request Id', inplace=True)
for _, row in current_report_df.iterrows():
    if row['Request Id'] in master_report_df.index:
        #print(row['Request Id'])
        if master_report_df.at[row['Request Id'], 'Update Notes'] != row['Update Notes']:
            master_report_df.at[row['Request Id'], 'Update Notes'] = row['Update Notes']
        if master_report_df.at[row['Request Id'], 'Assignment Status'] != row['Assignment Status']:
            master_report_df.at[row['Request Id'], 'Assignment Status'] = row['Assignment Status']

    else:
        master_report_df.loc[row['Request Id']] = row
master_report_df.reset_index(inplace=True)
#print(master_report_df[['Request Id', 'Assignment Status']])
master_report_df.to_csv('Master_Work_Orders_Directory.csv', index=False)


# > # Changes to be done
# > - # Test other file types
#