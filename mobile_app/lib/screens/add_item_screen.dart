import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:barcode_widget/barcode_widget.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:math';

import '../services/woocommerce_service.dart';
import '../services/open_food_facts_service.dart';
import '../services/local_database_service.dart';
import '../services/user_session.dart';
import 'barcode_scanner.dart';
import 'text_recognizer_screen.dart';

import 'smart_scanner_screen.dart';
import 'inventory_import_screen.dart';
import 'local_products_screen.dart';
import 'auth_screen.dart';
import '../services/auth_service.dart'; // For logout

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
  XFile? _imageFile;
  bool _shareToGlobal = false;

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

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.camera);
    if (pickedFile != null) {
      setState(() {
        _imageFile = pickedFile;
      });
    }
  }

  Future<void> _submitProduct() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      
      final name = _nameController.text;
      final sku = _skuController.text;
      final price = _priceController.text;
      final stock = int.tryParse(_stockController.text) ?? 0;

      // 1. Save to WooCommerce (Existing)
      final success = await WooCommerceService().createProduct(
        name: name,
        price: price,
        stockQuantity: _stockController.text,
        sku: sku,
      );
      
      if (mounted) {
        if (success) {
           // 2. Save to Local DB (Per Profile)
           final localId = await LocalDatabaseService.instance.addProduct(
             name: name,
             sku: sku,
             price: price,
             stockQuantity: stock,
             image: _imageFile,
           );

           // 3. Share to Global DB if requested
           if (_shareToGlobal && _imageFile != null && UserSession().isLoggedIn) {
             final imagePath = (await LocalDatabaseService.instance.getProductById(localId!))?.imagePath;
             if (imagePath != null) {
                await AuthService().shareItem(
                  userId: UserSession().userId!,
                  name: name,
                  sku: sku,
                  imagePath: imagePath, // Use the locally saved path
                );
             }
           }

          _showBarcodeDialog(sku, name);

          _nameController.clear();
          _priceController.clear();
          _stockController.clear();
          _skuController.clear();
          setState(() {
            _imageFile = null;
            _shareToGlobal = false;
          });
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Failed to add product to WooCommerce.'),
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
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
               AuthService().logout();
               Navigator.pushReplacement(
                 context,
                 MaterialPageRoute(builder: (_) => const AuthScreen()),
               );
            },
          ),
        ],
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
              leading: const Icon(Icons.qr_code_scanner),
              title: const Text('Smart Scanner'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const SmartScannerScreen()),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.file_upload),
              title: const Text('Import Inventory'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const InventoryImportScreen()),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.dataset),
              title: const Text('Local Products'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const LocalProductsScreen()),
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
              
              // Image Picker UI
              GestureDetector(
                onTap: _pickImage,
                child: Container(
                  height: 150,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey),
                  ),
                  child: _imageFile != null
                      ? ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.file(
                            File(_imageFile!.path),
                            fit: BoxFit.cover,
                          ),
                        )
                      : const Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.camera_alt, size: 50, color: Colors.grey),
                            Text('Tap to take picture'),
                          ],
                        ),
                ),
              ),
              const SizedBox(height: 10),
              
              // Share Checkbox
              CheckboxListTile(
                title: const Text("Share to Global Database?"),
                subtitle: const Text("Help others identify this item"),
                value: _shareToGlobal,
                onChanged: (val) => setState(() => _shareToGlobal = val ?? false),
              ),
              const SizedBox(height: 10),

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
