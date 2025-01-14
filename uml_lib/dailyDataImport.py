#!/usr/bin/env python
# coding: utf-8

import uml_python.uml_lib.ebAPI_lib as eb
import json

def main():

    #dir = '/Users/kysgattu/FIS/ebData/'
    dir = "B:\\ebData\\"
    # dir = "C:\\FISpython\\ebData\\"
    totalAPIcalls = 9
    retStr = ''

    #1. Projects
    while True:
        print("Project data: 1 of ", str(totalAPIcalls))
        try:
            projects_data = eb.get_project_allData()
            break
        except:
            print("API Limit Reached, Retrying! Do Not Terminate the process")
            pass

    module_file = dir + 'Projects.json'
    with open(module_file, 'w') as file:
        json.dump(projects_data, file)
    retStr+=f"Projects Saved at {module_file} \n"

    #2. Active Projects
    while True:
        print("Project data 2: 2 of ", str(totalAPIcalls))
        try:
            active_projects_data = eb.get_active_project_all_data()
            break
        except:
            print("API Limit Reached, Retrying! Do Not Terminate the process")
            pass

    module_file = dir + 'ActiveProjects.json'
    with open(module_file, 'w') as file:
        json.dump(active_projects_data, file)
    retStr += f"Active Projects Saved at {module_file} \n"

    #3. Budget
    while True:
        print("Budget data: 3 of ", str(totalAPIcalls))

        try:
            budgets_data = eb.get_budget_all_data()
            break
        except:
            print("API Limit Reached, Retrying! Do Not Terminate the process")
            pass


    module_file = dir + 'Budgets.json'
    with open(module_file, 'w') as file:
        json.dump(budgets_data, file)

    retStr += f"Budgets Saved at {module_file} \n"

    #4. Commitments

    while True:
        print("Commitment data: 4 of ", str(totalAPIcalls))

        try:
            commitments_data = eb.get_commitment_all_data()
            break
        except:
            print("API Limit Reached, Retrying! Do Not Terminate the process")
            pass

    module_file = dir + 'Commitments.json'
    with open(module_file, 'w') as file:
        json.dump(commitments_data, file)
    retStr += f"Commitments Saved at {module_file} \n"

    #5. Invoice

    while True:
        print("Invoice data: 5 of ", str(totalAPIcalls))

        try:
            invoices_data = eb.get_invoice_allData()
            break
        except:
            print("API Limit Reached, Retrying! Do Not Terminate the process")
            pass


    module_file = dir + 'Invoices.json'
    with open(module_file, 'w') as file:
        json.dump(invoices_data, file)
    retStr += f"Invoices Saved at {module_file} \n"

    #6. Funding Rules

    while True:
        print("Funding Rule data: 6 of ", str(totalAPIcalls))

        try:
            fundingRules_data = eb.get_fundingRules_allData()
            break
        except:
            print("API Limit Reached, Retrying! Do Not Terminate the process")
            pass

    module_file = dir + 'FundingRules.json'
    with open(module_file, 'w') as file:
        json.dump(fundingRules_data, file)
    retStr += f"Funding Rules Saved at {module_file} \n"

    #7. Companies
    while True:
        print("Company data: 7 of ", str(totalAPIcalls))

        try:
            companies_data = eb.get_companies_allData()
            break
        except:
            print("API Limit Reached, Retrying! Do Not Terminate the process")
            pass

    module_file = dir + 'Companies.json'
    with open(module_file, 'w') as file:
        json.dump(companies_data, file)
    retStr += f"Companies Saved at {module_file} \n"

    #8. Commitment items
    while True:
        print("Commitment Items data: 8 of ", str(totalAPIcalls))

        try:
            commitmentItems_data = eb.get_commitmentItems_allData()
            break
        except:
            print("API Limit Reached, Retrying! Do Not Terminate the process")
            pass

    module_file = dir + 'CommitmentItems.json'
    with open(module_file, 'w') as file:
        json.dump(commitmentItems_data, file)
    retStr += f"Commitment Items Saved at {module_file} \n"

    #9. Funding sources
    while True:
        print("Funding source data: 9 of ", str(totalAPIcalls))

        try:
            fundingSources_data = eb.get_fundingSources_allData()
            break
        except:
            print("API Limit Reached, Retrying! Do Not Terminate the process")
            pass

    module_file = dir + 'FundingSources.json'
    with open(module_file, 'w') as file:
        json.dump(fundingSources_data, file)
    retStr += f"Funding Sources Saved at {module_file} \n"


    POREQ_data = eb.getPOREQData()

    module_file = dir + 'POREQ.json'
    with open(module_file, 'w') as file:
        json.dump(POREQ_data, file)

    retStr += f"POREQs Data Saved at {module_file} \n"

    return retStr

if __name__ == "__main__":
    main()

    #get_ipython().system('jupyter nbconvert --to script dailyDataImport.ipynb')

