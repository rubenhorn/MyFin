#!/usr/bin/env python3

from os import name
from typing import List, Mapping, Optional
import config
import requests
import json
from pathlib import Path
import csv
import sys
from functools import reduce
import pandas as pd
import numpy as np

currency_symbol = '€'
output_folder = Path(__file__).parent / 'reports'


class Expense:
    def __init__(self, year: int, month: int, day: int, description: str, amount: float, category: str, comment: str) -> None:
        self.year = year
        self.month = month
        self.day = day
        self.description = description
        self.amount = amount
        self.category = category
        self.comment = comment


class Report:
    def __init__(self, title: str, previous_interval=None) -> None:
        self.title = title
        self.categories = dict()
        self.sum = 0
        self.previous_interval = previous_interval

    def get_category_share(self, category_name: str) -> float:
        return self.sum / self.categories[category_name].sum

    class Category:
        def __init__(self, expenses_count: int, sum: float, increase: Optional[float]) -> None:
            self.expenses_count = expenses_count
            self.sum = sum
            self.increase = increase

    def add_category(self, category_name: str, category: Category):
        self.categories[category_name] = category
        self.sum = reduce(
            lambda a, b: a+b, [category.sum for category in self.categories.values()])


def download_expenses() -> List[Expense]:
    request = requests.get(
        f'https://script.google.com/macros/s/{ config.DEPLOYMENT_ID }/exec?apiKey={ config.API_KEY }', allow_redirects=True)

    def create_expense(arr):
        year, month, day = [int(v) for v in arr[0].split('-')]
        description = arr[1]
        amount = float(arr[2].replace(',', '').replace(currency_symbol, ''))
        category = arr[3]
        comment = '' if len(arr) < 5 else arr[4]
        return Expense(year, month, day, description, amount, category, comment)
    expenses = [create_expense(v) for v in json.loads(request.content)]
    return expenses


def sort_expenses(expenses: List[Expense]):
    expenses.sort(key=lambda expense: expense.year *
                  10000 + expense.month * 100 + expense.day)


def export_expenses_csv(expenses: List[Expense], filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(
            ['Date', 'Description', 'Amount', 'Category', 'Comment'])
        for expense in expenses:
            csv_writer.writerow([f'{ expense.year }-{ str(expense.month).zfill(2) }-{ str(expense.day).zfill(2) }',
                                expense.description, f'{ expense.amount }{ currency_symbol }', expense.category, expense.comment])


def calculate_and_format_increase(old_value: float, new_value: float) -> str:
    difference = new_value - old_value
    percentage = ((new_value / old_value) - 1) * 100
    increase = '{:+.2f}% ({:.2f} {})'.format(percentage,
                                             abs(difference), currency_symbol)
    return increase


def export_report_html(report: Report, filename):
    template = ''
    with open(Path(__file__).parent / 'template.html', 'r', encoding='utf-8') as file:
        template = file.read()
    category_data = [[key, report.categories[key].sum]
                     for key in report.categories]
    categories_html = pd.read_csv(Path(filename).parent / 'report.csv').replace(np.nan, '', regex=True).to_html(index=False)
    expenses_html = pd.read_csv(Path(filename).parent / 'data.csv').replace(np.nan, '', regex=True).to_html(index=False)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(
            template
                .replace('//replace_with_category_data', str(category_data)[1:-1])
                .replace('<!--replace_with_title-->', f'Expenses {report.title}')
                .replace('<!--replace_with_categories-->', categories_html)
                .replace('<!--replace_with_expenses-->', expenses_html)
        )


def export_report_csv(report: Report, filename):
    increase = None
    if report.previous_interval is not None:
        increase = calculate_and_format_increase(
            report.previous_interval.sum, report.sum)
    rows_and_sum = []
    for category_name in report.categories.keys():
        category = report.categories[category_name]
        row = [category_name, category.expenses_count, '{:.2f}{} ({:.2f}%)'.format(
            category.sum, currency_symbol, 100 * category.sum / report.sum), category.increase]
        rows_and_sum.append((row, category.sum))
    rows_and_sum.sort(key=lambda rs: rs[1] * -1)
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(['Category', 'Expenses count', 'Sum', 'Increase'])
        csv_writer.writerow(
            ['balance', reduce(lambda a, b: a+b, [c.expenses_count for c in report.categories.values()]), '{:.2f}{}'.format(report.sum, currency_symbol), increase])
        for row, _ in rows_and_sum:
            csv_writer.writerow(row)


def group_expenses_by_months(expenses: List[Expense]) -> Mapping[str, List[Expense]]:
    groups = dict()
    for expense in expenses:
        key = f'{ expense.year }-{ str(expense.month).zfill(2) }'
        if key not in groups:
            groups[key] = []
        groups[key].append(expense)
    return groups


def generate_report(title: str, expenses: List[Expense], previous_interval: Report) -> Report:
    report = Report(title, previous_interval)
    category_names = set([expense.category.lower() for expense in expenses])
    for category_name in category_names:
        category_expenses = [
            expense for expense in expenses if expense.category == category_name]
        expenses_count = len(category_expenses)
        expenses_sum = reduce(lambda a, b: a+b,
                              [expense.amount for expense in category_expenses])
        increase = None
        if previous_interval is not None and category_name in previous_interval.categories:
            increase = calculate_and_format_increase(
                previous_interval.categories[category_name].sum, expenses_sum)
        category = Report.Category(expenses_count, expenses_sum, increase)
        report.add_category(category_name, category)
    return report


def create_index_html(groups: Mapping[str, List[Expense]]):
    html = '''<!DOCTYPE html>
<html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/purecss@2.0.6/build/pure-min.css"
            integrity="sha384-Uu6IeWbM+gzNVXJcM9XV3SohHtmWE+3VGi496jvgX1jyvDTXfdK+rfZc8C1Aehk5" crossorigin="anonymous">
    </head>
    <body style="padding: 10px">
        <h1>Expenses Report</h1>
        <ul><!--replace_with_li-->
        </ul>
    </body>
</html>'''.replace('<!--replace_with_li-->', '\n'.join([f'<li><a href="./{key}/index.html">{key}</a></li>' for key in groups.keys()]))
    with open(output_folder / 'index.html', 'w', encoding='utf-8') as file:
        file.write(html)


print('Downloading expenses...', end='')
sys.stdout.flush()
expenses = download_expenses()
print('Done')
print('Sorting expenses...', end='')
sys.stdout.flush()
sort_expenses(expenses)
print('Done')
print('Exporting downloaded expenses...', end='')
sys.stdout.flush()
Path(output_folder).mkdir(exist_ok=True)
export_expenses_csv(expenses, output_folder / 'data.csv')
print('Done')
print('Grouping expenses by month...', end='')
sys.stdout.flush()
groups = group_expenses_by_months(expenses)
print('Done')
print('Generating reports:')
previous_interval = None
for key in groups.keys():
    print(f' - {key}...', end='')
    sys.stdout.flush()
    report_expenses = groups[key]
    report_output_folder = output_folder / key
    report_output_folder.mkdir(exist_ok=True)
    export_expenses_csv(report_expenses, report_output_folder / 'data.csv')
    report = generate_report(key, report_expenses, previous_interval)
    export_report_csv(report, report_output_folder / 'report.csv')
    export_report_html(report, report_output_folder / 'index.html')
    previous_interval = report
    print('Done')
print('Generating index...', end='')
sys.stdout.flush()
create_index_html(groups)
print('Done')

print('\nDone!')
