import 'dart:convert';
import 'package:http/http.dart' as http;

class OpenFoodFactsService {
  Future<Map<String, dynamic>?> searchProduct(String barcode) async {
    if (barcode.isEmpty) return null;

    final url = Uri.parse('https://world.openfoodfacts.org/api/v0/product/$barcode.json');
    
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 1 && data['product'] != null) {
          return {
            'name': data['product']['product_name'] ?? '',
            'image': data['product']['image_url'] ?? '',
          };
        }
      }
    } catch (e) {
      print('Error fetching product from OpenFoodFacts: $e');
    }
    return null;
  }
}
