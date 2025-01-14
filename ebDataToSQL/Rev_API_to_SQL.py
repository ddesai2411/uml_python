import json
import re
import pyodbc
import uml_python.uml_lib.ebAPI_lib as eb


def flatten_json(json_data, parent_key='', sep='_'):
    items = []
    for key, value in json_data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_json(value, new_key, sep=sep).items())
        else:
            items.append((re.sub('[^A-Za-z0-9]+', '_', new_key), value))
    return dict(items)


files = ['ActiveProjects', 'Budgets', 'CommitmentItems', 'Companies', 'FundingRules', 'POREQ', 'Projects', 'Invoices']

projects_data = eb.getDataFromCache("Projects"),
active_projects_data = eb.getDataFromCache("ActiveProjects"),
budgets_data = eb.getDataFromCache("Budgets"),
commitments_data = eb.getDataFromCache("Commitments"),
commitmentItems_data = eb.getDataFromCache("CommitmentItems"),
invoices_data = eb.getDataFromCache("Invoices"),
fundingRules_data = eb.getDataFromCache("FundingRules"),
companies_data = eb.getDataFromCache("Companies"),
fundingSources_data = eb.getDataFromCache("FundingSources"),
POREQ_data = eb.getDataFromCache("POREQ"),

File_Data = {
    'ActiveProjects': active_projects_data,
    'Budgets': budgets_data,
    'CommitmentItems': commitmentItems_data,
    'Commitments': commitments_data,
    'Companies': companies_data,
    'FundingRules': fundingRules_data,
    'FundingSources': fundingSources_data,
    'POREQ': POREQ_data,
    'Projects': projects_data,
    'Invoices': invoices_data
}
type_map = {
    'int': 'INT',
    'float': 'FLOAT',
    'str': 'NVARCHAR(MAX)',
    'dict': 'NVARCHAR(MAX)',
    'list': 'NVARCHAR(MAX)',
    'tuple': 'NVARCHAR(MAX)',
    'NoneType': 'NVARCHAR(MAX)',
    'bool': 'BIT',
    'bytes': 'VARBINARY(MAX)',
}

# Connect to SQL Server
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=arcgis-sql.fs.uml.edu;DATABASE=eBuilder;')
# Create cursor
cursor = conn.cursor()

for name, data in File_Data.items():
    table_name = name
    print('Dropping table if exists', table_name)
    cursor.execute(f'DROP TABLE IF EXISTS {table_name}')

    # Flatten the JSON data
    flattened_data = [flatten_json(record) for record in data]

    columns = list(set([column for record in flattened_data for column in record.keys()]))

    columns_sql = ', '.join(f'{column} {type_map[type(flattened_data[0][column]).__name__]}' for column in columns)
    cursor.execute(f'''IF NOT EXISTS (
        select * from sysobjects where name='{table_name}' and xtype='U'
        )CREATE TABLE {table_name} ({columns_sql})''')
    print(table_name, 'table created')

    # Insert data
    values = [[record.get(column) for column in columns] for record in flattened_data]
    placeholders = ','.join('?' * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    cursor.executemany(insert_sql, values)

    print(table_name, 'rows inserted')

# Commit changes and close cursor and connection
conn.commit()
cursor.close()
conn.close()
