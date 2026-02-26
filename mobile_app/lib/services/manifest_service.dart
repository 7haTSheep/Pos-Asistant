import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';

class ManifestService {
  final String baseUrl = AppConfig.automationApiUrl;

  Future<Map<String, dynamic>?> dispatch({
    required String sku,
    required int quantity,
    required String slot,
    required String destination,
    String? notes,
  }) async {
    final payload = {
      'sku': sku,
      'quantity': quantity,
      'slot': slot,
      'destination': destination,
      if (notes != null) 'notes': notes,
    };
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/manifest/dispatch'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      print('Manifest dispatch error: $e');
    }
    return null;
  }

  Future<List<Map<String, dynamic>>> listOpen() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/manifest/open'));
      if (response.statusCode == 200) {
        final Map<String, dynamic> payload = jsonDecode(response.body);
        final items = payload['in_transit'] as List<dynamic>? ?? [];
        return items.map((item) => Map<String, dynamic>.from(item)).toList();
      }
    } catch (e) {
      print('Manifest list error: $e');
    }
    return [];
  }

  Future<bool> verify(int manifestId) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/manifest/verify'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'manifest_id': manifestId}),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Manifest verify error: $e');
      return false;
    }
  }
}
