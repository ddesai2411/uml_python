import json
import re
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))

import pyodbc
import uml_lib.ebAPI_lib as eb

def flatten_json(json_data, parent_key='', sep='_'):
    items = []
    for key, value in json_data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_json(value, new_key, sep=sep).items())
        else:
            items.append((re.sub('[^A-Za-z0-9]+', '_', new_key), value))
    return dict(items)

files = ['Projects','ActiveProjects','Budgets','Commitments','CommitmentItems','Invoices','Companies','FundingRules','FundingSources']


File_Data = {
    'Projects':eb.getDataFromCache("Projects"),
    'ActiveProjects' : eb.getDataFromCache("ActiveProjects"),
    'Budgets': eb.getDataFromCache("Budgets"),
    'Commitments':eb.getDataFromCache("Commitments"),
    'CommitmentItems':eb.getDataFromCache("CommitmentItems"),
    'Invoices':eb.getDataFromCache("Invoices"),
    'Companies':eb.getDataFromCache("Companies"),
    'FundingRules':eb.getDataFromCache("FundingRules"),
    'FundingSources':eb.getDataFromCache("FundingSources"),
    #'POREQ': eb.getDataFromCache("POREQ"),

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


def infer_sql_type(value):
    if value is None:
        return 'NVARCHAR(MAX)'
    return type_map.get(type(value).__name__, 'NVARCHAR(MAX)')


def infer_column_type(column, records):
    for record in records:
        if column in record and record[column] is not None:
            return infer_sql_type(record[column])
    return 'NVARCHAR(MAX)'


# Connect to SQL Server
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=arcgis-sql-02.fs.uml.edu;DATABASE=eBuilder;')
# Create cursor
cursor = conn.cursor()

for name,data in File_Data.items():
    table_name = name 
    print('Dropping table if exists',table_name)
    cursor.execute(f'DROP TABLE IF EXISTS {table_name}')

    # Flatten the JSON data
    flattened_data = [flatten_json(record) for record in data]

    if not flattened_data:
        print(f'Skipping {table_name}: no records found in cache')
        continue

    for record in flattened_data:
     for k, v in record.items():
        if isinstance(v, (dict, list, tuple)):
            record[k] = json.dumps(v)
    
    columns = list(set([column for record in flattened_data for column in record.keys()]))
    if not columns:
        print(f'Skipping {table_name}: no columns generated after flattening')
        continue

    columns_sql = ', '.join(f'{column} {infer_column_type(column, flattened_data)}' for column in columns)
    cursor.execute(f'''IF NOT EXISTS (
        select * from sysobjects where name='{table_name}' and xtype='U'
        )
        CREATE TABLE {table_name} ({columns_sql})''')
    print(table_name,'table created')

    # Insert data
    values = [[record.get(column) for column in columns] for record in flattened_data]
    placeholders = ','.join('?' * len(columns))
    
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    print("INSERT SQL:", insert_sql)
    print("First row of values:", values[0])
    print("Types:", [type(v) for v in values[0]])

    cursor.executemany(insert_sql, values)

    print(table_name,'rows inserted')

# Commit changes and close cursor and connection
conn.commit()
cursor.close()
conn.close()
