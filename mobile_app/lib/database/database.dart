import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

part 'database.g.dart';

/// Local products table for offline storage
class LocalProducts extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get name => text()();
  TextColumn get sku => text().nullable()();
  TextColumn get price => text().nullable()();
  IntColumn get stockQuantity => integer().nullable()();
  TextColumn get imagePath => text().nullable()(); // Local file path to thumbnail
  TextColumn get imageHash => text().nullable()(); // Perceptual hash for similarity matching
  IntColumn get wooCommerceId => integer().nullable()(); // Link to WooCommerce product
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
  DateTimeColumn get updatedAt => dateTime().nullable()();
}

@DriftDatabase(tables: [LocalProducts])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;

  static QueryExecutor _openConnection() {
    return driftDatabase(name: 'pos_assistant.db');
  }

  // --- CRUD Operations ---

  /// Insert a new local product
  Future<int> insertLocalProduct(LocalProductsCompanion product) {
    return into(localProducts).insert(product);
  }

  /// Get all local products
  Future<List<LocalProduct>> getAllLocalProducts() {
    return select(localProducts).get();
  }

  /// Get a product by ID
  Future<LocalProduct?> getLocalProductById(int id) {
    return (select(localProducts)..where((t) => t.id.equals(id))).getSingleOrNull();
  }

  /// Get a product by SKU
  Future<LocalProduct?> getLocalProductBySku(String sku) {
    return (select(localProducts)..where((t) => t.sku.equals(sku))).getSingleOrNull();
  }

  /// Get products by image hash (for similarity matching)
  Future<List<LocalProduct>> getProductsByImageHash(String hash) {
    return (select(localProducts)..where((t) => t.imageHash.equals(hash))).get();
  }

  /// Search products by name
  Future<List<LocalProduct>> searchProductsByName(String query) {
    return (select(localProducts)
      ..where((t) => t.name.like('%$query%')))
      .get();
  }

  /// Update a product
  Future<bool> updateLocalProduct(int id, LocalProductsCompanion product) {
    return (update(localProducts)..where((t) => t.id.equals(id)))
        .write(product.copyWith(updatedAt: Value(DateTime.now())))
        .then((count) => count > 0);
  }

  /// Delete a product
  Future<bool> deleteLocalProduct(int id) {
    return (delete(localProducts)..where((t) => t.id.equals(id)))
        .go()
        .then((count) => count > 0);
  }

  /// Check if a product with given SKU exists
  Future<bool> productExistsBySku(String sku) async {
    final product = await getLocalProductBySku(sku);
    return product != null;
  }
}
