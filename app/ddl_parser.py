import sqlparse

def extract_schema_metadata(ddl_sql):
    statements = sqlparse.parse(ddl_sql)
    metadata = []

    for stmt in statements:
        if stmt.get_type() != 'CREATE':
            continue

        tokens = stmt.tokens
        table_name = None
        column_definitions = []
        for token in tokens:
            if isinstance(token, sqlparse.sql.Identifier) and not table_name:
                table_name = token.get_name()
            elif isinstance(token, sqlparse.sql.Parenthesis):
                column_definitions = token.value.strip('()').split(',')

        if not table_name or not column_definitions:
            continue

        column_names = []
        data_types = []

        for col in column_definitions:
            col = col.strip()
            if not col:
                continue
            if col.upper().startswith('FOREIGN KEY'):
                continue
            parts = col.split()
            if len(parts) < 2:
                continue

            column_name = parts[0]
            data_type = parts[1]

            column_names.append(column_name)
            data_types.append(data_type)

        metadata.append([table_name, column_names, data_types])

    return metadata

