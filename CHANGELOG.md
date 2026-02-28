# Changelog

## [Unreleased]
### Fixed
- **Cookbook Deletion**: Deleting a cookbook now correctly cascade-deletes all associated recipes, ingredients, instructions, and category mappings instead of preserving orphaned recipes in the database.
- **MZ2 Imports**: Hard limit for `import_mz2` API route increased from 200MB to 500MB to accommodate Base64 overhead for large images.
- **Category Parsing**: Fixed MZ2 importing bug where category names were omitted due to XML spacing/fallback values missing the `<CatT>` text content.
- **UI Tweaks**: Removed the duplicate "Print Recipe" button layout on the recipe viewing modal.
