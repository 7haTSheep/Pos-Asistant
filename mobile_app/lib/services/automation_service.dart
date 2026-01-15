import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';

class AutomationService {
  final String baseUrl = AppConfig.automationApiUrl;

  Future<Map<String, dynamic>> getStatus() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/status'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print('Error fetching status: $e');
    }
    return {};
  }

  Future<bool> startSession() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/start'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'duration_minutes': 40}),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Error starting session: $e');
      return false;
    }
  }

  Future<bool> stopSession() async {
    try {
      final response = await http.post(Uri.parse('$baseUrl/stop'));
      return response.statusCode == 200;
    } catch (e) {
      print('Error stopping session: $e');
      return false;
    }
  }
}
