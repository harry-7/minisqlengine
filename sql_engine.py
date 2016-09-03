"""
Main runner file for sql engine
"""
from re import match
import string
import sys

from util import read_meta, check_for, error_exit, get_tables_columns, \
    format_string, read_table_data, generate_header, display_output

__author__ = 'harry-7'
METAFILE = 'metadata.txt'
FUNCTIONS = ['distinct', 'max', 'sum', 'avg', 'min']


def main():
    """ The Main function. Initiates the sql engine functioning"""
    table_info = read_meta(METAFILE)
    queries = str(sys.argv[1]).split(';')
    for query in queries:
        process_query(query, table_info)


def process_query(query, table_info):
    """Processes the given query and prints the output"""
    query = format_string(query)
    function_process = []
    distinct_process = []

    if not check_for('from', query.split()):
        error_exit("Syntax Error: No Table Selected")

    lis = query.split('from')
    project = format_string(str(lis[0]))
    remaining = format_string(str(lis[1]))

    if len(lis) != 2:
        error_exit("Syntax Error: More than one from statement given")
    if not check_for('select', project.lower().split()):
        error_exit("Syntax Error: No Select statement given")
    clauses = remaining.split('where')
    tables = format_string(clauses[0])
    tables = tables.split(',')
    tables_data = {}
    for i in range(0, len(tables)):
        tables[i] = format_string(tables[i])
        if tables[i] not in table_info.keys():
            error_exit('No Such Table \'' + tables[i] + '\' Exists')
        tables_data[tables[i]] = read_table_data(tables[i])

    required = project[len('select '):]
    required = format_string(required)
    required = required.split(',')
    columns = []
    process_select(required, function_process, distinct_process, columns)

    if len(clauses) > 1 and \
            (len(function_process) != 0 or len(distinct_process) != 0):
        error_exit('ERROR:Where Condition can '
                   'only be given to project functions')
    if len(clauses) > 1 and len(tables) == 1:
        # Single table where condition
        process_where(clauses[1], columns,
                      tables[0], table_info, tables_data[tables[0]])
    elif len(clauses) > 1 and len(tables) > 1:
        process_where_multiple(clauses[1], columns,
                               tables, table_info, tables_data)
    elif len(function_process) != 0:
        process_aggregate(function_process, tables, table_info, tables_data)
    elif len(distinct_process) != 0:
        pass
    elif len(tables) > 1:
        process_join(columns, tables, table_info, tables_data)
    else:
        process_project(columns, tables[0], table_info, tables_data)


def process_select(required, function_process, distinct_process, columns):
    """Process the select part of the query and return tokens"""
    column_name = ''
    for thing in required:
        taken = False
        thing = format_string(thing)
        for function in FUNCTIONS:
            if function + '(' in thing.lower():
                taken = True
                if ')' not in thing:
                    error_exit('Syntax Error: \')\' expected ')
                else:
                    column_name = thing.strip(')').split(function + '(')[1]
                if function == 'distinct':
                    distinct_process.append([function, column_name])
                else:
                    function_process.append([function, column_name])
                break
        if not taken:
            columns.append(thing.strip('()'))


def generate_evaluator(condition, table, table_info, data):
    """Generates the evaluator string for single table where"""
    condition = condition.split(' ')
    evaluator = ''
    for i in condition:
        if i == '=':
            evaluator += i * 2
        elif i.lower() == 'and' or i.lower == 'or':
            evaluator += ' ' + i.lower() + ' '
        elif i in table_info[table]:
            evaluator += data[table_info[table].index(i)]
        else:
            evaluator += i
    return evaluator


def process_where_multiple(condition, columns, tables,
                           table_info, tables_data):
    """Deals with Join type queries"""
    condition = format_string(condition)
    oper = ''
    if '<' in condition:
        condition = condition.split('<')
        oper = '<'
    elif '>' in condition:
        condition = condition.split('>')
        oper = '>'
    elif '=' in condition:
        condition = condition.split('=')
        oper = '='
    pattern = "([" + string.letters + "])+"
    if len(condition) == 2 and match(
            pattern, format_string(condition[1])) is not None:
        print condition[1]
        process_where_join([condition, oper], columns, tables, table_info, tables_data)


def process_where_join(clauses, columns, tables, table_info, tables_data):
    """ Processes the where clause with join condition"""
    if clauses[1] == '=':
        clauses[1] *= 2
    columns_condition, tables_condition = get_tables_columns(
        clauses[0], tables, table_info)
    columns, tables = get_tables_columns(
        columns, tables, table_info)
    table1 = tables_condition[0]
    table2 = tables_condition[1]
    column1 = table_info[table1].index(columns_condition[table1][0])
    column2 = table_info[table2].index(columns_condition[table2][0])
    needed_data = []
    for data in tables_data[table1]:
        for row in tables_data[table2]:
            evaluator = data[column1] + clauses[1] + row[column2]
            if eval(evaluator):
                needed_data.append(data + row)
    display_output(tables, columns, table_info, needed_data)


def process_join(columns, tables, table_info, tables_data):
    """Deals with Join type queries"""

    columns_in_table, tables_needed = get_tables_columns(
        columns, tables, table_info)
    join_data = []
    table1 = tables_needed[0]
    table2 = tables_needed[1]
    for item1 in tables_data[table1]:
        for item2 in tables_data[table2]:
            join_data.append(item1 + item2)
    display_output(tables_needed, columns_in_table, table_info, join_data)
    return


def process_where(condition, columns, table, table_info, table_data):
    """ Process where clause on a single table"""
    condition = format_string(condition)

    if len(columns) == 1 and columns[0] == '*':
        columns = table_info[table]
    print generate_header(table, columns)

    for row in table_data:
        evaluator = generate_evaluator(condition, table, table_info, row)
        if eval(evaluator):
            for column in columns:
                print row[table_info[table].index(column)],
            print


def process_aggregate(queries, tables,
                      table_info, tables_data):
    """Deals with aggregate functions and distinct"""
    header, result = '', ''
    for query in queries:
        function_name = query[0]
        column_name = query[1]
        table, column = '', ''
        if '.' in column_name:
            table, column = column_name.split('.')
        else:
            cnt = 0
            for tab in tables:
                if column_name in table_info[tab]:
                    if cnt > 1:
                        error_exit('Abigous column name \'' +
                                   column_name + '\' given')
                    table = tab
                    column = column_name
                    cnt += 1
            if cnt == 0:
                error_exit('No such column \'' + column_name + '\' found')

        data = []
        header += table + '.' + column + ', '
        for row in tables_data[table]:
            data.append(int(row[table_info[table].index(column)]))

        if function_name.lower() == 'max':
            result += str(max(data))
        elif function_name.lower() == 'min':
            result += str(min(data))
        elif function_name.lower() == 'sum':
            result += str(sum(data))
        elif function_name.lower() == 'avg':
            result += str(float(sum(data)) / len(data))
        result += ' '
    header.strip(', ')
    print header
    print result


def process_project(columns, table, table_info, tables_data):
    """ Deals with project operation without in a single table"""
    if len(columns) == 1 and columns[0] == '*':
        columns = table_info[table]
    for column in columns:
        if column not in table_info[table]:
            error_exit('No Such column \'' + column +
                       '\' found i  n the given table \'' + table + '\' ')
    print generate_header(table, columns)

    for data in tables_data[table]:
        for column in columns:
            print data[table_info[table].index(column)],
        print


if __name__ == '__main__':
    main()
