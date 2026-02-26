import 'package:flutter/material.dart';
import 'barcode_scanner.dart';
import '../services/manifest_service.dart';

class ManifestDispatchScreen extends StatefulWidget {
  const ManifestDispatchScreen({super.key});

  @override
  State<ManifestDispatchScreen> createState() => _ManifestDispatchScreenState();
}

class _ManifestDispatchScreenState extends State<ManifestDispatchScreen> {
  final _skuController = TextEditingController();
  final _destinationController = TextEditingController(text: 'Storefront');
  final _quantityController = TextEditingController(text: '1');
  final _rowController = TextEditingController(text: '1');
  final _colController = TextEditingController(text: '1');
  final _layerController = TextEditingController(text: '1');
  final _service = ManifestService();
  bool _isSubmitting = false;

  @override
  void dispose() {
    _skuController.dispose();
    _destinationController.dispose();
    _quantityController.dispose();
    _rowController.dispose();
    _colController.dispose();
    _layerController.dispose();
    super.dispose();
  }

  Future<void> _scanSku() async {
    final scan = await Navigator.of(context).push<String>(
      MaterialPageRoute(builder: (_) => const BarcodeScannerScreen()),
    );
    if (scan != null && scan.isNotEmpty) {
      setState(() {
        _skuController.text = scan;
      });
    }
  }

  Future<void> _submitDispatch() async {
    if (_skuController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('SKU is required for dispatch')),
      );
      return;
    }
    final slot =
        'R${_rowController.text}C${_colController.text}L${_layerController.text}';
    final quantity = int.tryParse(_quantityController.text) ?? 1;
    setState(() => _isSubmitting = true);
    final result = await _service.dispatch(
      sku: _skuController.text.trim(),
      quantity: quantity,
      slot: slot,
      destination: _destinationController.text.trim(),
    );

    if (result != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Dispatch marked as in-transit')),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to create manifest entry')),
      );
    }
    setState(() => _isSubmitting = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dispatch to Storefront')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _skuController,
              decoration: InputDecoration(
                labelText: 'SKU',
                prefixIcon: const Icon(Icons.inventory_2),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.qr_code_scanner),
                  onPressed: _scanSku,
                ),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _quantityController,
              decoration: const InputDecoration(
                labelText: 'Quantity',
                prefixIcon: Icon(Icons.format_list_numbered),
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _destinationController,
              decoration: const InputDecoration(
                labelText: 'Destination',
                prefixIcon: Icon(Icons.store),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _rowController,
                    decoration: const InputDecoration(labelText: 'Row'),
                    keyboardType: TextInputType.number,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _colController,
                    decoration: const InputDecoration(labelText: 'Col'),
                    keyboardType: TextInputType.number,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _layerController,
                    decoration: const InputDecoration(labelText: 'Layer'),
                    keyboardType: TextInputType.number,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isSubmitting ? null : _submitDispatch,
              child: _isSubmitting
                  ? const CircularProgressIndicator()
                  : const Text('Mark In-Transit'),
            ),
          ],
        ),
      ),
    );
  }
}
