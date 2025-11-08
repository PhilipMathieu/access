#!/usr/bin/env python3
"""
Remove DVC tracking from the project.
This script removes .dvc files and updates .gitignore if needed.
"""

import sys
from pathlib import Path
import shutil

def remove_dvc_files():
    """Remove all .dvc files from the data directory."""
    data_dir = Path("data")
    dvc_files = list(data_dir.glob("*.dvc"))
    
    if not dvc_files:
        print("No .dvc files found in data/ directory.")
        return 0
    
    print(f"Found {len(dvc_files)} .dvc file(s):")
    for dvc_file in dvc_files:
        print(f"  - {dvc_file}")
    
    response = input("\nRemove these .dvc files? (y/N): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return 1
    
    removed = 0
    for dvc_file in dvc_files:
        try:
            dvc_file.unlink()
            print(f"✓ Removed: {dvc_file}")
            removed += 1
        except Exception as e:
            print(f"✗ Error removing {dvc_file}: {e}")
    
    print(f"\nRemoved {removed} .dvc file(s).")
    return 0


def update_gitignore():
    """Update .gitignore to ensure data files are tracked (or ignored as needed)."""
    gitignore_path = Path(".gitignore")
    
    if not gitignore_path.exists():
        print("\n.gitignore not found. Creating one...")
        with open(gitignore_path, 'w') as f:
            f.write("# Data files\n")
            f.write("data/*.zip\n")
            f.write("data/*.txt\n")
            f.write("data/*.geojson\n")
            f.write("data/*.shp\n")
            f.write("data/*.shx\n")
            f.write("data/*.dbf\n")
            f.write("data/*.prj\n")
            f.write("data/blocks/\n")
            f.write("data/tracts/\n")
            f.write("data/conserved_lands/\n")
            f.write("data/joins/\n")
            f.write("data/walk_times/\n")
            f.write("\n# Keep directory structure\n")
            f.write("!data/.gitkeep\n")
        print("✓ Created .gitignore")
        return
    
    print("\n.gitignore exists. Review it to ensure data files are handled appropriately.")
    print("You may want to add data files to .gitignore if they're large.")


def check_dvc_config():
    """Check for DVC configuration files."""
    dvc_files = [
        Path(".dvc"),
        Path(".dvcignore"),
        Path("dvc.yaml"),
        Path("dvc.lock"),
    ]
    
    found = [f for f in dvc_files if f.exists()]
    
    if found:
        print("\nFound DVC configuration files:")
        for f in found:
            print(f"  - {f}")
        print("\nYou may want to remove these as well:")
        print("  rm -rf .dvc .dvcignore dvc.yaml dvc.lock")
    else:
        print("\nNo additional DVC configuration files found.")


def main():
    """Main function."""
    print("=" * 70)
    print("Remove DVC from Access Project")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Remove .dvc files from data/ directory")
    print("  2. Update .gitignore (if needed)")
    print("  3. Check for other DVC configuration files")
    print()
    
    # Remove .dvc files
    result = remove_dvc_files()
    if result != 0:
        return result
    
    # Update .gitignore
    update_gitignore()
    
    # Check for other DVC files
    check_dvc_config()
    
    print("\n" + "=" * 70)
    print("DVC Removal Complete")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Review .gitignore to ensure data files are handled appropriately")
    print("  2. If you have a DVC remote configured, you may want to remove it:")
    print("     git remote remove dvc  # if it exists")
    print("  3. Commit the changes:")
    print("     git add .gitignore")
    print("     git commit -m 'Remove DVC tracking from project'")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

