const API_KEY = 'mySecretApiKey';
const currencySymbol = '€'

// Run this first
function setup() {
  const spreadsheetId = SpreadsheetApp.getActiveSpreadsheet().getId();
  PropertiesService.getScriptProperties().setProperty('spreadsheetId', spreadsheetId);
  Sheets.Spreadsheets.Values.update({
    'majorDimension': 'ROWS',
    'values': [['Date', 'Description', 'Amount', 'Category', 'Comment']]
  }, spreadsheetId, 'Sheet1!A1:E1', {valueInputOption: 'RAW'});
}

const range = 'Sheet1!A:E'

function doGet(request) {
  if(request.parameter['apiKey'] != API_KEY) throw 'Invalid api key!';
  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('spreadsheetId');
  const data = Sheets.Spreadsheets.Values.get(spreadsheetId, range).values.slice(1);
  return ContentService.createTextOutput(JSON.stringify(data));
}

function doPost(request) {
  if(request.parameter['apiKey'] != API_KEY) throw 'Invalid api key!';
  const date = request?.parameter['date'];
  if(!/\d{4}-[01]\d-\d{2}/.test(date)) throw 'Invalid date format!';
  const description = request?.parameter['description'];
  if(description == null || description.length > 200) throw 'Invalid description';
  const amount = Number(request?.parameter['amount']);
  if(Number.isNaN(amount)) throw 'Invalid amount';
  const category = request?.parameter['category'];
  if(category == null || category.length > 200) throw 'Invalid category';
  const comment = request?.parameter['comment'] ?? '';
  if(comment.length > 200) throw 'Invalid comment';
  const resource = {
    'majorDimension': 'ROWS',
    'values': [[date, description, `${ amount }${ currencySymbol }`, category, comment]]
  };
  const optionalArgs = {valueInputOption: 'USER_ENTERED'};
  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('spreadsheetId');
  const result = Sheets.Spreadsheets.Values.append(resource, spreadsheetId, range, optionalArgs);
  const success = result.updates.updatedRows == 1
  return ContentService.createTextOutput(JSON.stringify({ 'success': success }));
}
