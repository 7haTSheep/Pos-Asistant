import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'services/woocommerce_service.dart';
import 'screens/barcode_scanner.dart';
import 'dart:math';
import 'package:barcode_widget/barcode_widget.dart';
import 'screens/automation_screen.dart';
import 'services/open_food_facts_service.dart';
import 'screens/text_recognizer_screen.dart';

void main() {
  runApp(const ProviderScope(child: MyApp()));
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Inventory Manager',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: const AddItemScreen(),
    );
  }
}


class AddItemScreen extends ConsumerStatefulWidget {
  const AddItemScreen({super.key});

  @override
  ConsumerState<AddItemScreen> createState() => _AddItemScreenState();
}

class _AddItemScreenState extends ConsumerState<AddItemScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _priceController = TextEditingController();
  final _stockController = TextEditingController();
  final _skuController = TextEditingController();
  bool _isLoading = false;

  void _generateSku() {
    // Determine prefix based on name if possible
    String prefix = 'GEN';
    if (_nameController.text.isNotEmpty) {
      prefix = _nameController.text.substring(0, min(3, _nameController.text.length)).toUpperCase();
    }
    final random = Random().nextInt(999999).toString().padLeft(6, '0');
    setState(() {
      _skuController.text = '$prefix-$random';
    });
  }

  void _showBarcodeDialog(String sku, String name) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Product Added'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Here is the generated barcode for this item:'),
            const SizedBox(height: 20),
            BarcodeWidget(
              barcode: Barcode.code128(),
              data: sku,
              width: 200,
              height: 80,
            ),
            const SizedBox(height: 10),
            Text(sku, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 5),
            Text(name),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Future<void> _lookupProduct(String sku) async {
    if (sku.isEmpty) return;
    
    setState(() => _isLoading = true);
    final data = await OpenFoodFactsService().searchProduct(sku);
    
    if (mounted) {
       setState(() => _isLoading = false);
       if (data != null && data['name'] != null && data['name'].toString().isNotEmpty) {
         _nameController.text = data['name'];
         ScaffoldMessenger.of(context).showSnackBar(
           SnackBar(content: Text('Found: ${data['name']}')),
         );
       } else {
         ScaffoldMessenger.of(context).showSnackBar(
           const SnackBar(content: Text('Product not found in global db.')),
         );
       }
    }
  }

  Future<void> _submitProduct() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      
      final name = _nameController.text;
      final sku = _skuController.text;

      final success = await WooCommerceService().createProduct(
        name: name,
        price: _priceController.text,
        stockQuantity: _stockController.text,
        sku: sku,
      );
      
      if (mounted) {
        if (success) {
          // ScaffodMessenger/SnackBar removed in favor of Dialog for success
          // Clear forms but keep details for dialog? No, clear logic is separate
          
          _showBarcodeDialog(sku, name);

          _nameController.clear();
          _priceController.clear();
          _stockController.clear();
          _skuController.clear();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Failed to add product. Check API config.'),
              backgroundColor: Colors.red,
            ),
          );
        }
        
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _priceController.dispose();
    _stockController.dispose();
    _skuController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Add New Inventory Item'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
             DrawerHeader(
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primary,
              ),
              child: const Text('Menu', style: TextStyle(color: Colors.white, fontSize: 24)),
            ),
            ListTile(
              leading: const Icon(Icons.add_box),
              title: const Text('Add Item'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.auto_mode),
              title: const Text('Automation'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const AutomationScreen()),
                );
              },
            ),
          ],
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Enter Item Details',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 20),
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Product Name',
                  hintText: 'e.g. Blue Denim Jacket',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.shopping_bag),
                ),
                validator: (value) =>
                    value == null || value.isEmpty ? 'Please enter a product name' : null,
              ),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  icon: const Icon(Icons.document_scanner),
                  label: const Text("Scan Label Text"),
                  onPressed: () async {
                    final text = await Navigator.push<String>(
                      context,
                      MaterialPageRoute(builder: (_) => const TextRecognizerScreen()),
                    );
                    if (text != null && text.isNotEmpty) {
                      _nameController.text = text;
                      _generateSku(); // Auto-generate SKU if using name? Optional.
                    }
                  },
                ),
              ),
              const SizedBox(height: 16),
                // SKU Field with Scan Button
                TextFormField(
                  controller: _skuController,
                  decoration: InputDecoration(
                    labelText: 'SKU (Scan, type, or generate)',
                    border: const OutlineInputBorder(),
                    prefixIcon: const Icon(Icons.qr_code),
                    suffixIcon: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Tooltip(
                          message: "Lookup in Global DB",
                          child: IconButton(
                            icon: const Icon(Icons.public),
                            onPressed: () => _lookupProduct(_skuController.text),
                          ),
                        ),
                        Tooltip(
                          message: "Generate Digital Barcode",
                          child: IconButton(
                            icon: const Icon(Icons.autorenew),
                            onPressed: _generateSku,
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.camera_alt),
                          onPressed: () async {
                            final scanned = await Navigator.of(context).push<String>(
                              MaterialPageRoute(builder: (_) => const BarcodeScannerScreen()),
                            );
                            if (scanned != null && scanned.isNotEmpty) {
                              _skuController.text = scanned;
                              _lookupProduct(scanned); // Auto-lookup
                            }
                          },
                        ),
                      ],
                    ),
                  ),
                  validator: (value) => 
                     value == null || value.isEmpty ? 'SKU is required for barcode' : null,
                ),
                const SizedBox(height: 16),
                Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _priceController,
                      decoration: const InputDecoration(
                        labelText: 'Price',
                        prefixText: '\$',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.attach_money),
                      ),
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      validator: (value) =>
                          value == null || value.isEmpty ? 'Enter price' : null,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: TextFormField(
                      controller: _stockController,
                      decoration: const InputDecoration(
                        labelText: 'Stock Qty',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.inventory),
                      ),
                      keyboardType: TextInputType.number,
                      validator: (value) =>
                          value == null || value.isEmpty ? 'Enter stock' : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              SizedBox(
                height: 56,
                child: FilledButton.icon(
                  onPressed: _isLoading ? null : _submitProduct,
                  icon: _isLoading
                      ? const SizedBox.shrink()
                      : const Icon(Icons.cloud_upload),
                  label: _isLoading
                      ? const SizedBox(
                          height: 24,
                          width: 24,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Text('Add Item to Database', style: TextStyle(fontSize: 18)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
