import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import '../config.dart';

class InventoryImportScreen extends StatefulWidget {
  const InventoryImportScreen({super.key});

  @override
  State<InventoryImportScreen> createState() => _InventoryImportScreenState();
}

class _InventoryImportScreenState extends State<InventoryImportScreen> {
  bool _isUploading = false;
  String? _uploadStatus;

  Future<void> _pickAndUploadFile() async {
    setState(() {
      _isUploading = true;
      _uploadStatus = "Picking file...";
    });

    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['csv', 'xlsx', 'xls'],
      );

      if (result != null) {
        PlatformFile file = result.files.first;
        
        setState(() => _uploadStatus = "Uploading ${file.name}...");

        // Prepare upload
        var request = http.MultipartRequest(
          'POST',
          Uri.parse('${AppConfig.automationApiUrl}/import-inventory'),
        );

        if (file.path != null) {
             request.files.add(
                await http.MultipartFile.fromPath('file', file.path!)
             );
        } else {
            // Web support or if path is null (shouldn't happen on mobile usually)
             request.files.add(
                http.MultipartFile.fromBytes('file', file.bytes!, filename: file.name)
             );
        }

        var response = await request.send();
        var responseBody = await response.stream.bytesToString();

        if (response.statusCode == 200) {
          setState(() => _uploadStatus = "Success! \n$responseBody");
        } else {
          setState(() => _uploadStatus = "Failed: ${response.statusCode}\n$responseBody");
        }
      } else {
        setState(() => _uploadStatus = "Cancelled");
      }
    } catch (e) {
      setState(() => _uploadStatus = "Error: $e");
    } finally {
      setState(() => _isUploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Import Inventory')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.file_upload, size: 80, color: Colors.blue),
              const SizedBox(height: 20),
              const Text(
                'Upload CSV or Excel file to update inventory.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16),
              ),
              const SizedBox(height: 10),
              const Text(
                'Columns needed: name, price, stock, sku',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
              const SizedBox(height: 30),
              if (_isUploading)
                const CircularProgressIndicator()
              else
                ElevatedButton(
                  onPressed: _pickAndUploadFile,
                  child: const Text('Pick File'),
                ),
              const SizedBox(height: 20),
              if (_uploadStatus != null)
                Text(_uploadStatus!, textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}
