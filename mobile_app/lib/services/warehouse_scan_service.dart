import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';

class WarehouseScanService {
  final String baseUrl = AppConfig.automationApiUrl;

  Future<Map<String, dynamic>?> submitScanEvent({
    required String barcode,
    required String objectId,
    required int row,
    required int col,
    required int layer,
    int quantity = 1,
    String? floorId,
    String? floorName,
    String sourceDevice = 'mobile_app',
  }) async {
    try {
      final payload = {
        'barcode': barcode,
        'object_id': objectId,
        'slot': {
          'row': row,
          'col': col,
          'layer': layer,
        },
        'quantity': quantity,
        'floor_id': floorId,
        'floor_name': floorName,
        'source_device': sourceDevice,
      };

      final response = await http.post(
        Uri.parse('$baseUrl/warehouse/scan-events'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      print('Warehouse scan submit error: $e');
    }

    return null;
  }
}
