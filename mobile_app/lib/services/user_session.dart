
class UserSession {
  static final UserSession _instance = UserSession._internal();
  
  factory UserSession() {
    return _instance;
  }
  
  UserSession._internal();
  
  int? userId;
  String? username;
  
  bool get isLoggedIn => userId != null;
  
  void clear() {
    userId = null;
    username = null;
  }
  
  void setUser(int id, String name) {
    userId = id;
    username = name;
  }
}
