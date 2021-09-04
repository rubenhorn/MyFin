#!/usr/bin/env python3

from typing import List
import config
import requests
import json
from pathlib import Path
import csv

currency_symbol = '€'
output_folder = str(Path(__file__).parent.absolute() / 'reports')


class Expense:
    def __init__(self, year: int, month: int, day: int, description: str, amount: float, category: str, comment: str) -> None:
        self.year = year
        self.month = month
        self.day = day
        self.description = description
        self.amount = amount
        self.category = category
        self.comment = comment


def download_expenses() -> List[Expense]:
    request = requests.get(
        f'https://script.google.com/macros/s/{ config.DEPLOYMENT_ID }/exec?apiKey={ config.API_KEY }', allow_redirects=True)

    def create_expense(arr):
        year, month, day = [int(v) for v in arr[0].split('-')]
        description = arr[1]
        amount = float(arr[2].replace(currency_symbol, ''))
        category = arr[3]
        comment = '' if len(arr) < 5 else arr[4]
        return Expense(year, month, day, description, amount, category, comment)
    expenses = [create_expense(v) for v in json.loads(request.content)]
    return expenses


def export_csv(expenses: List[Expense]):
    with open(Path(output_folder) / 'data.csv', 'w', newline='', encoding='utf-8') as file:
        file.write('Date,Description,Amount,Category,Comment\n')
        csv_writer = csv.writer(file)
        for expense in expenses:
            csv_writer.writerow([f'{ expense.year }-{ str(expense.month).zfill(2) }-{ str(expense.day).zfill(2) }',
                                expense.description, f'{ expense.amount }{ currency_symbol }', expense.category, expense.comment])


expenses = download_expenses()
Path(output_folder).mkdir(exist_ok=True)
export_csv(expenses)
print('Done!')
