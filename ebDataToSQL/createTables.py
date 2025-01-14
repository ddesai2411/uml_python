#!/usr/bin/env python
# coding: utf-8

import os
import pyodbc
import uml_python.uml_lib.ebAPI_lib as eb
import uml_python.uml_lib.ebSQLlib as ebSQL
import mysql.connector
from mysql.connector import Error

# moduleFiles = [os.path.splitext(file)[0] for file in [f for f in os.listdir("B:\\ebData") if f.endswith('.json')]]
moduleFiles = [os.path.splitext(file)[0] for file in
               [f for f in os.listdir("/Users/kysgattu/FIS/ebData") if f.endswith('.json')]]

modules = {}
cleanedModules = {}
queries = {}
columnNames = {}

for mod in moduleFiles:
    modules[mod] = eb.getDataFromCache(mod)

# Keys to be removed
keys_to_remove = ['POREQ']
# Remove items based on key names
modules = {key: value for key, value in modules.items() if key not in keys_to_remove}

for mod in modules:
    module = modules[mod]
    cleanedModules[mod] = ebSQL.cleanModuleData(module)

for mod in cleanedModules:
    colsAndQueries = ebSQL.generate_table_creation_sql(mod, cleanedModules[mod])
    queries[mod] = colsAndQueries["SQL Statement"]
    columnNames[mod] = colsAndQueries["Column Names"]

primaryKeys = {
    "Projects":'projectId',
    "ActiveProjects":'projectId',
    "Budgets":'budgetsId',
    "Commitments":'commitmentID',
    "CommitmentItems":'commitmentID',
    "Invoices":'invoiceId',
    "Companies":'companyId',
    "FundingSources":'fundingSourceID',
    "FundingRules":'fundingRuleID',
    }

try:
    mysql_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'database': 'eBuilder',
    }
    # Create MySQL connection
    conn = mysql.connector.connect(**mysql_config)

    # Connect to SQL Server
    # conn = pyodbc.connect('DRIVER={SQL Server};SERVER=arcgis-sql.fs.uml.edu;DATABASE=eBuilder;')

    # Create cursor
    cursor = conn.cursor()

    for module in queries:
        # Check if table exists
        cursor.execute(f"SHOW TABLES LIKE '{module}'")
        table_exists = cursor.fetchone()

        if table_exists:
            print(f'{module} Table Exists')
            # Table exists, compare existing structure with the new query
            cursor.execute(f"DESCRIBE {module}")
            existing_columns = [column[0] for column in cursor.fetchall()]
            new_columns = columnNames[module]

            if set(existing_columns) != set(new_columns):
                # Table structure doesn't match, update the table
                print(f"{module} Table structure doesn't match, update the table")
                cursor.execute(f'DROP TABLE IF EXISTS {module}')
                cursor.execute(queries[module])
                print(f"{module} Modified.\n")
        else:
            # Table doesn't exist, create it
            print(f"{module} Table doesn't exist, create it")
            cursor.execute(queries[module])
            print(f"{module} Table created.\n")

        cursor.execute(f"DESCRIBE {module}")
        priKeys = [column[3] for column in cursor.fetchall()]
        if primaryKeys[module] in existing_columns and 'PRI' not in priKeys:
            pkCommand = f'ALTER TABLE {module} ADD PRIMARY KEY ({primaryKeys[module]})'
            cursor.execute(pkCommand)
            print(f"Primary Key added on {primaryKeys[module]}")
        else:
            print("Primary Key already Present in the Table")
        print("____________________________________________________________________________________")

    # Commit changes and close cursor and connection
    conn.commit()
    cursor.close()
    conn.close()

except Error as e:
    print(f"Error:\n\n {e}")
finally:
    if conn.is_connected():
        conn.close()



# >#### POREQ Has to be done
# def analyze_data_and_determine_sizes(data, parent_key='', column_sizes=None, tables=None):
#     if column_sizes is None:
#         column_sizes = {}
#     if tables is None:
#         tables = []
#
#     for key, value in data.items():
#         if isinstance(value, dict):
#             analyze_data_and_determine_sizes(value, f'{parent_key}_{key}' if parent_key else key, column_sizes, tables)
#         elif isinstance(value, list):
#             column_name = f'{parent_key}_{key}' if parent_key else key
#             # For list items, set a default size of 10
#             column_sizes[column_name] = {'type': 'VARCHAR', 'size': 10}
#
#             # Create a table for the list
#             list_table_name = f'{column_name}_Table'
#             list_table_columns = {}
#             for item in value:
#                 analyze_data_and_determine_sizes(item, column_sizes=list_table_columns)
#
#             list_table_sql = f"CREATE TABLE {list_table_name} ({', '.join([f'{column} VARCHAR(MAX)' for column in list_table_columns])});"
#             tables.append(list_table_sql)
#         else:
#             column_name = f'{parent_key}_{key}' if parent_key else key
#             current_size = max(10, len(str(value)))
#             if column_name not in column_sizes or current_size > column_sizes[column_name]['size']:
#                 column_sizes[column_name] = {'type': 'VARCHAR', 'size': current_size}
#
# # Example data
# data = {'CommitmentType': {'CommitmentType': '1. Purchase Order'},
#         'Company': {'CompanyId': '2c351f90-e2d9-4a74-ac45-6e11938cec9a'},
#         'Project': {'ProjectName': 'zzTEST Integration'},
#         'Process': {'Prefix': 'POREQ'},
#         'ProcessInstance': {'InstanceCounter': '55',
#                             'PortalId': 'a025166b-48eb-4f10-9dea-31df66baf669',
#                             'Subject': 'ELLENZWEIG - 09/28/2023',
#                             'CurrentStepName': 'Python Hold: Send to BW',
#                             'DataFields': {'Description': 'Test Case #9: 1 line, split ST 1 line, Lump Sum',
#                                            'Attention': '',
#                                            'Room Floor Suite': '',
#                                            'Blanket Order': 'Yes',
#                                            'External Comments': '',
#                                            'username': '10129780',
#                                            'City': '',
#                                            'State': '',
#                                            'Shipping Address': '150 Wilder Street: WILDER: 150 Wilder Street, Lowell, MA 01854',
#                                            'Zip Code': '',
#                                            'Address Line': ''}},
#         'LineItems': [{'CommitmentItem': {'Amount': '20.0000',
#                                           'CommitmentId': '0ae199a3-29f1-4316-8151-3cf13b0b6726',
#                                           'FundingRuleId': 'a3dc1b37-8231-496e-854b-d2b1146e6ef2',
#                                           'ItemNumber': '001',
#                                           'Quantity': '0.0000',
#                                           'UnitCost': '0.0000'}}]}
#
# column_sizes = {}
# tables = []
# analyze_data_and_determine_sizes(data, column_sizes=column_sizes, tables=tables)
#
# # Generate SQL table creation statement for the main table
# main_table_name = 'YourMainTableName'  # Replace with your desired main table name
# # main_table_sql = f"CREATE TABLE {main_table_name} ({', '.join([f'{column} VARCHAR({details['size']})' for column, details in column_sizes.items()])});"
# # print(main_table_sql)
#
# # Print the determined column sizes
# columns_data = ''
# for column, details in column_sizes.items():
#     # print(f"{column} ({details['type']}({details['size']})),\n")
#     columns_data += f"{column} {details['type']}({details['size']}), "
#
# print(columns_data)
# main_table_sql = f"CREATE TABLE {main_table_name} {columns_data}"
# # print(main_table_sql)
# # Print the table creation statements for lists
# for table_sql in tables:
#     print(table_sql)
