import 'package:http/http.dart' as http;

import 'config.dart' as config;

Future<void> submitExpense(String date, String description, String amount,
    String category, String comment) async {
  final url = Uri.encodeFull(
      'https://script.google.com/macros/s/${config.DEPLOYMENT_ID}/exec?apiKey=${config.API_KEY}&date=$date&description=$description&amount=$amount&category=$category&comment=$comment');

  http.Request request = http.Request('Post', Uri.parse(url))
    ..followRedirects = true;
  http.Client baseClient = http.Client();
  http.StreamedResponse response = await baseClient.send(request);
  Uri redirectUri = Uri.parse(response.headers['location']!);
  final responseBody = (await http.get(redirectUri)).body;
  assert(responseBody == '{"success":true}');
}
