"""
Load Testing Configuration

This file contains configuration for load testing scenarios.
"""

# Test scenarios
SCENARIOS = {
    "light_load": {
        "users": 50,
        "spawn_rate": 5,
        "run_time": "3m",
        "description": "Light load - 50 concurrent users"
    },
    "normal_load": {
        "users": 100,
        "spawn_rate": 10,
        "run_time": "5m",
        "description": "Normal load - 100 concurrent users (Requirement 18.1)"
    },
    "heavy_load": {
        "users": 300,
        "spawn_rate": 20,
        "run_time": "5m",
        "description": "Heavy load - 300 concurrent users (Requirement 18.2)"
    },
    "stress_test": {
        "users": 500,
        "spawn_rate": 50,
        "run_time": "10m",
        "description": "Stress test - 500 concurrent users"
    },
    "endurance_test": {
        "users": 100,
        "spawn_rate": 10,
        "run_time": "1h",
        "description": "Endurance test - 100 users for 1 hour"
    }
}

# Performance targets (from Requirements 18.3, 18.4)
PERFORMANCE_TARGETS = {
    "p90_latency_min_ms": 3000,
    "p90_latency_max_ms": 8000,
    "max_error_rate_percent": 1.0,
    "max_queue_depth": 100
}

# Test users (should match database)
TEST_USERS = [
    {"username": "siswa1", "password": "password123"},
    {"username": "siswa2", "password": "password123"},
    {"username": "siswa3", "password": "password123"},
    {"username": "siswa4", "password": "password123"},
    {"username": "siswa5", "password": "password123"},
]

# Sample questions for testing
SAMPLE_QUESTIONS = [
    # Matematika
    "Apa itu Teorema Pythagoras?",
    "Bagaimana cara menghitung luas lingkaran?",
    "Bagaimana cara menyelesaikan persamaan kuadrat?",
    "Jelaskan tentang fungsi trigonometri",
    "Apa itu matriks dan bagaimana cara mengalikannya?",
    
    # Informatika
    "Jelaskan konsep variabel dalam pemrograman",
    "Apa itu algoritma sorting?",
    "Bagaimana cara kerja struktur data stack?",
    "Jelaskan perbedaan antara array dan linked list",
    "Apa itu rekursi dalam pemrograman?",
    
    # Biologi
    "Jelaskan tentang fotosintesis",
    "Apa perbedaan antara mitosis dan meiosis?",
    "Apa fungsi dari klorofil pada tumbuhan?",
    "Jelaskan sistem peredaran darah manusia",
    "Apa itu DNA dan bagaimana strukturnya?",
    
    # Fisika
    "Jelaskan hukum Newton pertama",
    "Bagaimana proses terjadinya hujan?",
    "Apa itu energi kinetik dan potensial?",
    "Jelaskan tentang gelombang elektromagnetik",
    "Bagaimana cara kerja rangkaian listrik sederhana?",
    
    # General
    "Apa itu metode ilmiah?",
    "Jelaskan tentang sistem periodik unsur",
    "Bagaimana cara menghitung kecepatan rata-rata?",
    "Apa perbedaan antara massa dan berat?",
    "Jelaskan tentang ekosistem dan rantai makanan",
]

# Subject filters
SUBJECTS = ["matematika", "informatika", "biologi", "fisika", "all"]

# API endpoints to test
ENDPOINTS = {
    "login": "/api/auth/login",
    "chat": "/api/chat",
    "chat_stream": "/api/chat/stream",
    "queue_stats": "/api/queue/stats",
    "health": "/api/health"
}

# Report configuration
REPORT_CONFIG = {
    "output_dir": "tests/load/reports",
    "format": "json",
    "include_raw_data": False,
    "include_charts": True
}
