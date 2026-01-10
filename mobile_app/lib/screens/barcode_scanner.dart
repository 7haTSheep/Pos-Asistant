import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class BarcodeScannerScreen extends StatefulWidget {
  const BarcodeScannerScreen({super.key});

  @override
  State<BarcodeScannerScreen> createState() => _BarcodeScannerScreenState();
}

class _BarcodeScannerScreenState extends State<BarcodeScannerScreen> {
  final MobileScannerController _controller = MobileScannerController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan Barcode'),
      ),
      body: MobileScanner(
        controller: _controller,
        allowDuplicates: false,
        onDetect: (barcode, args) {
          final String? rawValue = barcode.rawValue;
          if (rawValue != null && rawValue.isNotEmpty) {
            // Return the scanned code to previous screen
            Navigator.of(context).pop(rawValue);
          }
        },
      ),
    );
  }
}
