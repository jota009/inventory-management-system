#!/usr/bin/env python3
"""
Database Migration Script: Add Subcategory Column
==================================================

Purpose:
    This script adds the 'subcategory' column to the existing inventory table.
    The app code (app.py) already expects this column to exist, but the database
    schema was never updated to include it.

What it does:
    1. Connects to inventory.db
    2. Checks if the subcategory column already exists (safe to run multiple times)
    3. If not present, adds the column using ALTER TABLE
    4. Sets the column to TEXT type and allows NULL values (optional field)

Safety:
    - Uses ALTER TABLE ADD COLUMN (non-destructive operation)
    - Does not delete or modify existing data
    - Can be run multiple times without error (checks if column exists first)
    - Backs up the database before making changes

Usage:
    python migrate_add_subcategory.py
"""

import sqlite3
import shutil
from datetime import datetime
import os


def column_exists(cursor, table_name, column_name):
    """
    Check if a column exists in a table.

    Args:
        cursor: SQLite cursor object
        table_name: Name of the table to check
        column_name: Name of the column to check for

    Returns:
        bool: True if column exists, False otherwise
    """
    # Get table schema information
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    # Each row is: (cid, name, type, notnull, dflt_value, pk)
    # We check the 'name' field (index 1)
    column_names = [col[1] for col in columns]

    return column_name in column_names


def backup_database(db_path):
    """
    Create a backup of the database before migration.

    Args:
        db_path: Path to the database file

    Returns:
        str: Path to the backup file
    """
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"

    # Copy the database file
    shutil.copy2(db_path, backup_path)
    print(f"✓ Database backed up to: {backup_path}")

    return backup_path


def migrate():
    """
    Main migration function that adds the subcategory column.
    """
    db_path = 'inventory.db'

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"✗ Error: Database file '{db_path}' not found!")
        print("  Please run the Flask app first to initialize the database.")
        return False

    print("=" * 60)
    print("Database Migration: Adding 'subcategory' column")
    print("=" * 60)

    try:
        # Create backup before migration
        backup_path = backup_database(db_path)

        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the column already exists
        if column_exists(cursor, 'inventory', 'subcategory'):
            print("✓ Column 'subcategory' already exists. No migration needed.")
            conn.close()
            return True

        print("→ Adding 'subcategory' column to inventory table...")

        # Add the subcategory column
        # - TEXT type: stores text data
        # - After category: logical position (SQLite doesn't support this directly,
        #   but we document the intended position)
        # - NULL allowed: subcategory is optional
        cursor.execute('''
            ALTER TABLE inventory
            ADD COLUMN subcategory TEXT
        ''')

        # Commit the changes
        conn.commit()

        print("✓ Successfully added 'subcategory' column!")

        # Verify the change
        if column_exists(cursor, 'inventory', 'subcategory'):
            print("✓ Verification passed: Column exists in schema")
        else:
            print("✗ Verification failed: Column not found after migration")
            conn.close()
            return False

        # Show the updated schema
        print("\n" + "=" * 60)
        print("Updated Schema:")
        print("=" * 60)
        cursor.execute("PRAGMA table_info(inventory)")
        columns = cursor.fetchall()
        for col in columns:
            cid, name, type_, notnull, dflt_value, pk = col
            nullable = "NOT NULL" if notnull else "NULL"
            default = f"DEFAULT {dflt_value}" if dflt_value else ""
            pk_marker = "PRIMARY KEY" if pk else ""
            print(f"  {name:20s} {type_:12s} {nullable:10s} {default:20s} {pk_marker}")

        conn.close()

        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print(f"Backup saved at: {backup_path}")
        print("You can now use the add_item feature with subcategories.")

        return True

    except Exception as e:
        print(f"\n✗ Migration failed with error:")
        print(f"  {str(e)}")
        print(f"\nDatabase backup is available at: {backup_path}")
        print("You can restore it by running:")
        print(f"  cp {backup_path} {db_path}")
        return False


if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
