import re
def parseColumnName(colName):
    # Replace specific characters with their corresponding replacements
    colName = colName.strip().replace('&', '_AND_').replace('#', '_NUM').replace('/', '_OR_').replace(')', '').replace('}', '').replace(']', '')
    # Remove special character at the end of the string
    if colName and not colName[-1].isalnum():
        colName = colName[:-1]
    # Replace any remaining non-alphanumeric characters with underscores
    colName = re.sub('[^A-Za-z0-9]+', '_', colName)
    return colName

def cleanModuleData(module):
    cleanedModData = []
    for record in module:
        cleanedRecord = {parseColumnName(key): value for key, value in record.items()}
        cleanedModData.append(cleanedRecord)
    return cleanedModData

def generate_table_creation_sql(module, data):
    column_sizes = {}
    column_names = []
    for row in data:
        for column, value in row.items():
            if column not in column_names: column_names.append(column)
            current_size = max(10, len(str(value)))
            if column not in column_sizes or current_size > column_sizes[column]['size']:
                column_sizes[column] = {'type': 'VARCHAR', 'size': current_size}

    columns = [f"{column} {info['type']}({info['size']})" for column, info in column_sizes.items()]
    columns_str = ", ".join(columns)
    sql_statement = f"CREATE TABLE {module} ({columns_str});"

    return {"Column Names": column_names, "SQL Statement":sql_statement}

