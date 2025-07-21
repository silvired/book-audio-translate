#!/usr/bin/env python3
"""
Setup verification script for the ebook to audio pipeline.
This script checks if all dependencies and components are working correctly.
"""

import sys
import os

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 10:
        print("✅ Python version is compatible (3.10+)")
        return True
    else:
        print("❌ Python version should be 3.10 or higher")
        print("   TTS library requires Python 3.10+ for best compatibility")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    dependencies = [
        ('pydub', 'pydub'),
        ('PyPDF2', 'PyPDF2'),
        ('TTS', 'TTS'),
        ('torch', 'torch')
    ]
    
    all_ok = True
    for package_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"✅ {package_name} is installed")
        except ImportError:
            print(f"❌ {package_name} is not installed")
            all_ok = False
    
    return all_ok

def check_project_structure():
    """Check if project structure is correct"""
    required_dirs = ['input_book', 'text_output', 'audio_output', 'merged_audio_output']
    required_files = ['book_to_text.py', 'text_to_speech_chunks.py', 'merge_audio_chunks.py', 'run_pipeline_v4.py']
    
    all_ok = True
    
    # Check directories
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ Directory '{dir_name}' exists")
        else:
            print(f"❌ Directory '{dir_name}' is missing")
            all_ok = False
    
    # Check files
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✅ File '{file_name}' exists")
        else:
            print(f"❌ File '{file_name}' is missing")
            all_ok = False
    
    return all_ok

def check_input_files():
    """Check if there are input files to process"""
    input_dir = 'input_book'
    if os.path.exists(input_dir):
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
        if pdf_files:
            print(f"✅ Found {len(pdf_files)} PDF file(s) in input_book directory")
            for pdf_file in pdf_files:
                print(f"   - {pdf_file}")
            return True
        else:
            print("❌ No PDF files found in input_book directory")
            return False
    else:
        print("❌ input_book directory does not exist")
        return False

def check_classes():
    """Check if all classes can be imported"""
    try:
        from book_to_text import PDFToText
        print("✅ PDFToText class imported successfully")
    except Exception as e:
        print(f"❌ Failed to import PDFToText: {e}")
        return False
    
    try:
        from text_to_speech_chunks import CoquiTTS
        print("✅ CoquiTTS class imported successfully")
    except Exception as e:
        print(f"❌ Failed to import CoquiTTS: {e}")
        return False
    
    try:
        from merge_audio_chunks import MergeAudioChunks
        print("✅ MergeAudioChunks class imported successfully")
    except Exception as e:
        print(f"❌ Failed to import MergeAudioChunks: {e}")
        return False
    
    return True

def main():
    """Main verification function"""
    print("=" * 60)
    print("Ebook to Audio Pipeline - Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Input Files", check_input_files),
        ("Class Imports", check_classes)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n--- {check_name} ---")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! The pipeline should work correctly.")
        print("\nTo run the pipeline:")
        print("1. pip install -r requirements.txt")
        print("2. ./run_pipeline.sh")
    else:
        print("❌ Some checks failed. Please fix the issues above before running the pipeline.")
    print("=" * 60)

if __name__ == "__main__":
    main() 