import argparse
import os
import re

from datetime import datetime

def arg_Parser():
    parser = argparse.ArgumentParser(description='Generate ToDoCheck Report')
    parser.add_argument("-rt", '--root', type=str, required=True,
                        help='Root directory of the project repository')
    parser.add_argument("-d", "--destination", type=str, required=True,
                        help='Destination folder path for the html report')
    parser.add_argument("-m", "--modified", type=str, required=True,
                        help='List of modified files')
    args = parser.parse_args()
    return vars(args)

def comment_check(line, extension, file_name):
    if extension in ('.c', '.cpp', '.h', '.hpp', '.groovy', '.js', '.cs') or (file_name.startswith('Jenkinsfile')):
        return line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith('*')
    elif extension in ('.css', '.json'):
        return line.strip().startswith('/*') or line.strip().startswith('*')
    elif extension in ('.py', '.yml', '.yaml', '.ps1', '.bat'):
        return line.strip().startswith('#')
    return False

def check_comments(repo_path, modified_file_list):
    todo_pattern = re.compile(r'TODO', re.IGNORECASE)
    project_pattern = re.compile(r'USGVINISPZ-\d+')

    todo_results = []
    modified_todo_results = []
    file_extensions = ('.c', '.cpp', '.h', '.hpp', '.py', '.groovy', '.js', '.css','.json', '.yml', '.yaml', '.ps1', '.bat', '.cs')

    for root, _, files in os.walk(repo_path):
        for file in files:
            current_file_name = os.path.basename(file)
            if file.endswith(file_extensions) or current_file_name.startswith('Jenkinsfile'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        current_file_extension = os.path.splitext(file)[1]
                        if comment_check(line, current_file_extension, current_file_name) and (todo_pattern.search(line) or project_pattern.search(line)):
                            todo_results.append((file_path, i + 1, line.strip()))
                            relative_file_path = os.path.relpath(file_path, repo_path)
                            print(f"relative path: {relative_file_path}")
                            if relative_file_path in modified_file_list:
                                modified_todo_results.append((file_path, i + 1, line.strip()))


    return todo_results, modified_todo_results

_HTML_STYLE = '''
html, body{
    width:98%;
    background: white;
    font-family: "Consolas", "Bitstream Vera Sans Mono", monospace !important;
}
table.report {
  font-family: "Times New Roman", Times, monospace;
  text-align: right;
  table-layout: fixed;
  margin-left: 2%;
  margin-right: 2%;
  width: 98%;
}
table.report td, table.report th {
  border: 1px solid black;
  padding: 2px 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  word-wrap: break-word;
  text-align: center;
}
table.report tr:nth-child(even) {
  background: #E0E4F5;
}
table.report thead {
  background: #06FA4;
}
table.report thead th {
  font-weight: bold;
  color: #FFFFFF;
  text-align: center;
  border-left: 2px solid #FFFFFF;
}
table.report thead th:first-child {
  border-left: none;
}
table.report tfoot {
  font-weight: bold;
  color: #333333;
  background: #E0E4F5;
  border-top: 3px solid #444444;
}
'''

def _create_report_table(list_of_todos):
    yield '<table class=\"todo_report\">'
    yield '<th>File</th>'
    yield '<th>Line</th>'
    yield '<th>Comment</th>'
    for todo in list_of_todos:
        yield '  <tr><td>'
        yield '    </td><td>'.join([str(value) for value in todo])
        yield '  </td></tr>'
    yield '</table>'

def _create_report_header(title):
    return '\n'.join([
        '<h1>TODO Report {}</h1>', '<p><b>Date: </b>{}</p>'
    ]).format(title, datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

def create_html_report(html_title, todo_results, output_path):
    html_table = '\n'.join(_create_report_table(todo_results))
    html_table_style = '<style>\n{}\n</style>'.format(_HTML_STYLE)
    title_style = '<title>{}</title>'.format(html_title)
    report_header = _create_report_header(html_title)
    html_data = '\n'.join([
        '<!DOCTYPE html>', '<html>', '<head>', title_style, html_table_style,
        '</head>', '<body>', report_header, html_table, '</body>', '</html>'
    ])

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    report_path = os.path.join(output_path, html_title)
    with open(report_path, "w") as html_result_file:
        html_result_file.write(html_data)

def main():
    args = arg_Parser()
    repo_path = args["root"]
    destination_path = args["destination"]
    modified_files_list = args["modified"].split()
    print(f"modified files: {modified_files_list}")
    todo_results, modified_todo_results = check_comments(repo_path, modified_files_list)
    if todo_results:
        print("TODO or USGVINISPZ comments found, results:")
        for file_path, line, message in todo_results:
            print(f"{file_path}:{line}: {message}")
        print("Creating HTML report...")
        create_html_report("todo_report.html", todo_results, destination_path)
    else:
        print("There are no TODO or USGVINISPZ comments found, ToDo Check is complete.")
        exit(0)

    if modified_todo_results:
        print("TODO or USGVINISPZ comments found in modified files, please review the following comments:")
        for file_path, line, message in modified_todo_results:
            print(f"{file_path}:{line}: {message}")
        print("Creating HTML report for modified files")
        create_html_report("modified_todo_report.html", modified_todo_results, destination_path)
    else:
        print("There are no TODO or USGVINISPZ comments found in the modified files, ToDo Check is complete")

if __name__ == "__main__":
    main()
