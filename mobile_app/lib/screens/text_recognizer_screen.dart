import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_picker/image_picker.dart';

class TextRecognizerScreen extends StatefulWidget {
  const TextRecognizerScreen({super.key});

  @override
  State<TextRecognizerScreen> createState() => _TextRecognizerScreenState();
}

class _TextRecognizerScreenState extends State<TextRecognizerScreen> {
  final _textRecognizer = TextRecognizer(script: TextRecognitionScript.latin);
  final _picker = ImagePicker();
  
  File? _imageFile;
  RecognizedText? _recognizedText;
  bool _isBusy = false;

  @override
  void dispose() {
    _textRecognizer.close();
    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final pickedFile = await _picker.pickImage(source: source);
      if (pickedFile != null) {
        setState(() {
          _imageFile = File(pickedFile.path);
          _recognizedText = null;
        });
        _processImage(_imageFile!);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error picking image: $e')),
      );
    }
  }

  Future<void> _processImage(File image) async {
    setState(() => _isBusy = true);
    try {
      final inputImage = InputImage.fromFile(image);
      final recognized = await _textRecognizer.processImage(inputImage);
      setState(() {
        _recognizedText = recognized;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
         SnackBar(content: Text('Error recognizing text: $e')),
      );
    }
    setState(() => _isBusy = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan Product Label'),
        actions: [
          IconButton(
            icon: const Icon(Icons.photo_library),
            onPressed: () => _pickImage(ImageSource.gallery),
          ),
          IconButton(
            icon: const Icon(Icons.camera_alt),
            onPressed: () => _pickImage(ImageSource.camera),
          ),
        ],
      ),
      body: _isBusy
          ? const Center(child: CircularProgressIndicator())
          : _imageFile == null
              ? const Center(child: Text('Take a photo of the product label'))
              : Column(
                  children: [
                    SizedBox(
                      height: 200,
                      width: double.infinity,
                      child: Image.file(_imageFile!, fit: BoxFit.cover),
                    ),
                    const Divider(),
                    const Padding(
                      padding: EdgeInsets.all(8.0),
                      child: Text(
                        'Tap the text that matches the product name:',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                    Expanded(
                      child: _recognizedText == null || _recognizedText!.blocks.isEmpty
                          ? const Center(child: Text('No text found.'))
                          : ListView.builder(
                              itemCount: _recognizedText!.blocks.length,
                              itemBuilder: (context, index) {
                                final block = _recognizedText!.blocks[index];
                                return ListTile(
                                  title: Text(block.text),
                                  trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                                  onTap: () {
                                    Navigator.pop(context, block.text);
                                  },
                                );
                              },
                            ),
                    ),
                  ],
                ),
    );
  }
}
