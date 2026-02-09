import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../config.dart';

class WooCommerceService {
  final String baseUrl = AppConfig.baseUrl;
  final String key = AppConfig.consumerKey;
  final String secret = AppConfig.consumerSecret;

  String get _authHeader {
    final credentials = '$key:$secret';
    final bytes = utf8.encode(credentials);
    return 'Basic ${base64.encode(bytes)}';
  }

  Future<Map<String, dynamic>?> getProductBySku(String sku) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/wp-json/wc/v3/products?sku=$sku'),
        headers: {HttpHeaders.authorizationHeader: _authHeader},
      );

      if (response.statusCode == 200) {
        final List products = jsonDecode(response.body);
        if (products.isNotEmpty) {
          return products.first;
        }
      }
    } catch (e) {
      print('Error finding product by SKU: $e');
    }
    return null;
  }

  Future<List<dynamic>> searchProducts(String query) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/wp-json/wc/v3/products?search=$query'),
        headers: {HttpHeaders.authorizationHeader: _authHeader},
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print('Error searching products: $e');
    }
    return [];
  }

  Future<bool> updateProduct(int id, Map<String, dynamic> data) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/wp-json/wc/v3/products/$id'),
        headers: {
          HttpHeaders.authorizationHeader: _authHeader,
          HttpHeaders.contentTypeHeader: 'application/json',
        },
        body: jsonEncode(data),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Error updating product: $e');
      return false;
    }
  }

  Future<bool> createProduct({
    required String name,
    required String price,
    required String stockQuantity,
    required String sku,
  }) async {
    final url = Uri.parse('$baseUrl/wp-json/wc/v3/products');
    
    try {
      final response = await http.post(
        url,
        headers: {
          HttpHeaders.authorizationHeader: _authHeader,
          HttpHeaders.contentTypeHeader: 'application/json',
        },
        body: jsonEncode({
          'name': name,
          'type': 'simple',
          'regular_price': price,
          'manage_stock': true,
          'stock_quantity': int.tryParse(stockQuantity) ?? 0,
          'sku': sku,
          'status': 'publish', 
        }),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return true;
      } else {
        print('Failed to create product. Status: ${response.statusCode}');
        print('Body: ${response.body}');
        return false;
      }
    } catch (e) {
      print('Error creating product: $e');
      return false;
    }
  }
}
