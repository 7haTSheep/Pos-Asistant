import 'package:drift/drift.dart';
import 'package:image_picker/image_picker.dart';
import '../database/database.dart';
import 'image_storage_service.dart';

/// Service layer for managing local products with images
class LocalDatabaseService {
  static LocalDatabaseService? _instance;
  static AppDatabase? _database;
  final ImageStorageService _imageService = ImageStorageService();

  LocalDatabaseService._();

  /// Singleton instance
  static LocalDatabaseService get instance {
    _instance ??= LocalDatabaseService._();
    return _instance!;
  }

  /// Get database instance
  AppDatabase get database {
    _database ??= AppDatabase();
    return _database!;
  }

  /// Add a new product with an optional image
  Future<int?> addProduct({
    required String name,
    String? sku,
    String? price,
    int? stockQuantity,
    XFile? image,
    int? wooCommerceId,
  }) async {
    try {
      // First insert the product to get the ID
      final productId = await database.insertLocalProduct(
        LocalProductsCompanion(
          name: Value(name),
          sku: Value(sku),
          price: Value(price),
          stockQuantity: Value(stockQuantity),
          wooCommerceId: Value(wooCommerceId),
        ),
      );

      // If there's an image, save it and update the product
      if (image != null) {
        final imagePath = await _imageService.saveProductImage(image, productId);
        final imageHash = await _imageService.computeImageHashFromFile(image);
        
        if (imagePath != null) {
          await database.updateLocalProduct(
            productId,
            LocalProductsCompanion(
              imagePath: Value(imagePath),
              imageHash: Value(imageHash),
            ),
          );
        }
      }

      return productId;
    } catch (e) {
      print('Error adding product: $e');
      return null;
    }
  }

  /// Get all products
  Future<List<LocalProduct>> getAllProducts() {
    return database.getAllLocalProducts();
  }

  /// Get product by SKU
  Future<LocalProduct?> getProductBySku(String sku) {
    return database.getLocalProductBySku(sku);
  }

  /// Get product by ID
  Future<LocalProduct?> getProductById(int id) {
    return database.getLocalProductById(id);
  }

  /// Search products by name
  Future<List<LocalProduct>> searchProducts(String query) {
    return database.searchProductsByName(query);
  }

  /// Update product with optional new image
  Future<bool> updateProduct({
    required int id,
    String? name,
    String? sku,
    String? price,
    int? stockQuantity,
    XFile? newImage,
    int? wooCommerceId,
  }) async {
    try {
      String? imagePath;
      String? imageHash;

      // Handle new image if provided
      if (newImage != null) {
        // Delete old image if exists
        final existingProduct = await database.getLocalProductById(id);
        if (existingProduct?.imagePath != null) {
          await _imageService.deleteProductImage(existingProduct!.imagePath!);
        }
        
        imagePath = await _imageService.saveProductImage(newImage, id);
        imageHash = await _imageService.computeImageHashFromFile(newImage);
      }

      return await database.updateLocalProduct(
        id,
        LocalProductsCompanion(
          name: name != null ? Value(name) : const Value.absent(),
          sku: sku != null ? Value(sku) : const Value.absent(),
          price: price != null ? Value(price) : const Value.absent(),
          stockQuantity: stockQuantity != null ? Value(stockQuantity) : const Value.absent(),
          wooCommerceId: wooCommerceId != null ? Value(wooCommerceId) : const Value.absent(),
          imagePath: imagePath != null ? Value(imagePath) : const Value.absent(),
          imageHash: imageHash != null ? Value(imageHash) : const Value.absent(),
        ),
      );
    } catch (e) {
      print('Error updating product: $e');
      return false;
    }
  }

  /// Delete a product and its image
  Future<bool> deleteProduct(int id) async {
    try {
      // Get product to delete image
      final product = await database.getLocalProductById(id);
      if (product?.imagePath != null) {
        await _imageService.deleteProductImage(product!.imagePath!);
      }
      
      return await database.deleteLocalProduct(id);
    } catch (e) {
      print('Error deleting product: $e');
      return false;
    }
  }

  /// Find similar products by image
  Future<List<LocalProduct>> findSimilarProducts(XFile image, {int threshold = 10}) async {
    try {
      final hash = await _imageService.computeImageHashFromFile(image);
      if (hash == null) return [];

      // Get all products with image hashes
      final allProducts = await database.getAllLocalProducts();
      
      // Filter by similarity
      return allProducts.where((product) {
        if (product.imageHash == null) return false;
        return _imageService.areImagesSimilar(hash, product.imageHash!, threshold: threshold);
      }).toList();
    } catch (e) {
      print('Error finding similar products: $e');
      return [];
    }
  }

  /// Check if product exists by SKU
  Future<bool> productExistsBySku(String sku) {
    return database.productExistsBySku(sku);
  }
}
