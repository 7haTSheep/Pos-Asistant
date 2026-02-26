import 'package:flutter/material.dart';
import 'barcode_scanner.dart';
import '../services/manifest_service.dart';

class ManifestVerificationScreen extends StatefulWidget {
  const ManifestVerificationScreen({super.key});

  @override
  State<ManifestVerificationScreen> createState() => _ManifestVerificationScreenState();
}

class _ManifestVerificationScreenState extends State<ManifestVerificationScreen> {
  final _service = ManifestService();
  List<Map<String, dynamic>> _manifestEntries = [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() => _loading = true);
    final entries = await _service.listOpen();
    setState(() {
      _manifestEntries = entries;
      _loading = false;
    });
  }

  Future<void> _scanAndVerify() async {
    final scan = await Navigator.of(context).push<String>(
      MaterialPageRoute(builder: (_) => const BarcodeScannerScreen()),
    );
    if (scan == null || scan.isEmpty) {
      return;
    }
    final match = _manifestEntries.firstWhere(
      (item) => item['sku'] == scan,
      orElse: () => <String, dynamic>{},
    );
    if (match.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No manifest entry for $scan')),
      );
      return;
    }
    final manifestId = match['id'] as int;
    final success = await _service.verify(manifestId);
    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Verified ${match['sku']} (ID $manifestId)')),
      );
      await _refresh();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Verification failed')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Storefront Check-off'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refresh,
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            ElevatedButton.icon(
              onPressed: _scanAndVerify,
              icon: const Icon(Icons.qr_code_scanner),
              label: const Text('Scan incoming SKU'),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _manifestEntries.isEmpty
                      ? const Center(child: Text('No items currently in-transit.'))
                      : ListView.builder(
                          itemCount: _manifestEntries.length,
                          itemBuilder: (context, index) {
                            final entry = _manifestEntries[index];
                            return Card(
                              margin: const EdgeInsets.symmetric(vertical: 6),
                              child: ListTile(
                                title: Text('${entry['sku']} (${entry['quantity']})'),
                                subtitle: Text(
                                  'Slot: ${entry['warehouse_slot']} · Dest: ${entry['destination']}',
                                ),
                                trailing: Text('#${entry['id']}'),
                              ),
                            );
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }
}
