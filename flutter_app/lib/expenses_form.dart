import 'package:date_field/date_field.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:my_fin_app/submit_expense.dart';

class ExpensesForm extends StatefulWidget {
  const ExpensesForm({Key? key}) : super(key: key);

  @override
  State<StatefulWidget> createState() => ExpensesFormState();
}

class ExpensesFormState extends State<ExpensesForm> {
  final _formKey = GlobalKey<FormState>();

  static const maxFieldLength = 200;

  bool isInputEnabled = true;

  var date = '';
  var description = '';
  var amount = '';
  var category = '';
  var comment = '';

  @override
  void initState() {
    super.initState();
    isInputEnabled = true;
  }

  Future<void> submit(BuildContext context) async {
    if (_formKey.currentState?.validate() ?? false) {
      _formKey.currentState?.save();
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Submitting expense...'),
        duration: Duration(days: 365),
      ));
      setState(() {
        isInputEnabled = false;
      });
      submitExpense(date, description, amount, category, comment).then((value) {
        setState(() {
          isInputEnabled = true;
        });
        _formKey.currentState?.reset();
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Successfully submitted expense!'),
        ));
      }, onError: (e) {
        setState(() {
          isInputEnabled = true;
        });
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Error submitted expense!'),
        ));
      });
    }
  }

  String? _validateTextInputField(String? value) {
    if (value?.trim().isEmpty ?? true) {
      return 'Please enter some text';
    } else if ((value?.length ?? 0) > maxFieldLength) {
      return 'Please enter at most $maxFieldLength  characters';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Form(
        key: _formKey,
        autovalidateMode: AutovalidateMode.disabled,
        child: Padding(
          padding: const EdgeInsets.all(8.0),
          child: Column(
            children: [
              DateTimeFormField(
                  onSaved: (value) {
                    final formatter = NumberFormat('00');
                    date =
                        '${value?.year}-${formatter.format(value?.month)}-${formatter.format(value?.day)}';
                  },
                  initialValue: DateTime.now(),
                  decoration: const InputDecoration(
                    labelText: 'Date',
                  ),
                  mode: DateTimeFieldPickerMode.date,
                  validator: (value) {
                    if (value == null) {
                      return 'Please select a date';
                    }
                    return null;
                  }),
              TextFormField(
                autocorrect: true,
                decoration: const InputDecoration(labelText: 'Description'),
                onSaved: (value) {
                  description = value!.trim();
                },
                validator: _validateTextInputField,
              ),
              TextFormField(
                autocorrect: true,
                decoration: const InputDecoration(labelText: 'Amount (€)'),
                keyboardType: const TextInputType.numberWithOptions(
                    decimal: true, signed: false),
                onSaved: (value) {
                  amount = value!.trim();
                },
                validator: (value) {
                  try{
                    double.parse(value!);
                    _validateTextInputField(value);
                  }
                  catch(_) {
                    return 'Please enter a valid number';
                  }
                },
              ),
              TextFormField(
                autocorrect: true,
                decoration: const InputDecoration(labelText: 'Category'),
                onSaved: (value) {
                  category = value!.trim();
                },
                validator: _validateTextInputField,
              ),
              TextFormField(
                autocorrect: true,
                decoration: const InputDecoration(labelText: 'Comment'),
                onSaved: (value) {
                  comment = value!.trim();
                },
                maxLines: 3,
                validator: (value) {
                  if ((value?.length ?? 0) > maxFieldLength) {
                    return 'Please enter at most $maxFieldLength  characters';
                  }
                  return null;
                },
              ),
              const SizedBox(
                height: 50,
              ),
              ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 50),
                  ),
                  onPressed: !isInputEnabled ? null : () => submit(context),
                  child: const Text('Submit'))
            ],
          ),
        ));
  }
}
