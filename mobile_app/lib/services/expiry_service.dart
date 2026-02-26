import 'dart:convert';
import '../config.dart';
import 'package:http/http.dart' as http;

class ExpiryService {
  final String baseUrl = AppConfig.automationApiUrl;

  Future<bool> reportExpiry({
    required String sku,
    required String name,
    required DateTime expiryDate,
    required bool isMeat,
  }) async {
    final payload = {
      'sku': sku,
      'name': name,
      'expiry_date': expiryDate.toIso8601String().split('T').first,
      'is_meat': isMeat,
    };

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/inventory/expiry'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Expiry report error: $e');
      return false;
    }
  }
}
