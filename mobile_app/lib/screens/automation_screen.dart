import 'package:flutter/material.dart';
import 'dart:async';
import '../services/automation_service.dart';

class AutomationScreen extends StatefulWidget {
  const AutomationScreen({super.key});

  @override
  State<AutomationScreen> createState() => _AutomationScreenState();
}

class _AutomationScreenState extends State<AutomationScreen> {
  final _service = AutomationService();
  bool _isLoading = false;
  bool _isActive = false;
  int _remainingSeconds = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _fetchStatus();
    _startLocalTimer();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _startLocalTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_isActive && _remainingSeconds > 0) {
        setState(() => _remainingSeconds--);
      } else if (_isActive && _remainingSeconds <= 0) {
        _fetchStatus(); // Re-sync when timer hits zero
      }
    });
  }

  Future<void> _fetchStatus() async {
    final status = await _service.getStatus();
    if (mounted) {
      setState(() => {
            _isActive = status['active'] ?? false,
            _remainingSeconds = status['remaining_seconds'] ?? 0,
          });
    }
  }

  Future<void> _toggleSession() async {
    setState(() => _isLoading = true);
    bool success;
    if (_isActive) {
      success = await _service.stopSession();
    } else {
      success = await _service.startSession();
    }

    if (success) {
      await _fetchStatus();
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to change session state')),
        );
      }
    }
    setState(() => _isLoading = false);
  }

  String _formatTime(int seconds) {
    final m = seconds ~/ 60;
    final s = seconds % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Automation Control'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              _isActive ? Icons.autorenew : Icons.power_settings_new,
              size: 100,
              color: _isActive ? Colors.green : Colors.grey,
            ),
            const SizedBox(height: 20),
            Text(
              _isActive ? 'Session Active' : 'Session Idle',
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            if (_isActive) ...[
              const SizedBox(height: 10),
              Text(
                'Remaining Time: ${_formatTime(_remainingSeconds)}',
                style: const TextStyle(fontSize: 18),
              ),
            ],
            const SizedBox(height: 40),
            SizedBox(
              width: 200,
              height: 50,
              child: FilledButton(
                onPressed: _isLoading ? null : _toggleSession,
                style: FilledButton.styleFrom(
                  backgroundColor: _isActive ? Colors.red : Colors.green,
                ),
                child: _isLoading
                    ? const SizedBox(
                        height: 24, width: 24, child: CircularProgressIndicator(color: Colors.white))
                    : Text(
                        _isActive ? 'Stop Session' : 'Start 40m Session',
                        style: const TextStyle(fontSize: 18),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
