"""
Contains various utility functions required for the mini sql Shell
"""
import re
import sys
import csv

__author__ = 'harry-7'


def read_meta(file_name):
    """ Reads the Metadata of the file
    returns a dictionary containing the info about table
    """
    try:
        meta_file = open(file_name, 'r')
        start = False
        table_name = ""
        table_info = {}
        for line in meta_file:
            line = line.strip()
            if line == '<begin_table>':
                start = True
            elif start:
                table_name = line
                table_info[table_name] = []
                start = False
            elif line != '<end_table>':
                table_info[table_name].append(line)
        return table_info
    except IOError:
        error_exit('No metadata file \'' + file_name + '\' found')


def read_table_data(table_name):
    """ Reads the csv file data and returns it as a list"""
    data = []
    file_name = table_name + '.csv'
    try:
        data_file = open(file_name, 'rb')
        reader = csv.reader(data_file)
        for row in reader:
            data.append(row)
        data_file.close()
    except IOError:
        error_exit('No file for given table: \'' + table_name + '\' found')
    return data


def check_for_string(string, lis):
    """Checks whether string is in the list"""
    return string in lis


def format_string(string):
    """Returns the query in a formatted manner removing unnecessary spaces"""
    return (re.sub(' +', ' ', string)).strip()


def generate_header(table_name, columns):
    """Prints the header of the columns needed"""
    string = ''
    for column in columns:
        if string != '':
            string += ','
        string += table_name + '.' + column

    return string


def display_output(tables_needed, columns_in_table, table_info, tables_data, join):
    """ Displays the output for a join operation without `where` clause"""
    if join:
        table1 = tables_needed[0]
        table2 = tables_needed[1]
        header1 = generate_header(table1, columns_in_table[table1])
        header2 = generate_header(table2, columns_in_table[table2])
        print header1 + ',' + header2
        for item in tables_data:
            ans = ''
            for column in columns_in_table[table1]:
                ans += item[table_info[table1].index(column)] + ','
            for column in columns_in_table[table2]:
                ans += item[table_info[table2].index(column) +
                            len(table_info[table1])] + ','
            print ans.strip(',')

    else:
        for table in tables_needed:
            print generate_header(table, columns_in_table[table])
            for data in tables_data[table]:
                ans = ''
                for column in columns_in_table[table]:
                    ans += data[table_info[table].index(column)] + ','
                print ans.strip(',')
            print


def error_exit(error):
    """Prints the error to Stderr and exits the program"""
    sys.stderr.write(error + '\n')
    quit(-1)



def join_needed_data(oper, tables, needed_data, tables_data):
    """ Joins the data needed for where clause"""
    if oper == 'and':
        return join_data_and(tables, needed_data)
    elif oper == 'or':
        return join_data_or(tables, needed_data, tables_data)
    else:
        return join_data_single(tables, needed_data, tables_data)


def join_data_and(tables, needed_data):
    """ Joins the data if AND operator in condition"""
    final_data = []
    table1 = format_string(tables[0])
    table2 = format_string(tables[1])
    for item1 in needed_data[table1]:
        for item2 in needed_data[table2]:
            final_data.append(item1 + item2)
    return final_data


def join_data_or(tables, needed_data, tables_data):
    """ Joins the data if OR operator in condition"""
    final_data = []
    table1 = format_string(tables[0])
    table2 = format_string(tables[1])
    for item1 in needed_data[table1]:
        for item2 in tables_data[table2]:
            if item2 not in needed_data[table2]:
                final_data.append(item1 + item2)
    for item1 in needed_data[table2]:
        for item2 in tables_data[table1]:
            if item2 not in needed_data[table1]:
                final_data.append(item2 + item1)
    return final_data


def join_data_single(tables, needed_data, tables_data):
    """ Joins the data with no AND/OR Operator"""
    final_data = []
    table1 = needed_data.keys()[0]
    flag = False
    table2 = tables[1]
    if table1 == tables[1]:
        table2 = tables[0]
        flag = True
    for item1 in needed_data[table1]:
        for item2 in tables_data[table2]:
            if not flag:
                final_data.append(item2 + item1)
                continue
            final_data.append(item1 + item2)
    return final_data
