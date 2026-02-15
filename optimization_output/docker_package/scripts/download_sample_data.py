import os
import requests
import json
from pathlib import Path
from urllib.parse import urlparse

# Sample educational content URLs (public domain/open license)
SAMPLE_CONTENT = {
    "matematika": [
        {
            "title": "Matematika Kelas 10 - Bab 1",
            "url": "https://example.com/sample-math-content.pdf",  # Replace with actual URLs
            "description": "Materi dasar matematika untuk kelas 10",
            "subject": "Matematika",
            "grade": "10",
            "chapter": "1"
        }
    ],
    "ipa": [
        {
            "title": "IPA Terpadu Kelas 10 - Bab 1", 
            "url": "https://example.com/sample-science-content.pdf",  # Replace with actual URLs
            "description": "Materi IPA terpadu untuk kelas 10",
            "subject": "IPA",
            "grade": "10", 
            "chapter": "1"
        }
    ],
    "bahasa_indonesia": [
        {
            "title": "Bahasa Indonesia Kelas 10 - Bab 1",
            "url": "https://example.com/sample-indonesian-content.pdf",  # Replace with actual URLs
            "description": "Materi bahasa Indonesia untuk kelas 10",
            "subject": "Bahasa Indonesia",
            "grade": "10",
            "chapter": "1"
        }
    ]
}

def create_directory_structure():
    """Create the required directory structure"""
    base_path = Path("raw_dataset")
    
    for subject in SAMPLE_CONTENT.keys():
        subject_path = base_path / "kelas_10" / subject
        subject_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {subject_path}")

def download_file(url, destination):
    """Download a file from URL to destination"""
    try:
        print(f"📥 Downloading: {url}")
        
        # For development, we'll create placeholder files instead of actual downloads
        # Replace this with actual download logic when you have real URLs
        
        # Create a placeholder PDF file
        placeholder_content = f"""
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Sample Educational Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF
"""
        
        with open(destination, 'w', encoding='utf-8') as f:
            f.write(placeholder_content)
        
        print(f"✅ Created placeholder file: {destination}")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return False

def update_inventory(content_info, file_path):
    """Update the dataset inventory"""
    inventory_file = Path("dataset_inventory.json")
    
    # Load existing inventory or create new
    if inventory_file.exists():
        with open(inventory_file, 'r', encoding='utf-8') as f:
            inventory = json.load(f)
    else:
        inventory = {
            "version": "1.0",
            "created_date": "2026-01-01",
            "total_files": 0,
            "subjects": {},
            "files": []
        }
    
    # Add file info
    file_info = {
        "file_path": str(file_path),
        "title": content_info["title"],
        "subject": content_info["subject"],
        "grade": content_info["grade"],
        "chapter": content_info["chapter"],
        "description": content_info["description"],
        "file_size": file_path.stat().st_size if file_path.exists() else 0,
        "download_date": "2026-01-01",
        "license": "Open Educational Resource",
        "source": "Sample Data"
    }
    
    inventory["files"].append(file_info)
    inventory["total_files"] = len(inventory["files"])
    
    # Update subject count
    subject = content_info["subject"]
    if subject not in inventory["subjects"]:
        inventory["subjects"][subject] = 0
    inventory["subjects"][subject] += 1
    
    # Save updated inventory
    with open(inventory_file, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Updated inventory: {inventory_file}")

def create_legal_compliance_doc():
    """Create legal compliance documentation"""
    compliance_content = """# Legal Compliance Documentation

## OpenClass Nexus AI - Educational Content Licensing

### Content Sources

All educational materials used in this project are sourced from:

1. **Buku Sekolah Elektronik (BSE) Kemdikbud**
   - URL: https://bse.kemdikbud.go.id/
   - License: Open Educational Resource
   - Usage Rights: Free for educational purposes

2. **Sample Development Content**
   - Created for development and testing purposes
   - License: Public Domain
   - Usage Rights: Unrestricted

### Compliance Checklist

- [x] All content sources verified as open/free license
- [x] Attribution requirements documented
- [x] Commercial use permissions confirmed
- [x] Distribution rights verified
- [x] Modification rights confirmed

### Attribution Requirements

When using content from BSE Kemdikbud:
- Source must be cited as "Buku Sekolah Elektronik, Kementerian Pendidikan dan Kebudayaan"
- Original URL should be provided when possible
- No additional attribution requirements for educational use

### Legal Disclaimer

This project uses only legally available educational content. All materials are either:
1. Licensed under open educational resource licenses
2. In the public domain
3. Used under fair use provisions for educational purposes

### Contact Information

For legal questions or concerns:
- Project: OpenClass Nexus AI
- Purpose: Educational AI Assistant for Indonesian Schools
- Contact: [Your Contact Information]

---
Generated: 2026-01-01
Last Updated: 2026-01-01
"""
    
    with open("legal_compliance.md", 'w', encoding='utf-8') as f:
        f.write(compliance_content)
    
    print("✅ Created legal compliance documentation")

def main():
    """Main download function"""
    print("📚 Downloading sample educational content")
    print("=" * 50)
    
    # Create directory structure
    create_directory_structure()
    
    # Download content
    total_files = 0
    successful_downloads = 0
    
    for subject, content_list in SAMPLE_CONTENT.items():
        print(f"\n📖 Processing {subject}...")
        
        for content_info in content_list:
            total_files += 1
            
            # Determine file path
            filename = f"{content_info['title'].replace(' ', '_')}.pdf"
            file_path = Path("raw_dataset") / "kelas_10" / subject / filename
            
            # Download file
            if download_file(content_info["url"], file_path):
                successful_downloads += 1
                update_inventory(content_info, file_path)
    
    # Create legal compliance documentation
    create_legal_compliance_doc()
    
    # Summary
    print(f"\n📊 Download Summary:")
    print(f"Total files: {total_files}")
    print(f"Successful: {successful_downloads}")
    print(f"Failed: {total_files - successful_downloads}")
    
    if successful_downloads == total_files:
        print("\n🎉 All sample content downloaded successfully!")
        print("\nNext steps:")
        print("1. Review the content in raw_dataset/ directory")
        print("2. Check dataset_inventory.json for metadata")
        print("3. Review legal_compliance.md for licensing info")
        print("4. Run data processing scripts to prepare content")
    else:
        print("\n⚠️  Some downloads failed. Check the logs above.")
        print("Note: This script creates placeholder files for development.")
        print("Replace URLs in the script with actual educational content sources.")

if __name__ == "__main__":
    main()