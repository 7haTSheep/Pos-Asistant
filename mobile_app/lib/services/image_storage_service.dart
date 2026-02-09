import 'dart:io';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:image/image.dart' as img;
import 'package:path_provider/path_provider.dart';
import 'package:image_picker/image_picker.dart';

/// Service for handling product image storage and processing
class ImageStorageService {
  static const int thumbnailSize = 200; // Max dimension for thumbnails
  static const String imageFolder = 'product_images';

  /// Get the directory for storing product images
  Future<Directory> _getImageDirectory() async {
    final appDir = await getApplicationDocumentsDirectory();
    final imageDir = Directory('${appDir.path}/$imageFolder');
    if (!await imageDir.exists()) {
      await imageDir.create(recursive: true);
    }
    return imageDir;
  }

  /// Save a product image from XFile, compress it, and return the path
  /// Returns the saved file path or null if failed
  Future<String?> saveProductImage(XFile imageFile, int productId) async {
    try {
      final imageDir = await _getImageDirectory();
      final bytes = await imageFile.readAsBytes();
      
      // Decode and compress the image
      final originalImage = img.decodeImage(bytes);
      if (originalImage == null) return null;

      // Resize to thumbnail size (maintaining aspect ratio)
      final thumbnail = img.copyResize(
        originalImage,
        width: originalImage.width > originalImage.height ? thumbnailSize : null,
        height: originalImage.height >= originalImage.width ? thumbnailSize : null,
      );

      // Encode as JPEG for smaller file size
      final compressedBytes = img.encodeJpg(thumbnail, quality: 85);
      
      // Save to file
      final fileName = 'product_$productId.jpg';
      final filePath = '${imageDir.path}/$fileName';
      final file = File(filePath);
      await file.writeAsBytes(compressedBytes);
      
      return filePath;
    } catch (e) {
      print('Error saving product image: $e');
      return null;
    }
  }

  /// Save image from bytes (for cases where we already have the bytes)
  Future<String?> saveProductImageFromBytes(Uint8List bytes, int productId) async {
    try {
      final imageDir = await _getImageDirectory();
      
      // Decode and compress the image
      final originalImage = img.decodeImage(bytes);
      if (originalImage == null) return null;

      // Resize to thumbnail size
      final thumbnail = img.copyResize(
        originalImage,
        width: originalImage.width > originalImage.height ? thumbnailSize : null,
        height: originalImage.height >= originalImage.width ? thumbnailSize : null,
      );

      // Encode as JPEG
      final compressedBytes = img.encodeJpg(thumbnail, quality: 85);
      
      // Save to file
      final fileName = 'product_$productId.jpg';
      final filePath = '${imageDir.path}/$fileName';
      final file = File(filePath);
      await file.writeAsBytes(compressedBytes);
      
      return filePath;
    } catch (e) {
      print('Error saving product image from bytes: $e');
      return null;
    }
  }

  /// Get the image file for a product
  Future<File?> getProductImage(String imagePath) async {
    try {
      final file = File(imagePath);
      if (await file.exists()) {
        return file;
      }
      return null;
    } catch (e) {
      print('Error getting product image: $e');
      return null;
    }
  }

  /// Compute a perceptual hash for an image (for similarity matching)
  /// Uses average hash algorithm for simplicity
  Future<String?> computeImageHash(String imagePath) async {
    try {
      final file = File(imagePath);
      if (!await file.exists()) return null;

      final bytes = await file.readAsBytes();
      final originalImage = img.decodeImage(bytes);
      if (originalImage == null) return null;

      // Resize to 8x8 for hash computation
      final resized = img.copyResize(originalImage, width: 8, height: 8);
      
      // Convert to grayscale
      final grayscale = img.grayscale(resized);
      
      // Calculate average pixel value
      int total = 0;
      for (int y = 0; y < 8; y++) {
        for (int x = 0; x < 8; x++) {
          final pixel = grayscale.getPixel(x, y);
          total += pixel.r.toInt(); // Grayscale so R=G=B
        }
      }
      final average = total ~/ 64;
      
      // Build hash: 1 if pixel > average, 0 otherwise
      StringBuffer hash = StringBuffer();
      for (int y = 0; y < 8; y++) {
        for (int x = 0; x < 8; x++) {
          final pixel = grayscale.getPixel(x, y);
          hash.write(pixel.r.toInt() > average ? '1' : '0');
        }
      }
      
      // Convert binary string to hex for compact storage
      final binaryString = hash.toString();
      final bigInt = BigInt.parse(binaryString, radix: 2);
      return bigInt.toRadixString(16).padLeft(16, '0');
    } catch (e) {
      print('Error computing image hash: $e');
      return null;
    }
  }

  /// Compute hash directly from XFile
  Future<String?> computeImageHashFromFile(XFile imageFile) async {
    try {
      final bytes = await imageFile.readAsBytes();
      final originalImage = img.decodeImage(bytes);
      if (originalImage == null) return null;

      // Resize to 8x8 for hash computation
      final resized = img.copyResize(originalImage, width: 8, height: 8);
      
      // Convert to grayscale
      final grayscale = img.grayscale(resized);
      
      // Calculate average pixel value
      int total = 0;
      for (int y = 0; y < 8; y++) {
        for (int x = 0; x < 8; x++) {
          final pixel = grayscale.getPixel(x, y);
          total += pixel.r.toInt();
        }
      }
      final average = total ~/ 64;
      
      // Build hash
      StringBuffer hash = StringBuffer();
      for (int y = 0; y < 8; y++) {
        for (int x = 0; x < 8; x++) {
          final pixel = grayscale.getPixel(x, y);
          hash.write(pixel.r.toInt() > average ? '1' : '0');
        }
      }
      
      final binaryString = hash.toString();
      final bigInt = BigInt.parse(binaryString, radix: 2);
      return bigInt.toRadixString(16).padLeft(16, '0');
    } catch (e) {
      print('Error computing image hash from file: $e');
      return null;
    }
  }

  /// Calculate Hamming distance between two hashes (lower = more similar)
  int hammingDistance(String hash1, String hash2) {
    if (hash1.length != hash2.length) return -1;
    
    final int1 = BigInt.parse(hash1, radix: 16);
    final int2 = BigInt.parse(hash2, radix: 16);
    final xor = int1 ^ int2;
    
    // Count 1 bits in XOR result
    int distance = 0;
    var temp = xor;
    while (temp > BigInt.zero) {
      distance += (temp & BigInt.one).toInt();
      temp = temp >> 1;
    }
    return distance;
  }

  /// Check if two images are similar (Hamming distance <= threshold)
  bool areImagesSimilar(String hash1, String hash2, {int threshold = 10}) {
    final distance = hammingDistance(hash1, hash2);
    return distance >= 0 && distance <= threshold;
  }

  /// Delete a product image
  Future<bool> deleteProductImage(String imagePath) async {
    try {
      final file = File(imagePath);
      if (await file.exists()) {
        await file.delete();
        return true;
      }
      return false;
    } catch (e) {
      print('Error deleting product image: $e');
      return false;
    }
  }
}
