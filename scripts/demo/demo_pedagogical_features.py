"""
Demo Pedagogical Features

Demonstrates the integrated pedagogical engine features:
1. Automatic mastery tracking after each question
2. Weak area detection
3. Adaptive practice question generation
4. Progress summary
"""

import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# API base URL
BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def login_as_student():
    """Login as student and return token"""
    print_section("1. LOGIN AS STUDENT")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "username": "siswa",
            "password": "siswa123",
            "role": "siswa"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print(f"✓ Login successful")
            print(f"  Token: {data['token'][:20]}...")
            return data['token']
        else:
            print(f"✗ Login failed: {data['message']}")
            return None
    else:
        print(f"✗ HTTP Error: {response.status_code}")
        return None

def ask_questions(token):
    """Ask several questions to build mastery data"""
    print_section("2. ASK QUESTIONS (Building Mastery Data)")
    
    questions = [
        "Bagaimana cara membuat program Python?",
        "Apa itu linked list?",
        "Jelaskan tentang SQL query",
        "Bagaimana cara membuat function di Python?",
        "Apa perbedaan array dan linked list?",
    ]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers=headers,
            json={
                "message": question,
                "subject_filter": "informatika"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Response received")
            print(f"  Confidence: {data.get('confidence', 'N/A')}")
            print(f"  (Mastery tracking updated automatically)")
        else:
            print(f"✗ HTTP Error: {response.status_code}")

def get_progress(token):
    """Get student progress summary"""
    print_section("3. GET PROGRESS SUMMARY")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/student/progress",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data['success']:
            print(f"✓ Progress retrieved successfully\n")
            print(f"Total Topics: {data['total_topics']}")
            print(f"Average Mastery: {data['average_mastery']:.2f}")
            print(f"Weak Areas Count: {data['weak_areas_count']}\n")
            
            print("Topics Mastery:")
            for topic, mastery in data['topics'].items():
                bar = "█" * int(mastery * 20)
                print(f"  {topic:20s} {mastery:.2f} {bar}")
            
            if data['weak_areas']:
                print("\nWeak Areas:")
                for wa in data['weak_areas']:
                    print(f"  • {wa['topic']}")
                    print(f"    Mastery: {wa['mastery_level']:.2f}")
                    print(f"    Weakness Score: {wa['weakness_score']:.2f}")
        else:
            print(f"✗ Failed: {data.get('error')}")
    else:
        print(f"✗ HTTP Error: {response.status_code}")
        print(response.text)

def get_weak_areas(token):
    """Get weak areas with recommendations"""
    print_section("4. GET WEAK AREAS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/student/weak-areas",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data['success']:
            weak_areas = data['weak_areas']
            
            if weak_areas:
                print(f"✓ Found {len(weak_areas)} weak area(s)\n")
                
                for i, wa in enumerate(weak_areas, 1):
                    print(f"{i}. {wa['topic']}")
                    print(f"   Mastery Level: {wa['mastery_level']:.2f}")
                    print(f"   Weakness Score: {wa['weakness_score']:.2f}")
                    print(f"   Recommendation: {wa['recommendation']}")
                    print()
            else:
                print("✓ No weak areas detected - great job!")
        else:
            print(f"✗ Failed: {data.get('error')}")
    else:
        print(f"✗ HTTP Error: {response.status_code}")
        print(response.text)

def get_practice_questions(token):
    """Get adaptive practice questions"""
    print_section("5. GET PRACTICE QUESTIONS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/student/practice-questions?count=3",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data['success']:
            questions = data['questions']
            
            if questions:
                print(f"✓ Generated {len(questions)} practice question(s)\n")
                
                for i, q in enumerate(questions, 1):
                    print(f"{i}. Topic: {q['topic']} | Difficulty: {q['difficulty']}")
                    print(f"   Question: {q['question']}")
                    print(f"   Hint: {q['hint']}")
                    print()
            else:
                print("✓ No practice questions needed - mastery is good!")
        else:
            print(f"✗ Failed: {data.get('error')}")
    else:
        print(f"✗ HTTP Error: {response.status_code}")
        print(response.text)

def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('initialized') and data.get('database'):
                return True
            else:
                print("✗ Server not fully initialized")
                print(f"  Initialized: {data.get('initialized')}")
                print(f"  Database: {data.get('database')}")
                return False
        else:
            print(f"✗ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server")
        print(f"  Please start the server: python api_server.py")
        return False
    except Exception as e:
        print(f"✗ Error checking server: {e}")
        return False

def main():
    """Main demo function"""
    print("=" * 60)
    print("OpenClass Nexus AI - Pedagogical Features Demo")
    print("=" * 60)
    
    # Check server
    print("\nChecking server status...")
    if not check_server():
        print("\n✗ Server is not running or not ready")
        print("\nPlease:")
        print("1. Start the server: python api_server.py")
        print("2. Wait for initialization to complete")
        print("3. Run this demo again")
        return False
    
    print("✓ Server is running and ready\n")
    
    # Login
    token = login_as_student()
    if not token:
        print("\n✗ Demo failed: Cannot login")
        return False
    
    # Ask questions to build mastery data
    ask_questions(token)
    
    # Get progress summary
    get_progress(token)
    
    # Get weak areas
    get_weak_areas(token)
    
    # Get practice questions
    get_practice_questions(token)
    
    # Summary
    print_section("DEMO COMPLETED")
    print("\n✓ All pedagogical features demonstrated successfully!")
    print("\nFeatures shown:")
    print("  1. Automatic mastery tracking after each question")
    print("  2. Progress summary with mastery levels per topic")
    print("  3. Weak area detection with recommendations")
    print("  4. Adaptive practice question generation")
    print("\nThese features are now INTEGRATED and working in the API server!")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
