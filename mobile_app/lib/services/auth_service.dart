
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'user_session.dart';

class AuthService {
  // Use 10.0.2.2 for Android Emulator to access localhost of host machine
  // Use actual IP if on physical device
  static const String baseUrl = 'http://10.0.2.2:8000'; 
  
  Future<bool> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'password': password,
        }),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        UserSession().setUser(data['user_id'], data['username']);
        return true;
      }
      return false;
    } catch (e) {
      print('Login error: $e');
      return false;
    }
  }
  
  Future<bool> register(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'password': password,
        }),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        UserSession().setUser(data['user_id'], username);
        return true;
      }
      return false;
    } catch (e) {
      print('Register error: $e');
      return false;
    }
  }
  
  void logout() {
    UserSession().clear();
  }

  Future<bool> shareItem({
    required int userId,
    required String name,
    required String imagePath,
    String? sku,
  }) async {
    try {
      final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/share-item'));
      
      request.fields['user_id'] = userId.toString();
      request.fields['name'] = name;
      if (sku != null) request.fields['sku'] = sku;
      
      request.files.add(await http.MultipartFile.fromPath('image', imagePath));
      
      final response = await request.send();
      
      if (response.statusCode == 200) {
        return true;
      }
      return false;
    } catch (e) {
      print('Share error: $e');
      return false;
    }
  }
}

