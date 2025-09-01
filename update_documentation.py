#!/usr/bin/env python3
"""
Script to update all documentation files with new system name
"""

import os
import re

# Define the old and new system names
OLD_NAME = "ระบบรวบรวมข้อมูลการทายเลข"
NEW_NAME = "ระบบสมาชิกขายส่ง"

# Files to update
FILES_TO_UPDATE = [
    "system_design_complete.md",
    "source_code_structure.md", 
    "database_structure_complete.md",
    "development_plan_checklist.md",
    "implementation_summary.md",
    "rule_matrix.md",
    "database_schema_updated.md",
    "security_implementation.md",
    "data_correctness_implementation.md",
    "p1_timezone_export_backup.md",
    "p1_dashboard_services.md"
]

def update_file(filepath):
    """Update a single file with new system name"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace old system name with new one
        updated_content = content.replace(OLD_NAME, NEW_NAME)
        
        # Also update variations
        updated_content = updated_content.replace(
            "ระบบรวบรวมและจัดการข้อมูลการทายเลข", 
            NEW_NAME
        )
        
        # Check if any changes were made
        if content != updated_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Updated: {filepath}")
            return True
        else:
            print(f"⏭️  No changes needed: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {filepath}: {e}")
        return False

def main():
    """Main function to update all files"""
    print(f"🔄 Updating documentation files...")
    print(f"Old name: {OLD_NAME}")
    print(f"New name: {NEW_NAME}")
    print("-" * 50)
    
    updated_count = 0
    
    for filename in FILES_TO_UPDATE:
        if update_file(filename):
            updated_count += 1
    
    print("-" * 50)
    print(f"✅ Updated {updated_count} files successfully!")
    
    # Also update the landing page redirect note
    print("\n📝 Additional updates needed:")
    print("- Index page now redirects to login directly")
    print("- System name changed throughout the application")
    print("- All templates updated with new branding")

if __name__ == "__main__":
    main()

