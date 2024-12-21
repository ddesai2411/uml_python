import ebAPI_lib as eb
import json

dir = "B:\\ebData\\"

while True:

    try:
        fundingSources_data = eb.get_fundingSources_allData()
        break
    except:
        print("API Limit Reached, Retrying! Do Not Terminate the process")
        pass

module_file = dir + 'FundingSources.json'
with open(module_file, 'w') as file:
    json.dump(fundingSources_data, file)

