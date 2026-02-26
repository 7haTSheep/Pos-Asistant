import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../services/warehouse_scan_service.dart';

class WarehouseScanScreen extends StatefulWidget {
  const WarehouseScanScreen({super.key});

  @override
  State<WarehouseScanScreen> createState() => _WarehouseScanScreenState();
}

class _WarehouseScanScreenState extends State<WarehouseScanScreen> {
  final WarehouseScanService _scanService = WarehouseScanService();
  final MobileScannerController _scannerController = MobileScannerController(
    detectionSpeed: DetectionSpeed.noDuplicates,
  );

  final TextEditingController _objectIdController = TextEditingController();
  final TextEditingController _floorNameController = TextEditingController();
  final TextEditingController _rowController = TextEditingController(text: '1');
  final TextEditingController _colController = TextEditingController(text: '1');
  final TextEditingController _layerController = TextEditingController(text: '1');
  final TextEditingController _qtyController = TextEditingController(text: '1');

  bool _isSubmitting = false;
  bool _scannerEnabled = true;
  String _status = 'Ready';
  final List<String> _recentLogs = [];

  @override
  void dispose() {
    _scannerController.dispose();
    _objectIdController.dispose();
    _floorNameController.dispose();
    _rowController.dispose();
    _colController.dispose();
    _layerController.dispose();
    _qtyController.dispose();
    super.dispose();
  }

  int _toInt(String value, {int fallback = 1}) {
    final parsed = int.tryParse(value.trim()) ?? fallback;
    return parsed < 1 ? 1 : parsed;
  }

  void _pushLog(String message) {
    setState(() {
      _recentLogs.insert(0, message);
      if (_recentLogs.length > 8) {
        _recentLogs.removeLast();
      }
    });
  }

  Future<void> _submitScan(String barcode) async {
    final objectId = _objectIdController.text.trim();
    if (objectId.isEmpty) {
      setState(() {
        _status = 'Set object ID first';
      });
      return;
    }

    setState(() {
      _isSubmitting = true;
      _status = 'Submitting $barcode...';
    });

    final result = await _scanService.submitScanEvent(
      barcode: barcode,
      objectId: objectId,
      row: _toInt(_rowController.text),
      col: _toInt(_colController.text),
      layer: _toInt(_layerController.text),
      quantity: _toInt(_qtyController.text),
      floorName: _floorNameController.text.trim().isEmpty
          ? null
          : _floorNameController.text.trim(),
    );

    if (!mounted) return;

    if (result != null) {
      final scanId = result['id'];
      final slot = result['slot'];
      final slotLabel = slot is Map
          ? 'R${slot['row']} C${slot['col']} L${slot['layer']}'
          : 'slot';
      _pushLog('#$scanId  $barcode -> $slotLabel');
      setState(() {
        _status = 'Submitted scan #$scanId';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Scan sent: $barcode')),
      );
    } else {
      setState(() {
        _status = 'Failed to submit scan';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to submit scan event')),
      );
    }

    setState(() {
      _isSubmitting = false;
    });
  }

  void _onDetect(BarcodeCapture capture) {
    if (!_scannerEnabled || _isSubmitting) return;

    for (final barcode in capture.barcodes) {
      final raw = barcode.rawValue;
      if (raw != null && raw.isNotEmpty) {
        _submitScan(raw);
        break;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Warehouse Scan'),
      ),
      body: Column(
        children: [
          Expanded(
            flex: 5,
            child: Stack(
              children: [
                MobileScanner(
                  controller: _scannerController,
                  onDetect: _onDetect,
                ),
                Positioned(
                  top: 12,
                  left: 12,
                  right: 12,
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.65),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      _status,
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            flex: 4,
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(12),
              child: Column(
                children: [
                  TextField(
                    controller: _objectIdController,
                    decoration: const InputDecoration(
                      labelText: 'Object ID (required)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _floorNameController,
                    decoration: const InputDecoration(
                      labelText: 'Floor name (optional)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _rowController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'Row', border: OutlineInputBorder()),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextField(
                          controller: _colController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'Col', border: OutlineInputBorder()),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextField(
                          controller: _layerController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'Layer', border: OutlineInputBorder()),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextField(
                          controller: _qtyController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'Qty', border: OutlineInputBorder()),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  SwitchListTile(
                    title: const Text('Enable live scanning'),
                    value: _scannerEnabled,
                    onChanged: (value) => setState(() => _scannerEnabled = value),
                    contentPadding: EdgeInsets.zero,
                  ),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Recent scans', style: Theme.of(context).textTheme.titleSmall),
                  ),
                  const SizedBox(height: 6),
                  if (_recentLogs.isEmpty)
                    const Align(
                      alignment: Alignment.centerLeft,
                      child: Text('No scans yet'),
                    ),
                  ..._recentLogs.map(
                    (line) => Align(
                      alignment: Alignment.centerLeft,
                      child: Text(line, style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
