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
for mod in moduleFiles:
    modules[mod] = eb.getDataFromCache(mod)

# Keys to be removed
keys_to_remove = ['POREQ']
# Remove items based on key names
modules = {key: value for key, value in modules.items() if key not in keys_to_remove}

cleanedModules = {}
for mod in modules:
    module = modules[mod]
    cleanedModules[mod] = ebSQL.cleanModuleData(module)

try:

    mysql_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'database': 'eBuilder',
    }

    # Connect to SQL Server
    # conn = pyodbc.connect('DRIVER={SQL Server};SERVER=arcgis-sql.fs.uml.edu;DATABASE=eBuilder;')

    # # Create MySQL connection
    conn = mysql.connector.connect(**mysql_config)
    # Create cursor
    count = 0
    cursor = conn.cursor()
    for module, data in cleanedModules.items():
        # Get column names from the table
        cursor.execute(f"DESCRIBE {module}")
        column_names = [column[0] for column in cursor.fetchall()]
        print(column_names)
        print("_______________________________________________________")
        # Insert values into the table
        for record in data:
            # Extract values corresponding to the column names
            values = [record.get(column, None) for column in column_names]

            # Check if the row already exists
            select_sql = f"SELECT * FROM {module} WHERE {' AND '.join([f'{column} = {repr(record.get(column, None))}' if record.get(column, None) is not None else f'{column} IS NULL' for column in column_names])}"

            cursor.execute(select_sql)
            existing_row = cursor.fetchone()

            if not existing_row:
                insert_values = [f'{repr(value)}' if value is not None else 'NULL' for value in values]
                insert_sql = f"INSERT INTO {module} ({', '.join(column_names)}) VALUES ({', '.join(insert_values)})"

                # insert_sql = f"INSERT INTO {module} ({', '.join(column_names)}) VALUES ({', '.join([f'{repr(str(value))}' for value in values])})"
                # print(insert_sql)
                # Execute the insertion query
                try:
                    cursor.execute(insert_sql)
                    print("Insertion successful")
                except Exception as e:
                    print(f"Insertion failed. Error: {e}")

                # print("...................................................")

    # Commit changes and close cursor and connection
    conn.commit()
    cursor.close()
    conn.close()

except Error as e:
    print(f"Error:\n\n {e}")
finally:
    if conn.is_connected():
        conn.close()