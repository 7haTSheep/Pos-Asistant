import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_native_timezone/flutter_native_timezone.dart';
import 'package:timezone/data/latest_all.dart' as tz_data;
import 'package:timezone/timezone.dart' as tz;

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;

  final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  NotificationService._internal();

  Future<void> init() async {
    if (_initialized) return;
    tz_data.initializeTimeZones();
    final String timezone = await FlutterNativeTimezone.getLocalTimezone();
    tz.setLocalLocation(tz.getLocation(timezone));

    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const ios = DarwinInitializationSettings();
    await _plugin.initialize(
      const InitializationSettings(android: android, iOS: ios),
    );

    _initialized = true;
  }

  Future<void> scheduleExpiryReminder({
    required int id,
    required String title,
    required String body,
    required DateTime scheduledDate,
  }) async {
    if (!_initialized) {
      await init();
    }

    final tz.TZDateTime scheduled = tz.TZDateTime.from(scheduledDate, tz.local);
    if (scheduled.isBefore(tz.TZDateTime.now(tz.local))) {
      return;
    }

    const androidDetails = AndroidNotificationDetails(
      'expiry_alerts',
      'Expiry Alerts',
      channelDescription: 'Notifications for expiring inventory',
      importance: Importance.max,
      priority: Priority.high,
    );
    const iosDetails = DarwinNotificationDetails();
    final details = NotificationDetails(android: androidDetails, iOS: iosDetails);

    await _plugin.zonedSchedule(
      id,
      title,
      body,
      scheduled,
      details,
      androidAllowWhileIdle: true,
      uiLocalNotificationDateInterpretation: UILocalNotificationDateInterpretation.absoluteTime,
    );
  }

  Future<void> scheduleExpiryReminders({
    required String sku,
    required String name,
    required DateTime expiryDate,
    required bool isMeat,
  }) async {
    final now = DateTime.now();
    final List<DateTime> reminders = [];

    if (isMeat) {
      final highPriority = expiryDate.subtract(const Duration(hours: 48));
      if (highPriority.isAfter(now)) {
        reminders.add(highPriority);
      }
    } else {
      final monthLead = expiryDate.subtract(const Duration(days: 30));
      final weekLead = expiryDate.subtract(const Duration(days: 7));
      if (monthLead.isAfter(now)) reminders.add(monthLead);
      if (weekLead.isAfter(now)) reminders.add(weekLead);
    }

    for (var i = 0; i < reminders.length; i++) {
      final scheduled = reminders[i];
      final id = sku.hashCode ^ scheduled.microsecondsSinceEpoch ^ i;
      await scheduleExpiryReminder(
        id: id.abs(),
        title: 'Expiry alert: $name',
        body: 'SKU $sku expires on ${expiryDate.toLocal().toString().split(" ").first}',
        scheduledDate: scheduled,
      );
    }
  }
}
