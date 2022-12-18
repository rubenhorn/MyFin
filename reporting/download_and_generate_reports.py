#!/usr/bin/python3

from io import StringIO
from time import sleep
from typing import List, Mapping, Optional
from pathlib import Path
import requests
import csv
import sys
from functools import reduce
import pandas as pd
import numpy as np
import os
import locale

locale.setlocale(locale.LC_ALL, 'de_DE')

if len(sys.argv) < 2:
    print('Keine Google Sheets ID bei Start spezifizier!')
    sheet_id = input('Bitte Google Sheets ID eingeben: ')
else:
    sheet_id = sys.argv[1]
currency_symbol = '€'
output_folder = Path(os.path.expanduser('~\Documents')) / 'Finanzen' / 'Ausgaben'

class Expense:
    def __init__(self, year: int, month: int, day: int, description: str, amount: float, category: str, comment: str) -> None:
        self.year = year
        self.month = month
        self.day = day
        self.description = description
        self.amount = amount
        self.category = category
        self.comment = comment

    def __repr__(self) -> str:
        return f'{ self.description }{ "" if self.comment == "" else " - " + self.comment } ({ self.category }, { currency_symbol }{ self.amount }) on { self.year }-{ self.month }-{ self.day }'


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
    response = requests.get(
        f'https://docs.google.com/spreadsheets/d/{ sheet_id }/gviz/tq?tqx=out:csv', allow_redirects=True)
    if response.status_code != 200:
        print(f'\nFehler beim Download! (HTTP { response.status_code })', file=sys.stderr)
        sleep(3)
        sys.exit(1)
    content = response.content.decode('utf-8')
    file = StringIO(content)
    reader = csv.reader(file, delimiter=',')
    def create_expense(arr):
        day, month, year = [int(v) for v in arr[1].split('.')] # Parsing "dd.MM.yyyy hh:mm:ss"
        description = arr[2]
        amount = float(arr[3].replace('.','').replace(',', '.').replace(currency_symbol, ''))
        category = arr[4]
        comment = '' if len(arr) < 6 else arr[5]
        return Expense(year, month, day, description, amount, category, comment)
    expenses = [create_expense(v) for v in list(reader)[1:]]
    return expenses


def sort_expenses(expenses: List[Expense]):
    expenses.sort(key=lambda expense: expense.year *
                  10000 + expense.month * 100 + expense.day)


def export_expenses_csv(expenses: List[Expense], filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(
            ['Datum', 'Beschreibung', 'Betrag', 'Kategorie', 'Kommentar'])
        for expense in expenses:
            csv_writer.writerow([f'{ str(expense.day).zfill(2) }.{ str(expense.month).zfill(2) }.{ expense.year }',
                                expense.description, f'{ locale.format("%.2f", expense.amount) }{ currency_symbol }', expense.category, expense.comment])


def calculate_and_format_increase(old_value: float, new_value: float) -> str:
    difference = new_value - old_value
    percentage = ((new_value / old_value) - 1) * 100
    increase = '{}% ({} {})'.format(locale.format('%.2f', percentage),
                                             locale.format('%.2f', abs(difference)), currency_symbol)
    if difference > 0:
        increase = '+' + increase
    return increase


def export_report_html(report: Report, filename):
    template = ''
    with open(Path(__file__).parent / 'template.html', 'r', encoding='utf-8') as file:
        template = file.read()
    category_data = [[key, report.categories[key].sum]
                     for key in report.categories]
    categories_html = pd.read_csv(Path(filename).parent / 'bericht.csv').replace(np.nan, '', regex=True).to_html(index=False)
    def create_grouped_expenses_html(filename):
        df = pd.read_csv(Path(filename).parent / 'daten.csv').replace(np.nan, '', regex=True)
        # group by category
        expenses_category = df.groupby('Kategorie')
        html = ''
        for category, expenses in expenses_category:
            html += f'<h3>{ category }</h3>'
            expenses = expenses.drop('Kategorie', axis=1)
            html += expenses.to_html(index=False)
        return html
    grouped_expenses_html = create_grouped_expenses_html(Path(filename).parent / 'daten.csv')
    expenses_html = pd.read_csv(Path(filename).parent / 'daten.csv').replace(np.nan, '', regex=True).to_html(index=False)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(
            template
                .replace('//replace_with_category_data', str(category_data)[1:-1])
                .replace('<!--replace_with_title-->', f'Ausgaben {report.title}')
                .replace('<!--replace_with_categories-->', categories_html)
                .replace('<!--replace_with_grouped_expenses-->', grouped_expenses_html)
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
        row = [category_name, category.expenses_count, '{}{} ({}%)'.format(
            locale.format('%.2f', category.sum), currency_symbol, locale.format('%.2f', 100 * category.sum / report.sum)), category.increase]
        rows_and_sum.append((row, category.sum))
    rows_and_sum.sort(key=lambda rs: rs[1] * -1)
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(['Kategorie', 'Anzahl an Ausgaben', 'Summe', 'Anstieg'])
        csv_writer.writerow(
            ['gesamt', reduce(lambda a, b: a+b, [c.expenses_count for c in report.categories.values()]), locale.format("%.2f", report.sum) + currency_symbol, increase])
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
            expense for expense in expenses if expense.category.lower() == category_name]
        expenses_count = len(category_expenses)
        expenses_sum = reduce(lambda a, b: a+b,
                              [0] + [expense.amount for expense in category_expenses])
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
        <h1>Berichte &uuml;ber Ausgaben</h1>
        <ul><!--replace_with_li-->
        </ul>
    </body>
</html>'''.replace('<!--replace_with_li-->', '\n'.join([f'<li><a href="./{key}/index.html">{key}</a></li>' for key in groups.keys()]))
    with open(output_folder / 'index.html', 'w', encoding='utf-8') as file:
        file.write(html)


print('Lade Ausgaben herunter...', end='')
sys.stdout.flush()
expenses = download_expenses()
print('Fertig')
print('Sortiere Ausgaben...', end='')
sys.stdout.flush()
sort_expenses(expenses)
print('Fertig')
print('Exportiere heruntergeladene Ausgaben...', end='')
sys.stdout.flush()
Path(output_folder).mkdir(exist_ok=True, parents=True)
export_expenses_csv(expenses, output_folder / 'ausgaben.csv')
print('Fertig')
print('Gruppiere Ausgaben nach Monat...', end='')
sys.stdout.flush()
groups = group_expenses_by_months(expenses)
print('Fertig')
print('Generiere Berichte:')
previous_interval = None
for key in groups.keys():
    print(f' - {key}...', end='')
    sys.stdout.flush()
    report_expenses = groups[key]
    report_output_folder = output_folder / key
    report_output_folder.mkdir(exist_ok=True)
    export_expenses_csv(report_expenses, report_output_folder / f'daten.csv')
    report = generate_report(key, report_expenses, previous_interval)
    export_report_csv(report, report_output_folder / 'bericht.csv')
    export_report_html(report, report_output_folder / 'index.html')
    previous_interval = report
    print('Fertig')
print('Generiere Index...', end='')
sys.stdout.flush()
create_index_html(groups)
print('Fertig')

print('\nFertig!')

# Open report in browser
os.system(f'start { (output_folder / "index.html").absolute() }')
