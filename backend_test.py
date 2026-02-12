#!/usr/bin/env python3
"""
Backend API Test Suite for Amen! Bible Reader App
Tests the Bible API endpoints as specified in the review request.
Focuses on multi-language Bible content, authentication, and AI study tools.
"""

import requests
import json
import sys
import time
from typing import Dict, Any, List

# Backend URL - using localhost since external URL has routing issues
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "testbible@cibospirituale.it"
TEST_PASSWORD = "Test123!"
TEST_NAME = "Bible Test User"

class BibleAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Amen-Bible-Tester/1.0'
        })
        self.results = []
        self.auth_token = None
        
    def log_result(self, test_name: str, success: bool, details: str, response_data: Dict = None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'response_data': response_data
        }
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def test_bible_books_italian(self):
        """Test GET /api/bible/books?lang=it - Should return list of Bible books in Italian"""
        try:
            response = self.session.get(f"{API_BASE}/bible/books?lang=it", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Bible Books (Italian)", False, 
                              f"Status code {response.status_code}, expected 200")
                return
                
            data = response.json()
            
            # Verify it's a list
            if not isinstance(data, list):
                self.log_result("Bible Books (Italian)", False, 
                              f"Response is not a list, got {type(data)}")
                return
                
            # Verify it has books
            if len(data) == 0:
                self.log_result("Bible Books (Italian)", False, "Empty books list")
                return
                
            # Check for expected Italian book names
            book_names = [book.get('name', '') for book in data]
            expected_books = ['Genesi', 'Esodo', 'Salmi', 'Matteo', 'Giovanni']
            
            found_books = [book for book in expected_books if book in book_names]
            if len(found_books) < 3:
                self.log_result("Bible Books (Italian)", False, 
                              f"Missing expected Italian books. Found: {found_books}")
                return
                
            # Verify book structure
            first_book = data[0]
            required_fields = ['name', 'chapters', 'abbrev']
            missing_fields = [field for field in required_fields if field not in first_book]
            
            if missing_fields:
                self.log_result("Bible Books (Italian)", False, 
                              f"Missing fields in book structure: {missing_fields}")
                return
                
            self.log_result("Bible Books (Italian)", True, 
                          f"Found {len(data)} books including {found_books[:3]}")
            
        except requests.exceptions.RequestException as e:
            self.log_result("Bible Books (Italian)", False, f"Request error: {str(e)}")
        except Exception as e:
            self.log_result("Bible Books (Italian)", False, f"Unexpected error: {str(e)}")
    
    def test_genesis_chapter_1(self):
        """Test GET /api/bible/chapter/Genesi/1?lang=it - Should return Genesis 1 with 31 verses from local database"""
        try:
            response = self.session.get(f"{API_BASE}/bible/chapter/Genesi/1?lang=it", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Genesis Chapter 1", False, 
                              f"Status code {response.status_code}, expected 200")
                return
                
            data = response.json()
            
            # Verify response structure
            required_fields = ['book', 'chapter', 'verses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result("Genesis Chapter 1", False, 
                              f"Missing fields: {missing_fields}")
                return
                
            # Verify book and chapter
            if data['book'] != 'Genesi' or data['chapter'] != 1:
                self.log_result("Genesis Chapter 1", False, 
                              f"Wrong book/chapter: {data['book']} {data['chapter']}")
                return
                
            # Verify verses
            verses = data['verses']
            if not isinstance(verses, list) or len(verses) == 0:
                self.log_result("Genesis Chapter 1", False, "Empty or invalid verses array")
                return
                
            # Should have 31 verses for Genesis 1
            if len(verses) != 31:
                self.log_result("Genesis Chapter 1", False, 
                              f"Expected 31 verses, got {len(verses)}")
                return
                
            # Check first verse content
            first_verse = verses[0]
            if 'verse' not in first_verse or 'text' not in first_verse:
                self.log_result("Genesis Chapter 1", False, "Invalid verse structure")
                return
                
            # Verify it's real Bible text (should contain "principio" and "Dio")
            first_text = first_verse['text']
            if 'principio' not in first_text.lower() or 'dio' not in first_text.lower():
                self.log_result("Genesis Chapter 1", False, 
                              f"First verse doesn't look like Genesis 1:1: {first_text}")
                return
                
            self.log_result("Genesis Chapter 1", True, 
                          f"Found {len(verses)} verses, first verse: {first_text[:50]}...")
            
        except requests.exceptions.RequestException as e:
            self.log_result("Genesis Chapter 1", False, f"Request error: {str(e)}")
        except Exception as e:
            self.log_result("Genesis Chapter 1", False, f"Unexpected error: {str(e)}")
    
    def test_genesis_chapter_4(self):
        """Test GET /api/bible/chapter/Genesi/4?lang=it - Should return Genesis 4 from laparola.net"""
        try:
            response = self.session.get(f"{API_BASE}/bible/chapter/Genesi/4?lang=it", timeout=15)
            
            if response.status_code != 200:
                self.log_result("Genesis Chapter 4", False, 
                              f"Status code {response.status_code}, expected 200")
                return
                
            data = response.json()
            
            # Verify response structure
            required_fields = ['book', 'chapter', 'verses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result("Genesis Chapter 4", False, 
                              f"Missing fields: {missing_fields}")
                return
                
            # Verify book and chapter
            if data['book'] != 'Genesi' or data['chapter'] != 4:
                self.log_result("Genesis Chapter 4", False, 
                              f"Wrong book/chapter: {data['book']} {data['chapter']}")
                return
                
            # Verify verses
            verses = data['verses']
            if not isinstance(verses, list) or len(verses) == 0:
                self.log_result("Genesis Chapter 4", False, "Empty or invalid verses array")
                return
                
            # Should have around 26 verses for Genesis 4
            if len(verses) < 20 or len(verses) > 30:
                self.log_result("Genesis Chapter 4", False, 
                              f"Expected ~26 verses, got {len(verses)}")
                return
                
            # Check first verse content (should be about Cain and Abel)
            first_verse = verses[0]
            if 'verse' not in first_verse or 'text' not in first_verse:
                self.log_result("Genesis Chapter 4", False, "Invalid verse structure")
                return
                
            first_text = first_verse['text']
            
            # Check if it's a placeholder or real text
            if '[Nuova Diodati]' in first_text or 'sarà presto disponibile' in first_text:
                self.log_result("Genesis Chapter 4", False, 
                              f"Got placeholder text instead of real Bible content: {first_text}")
                return
                
            # Verify it looks like real Genesis 4:1 (should mention Adam/Eva/Caino)
            if len(first_text) < 20:
                self.log_result("Genesis Chapter 4", False, 
                              f"First verse too short, might be placeholder: {first_text}")
                return
                
            self.log_result("Genesis Chapter 4", True, 
                          f"Found {len(verses)} verses from external source, first verse: {first_text[:50]}...")
            
        except requests.exceptions.RequestException as e:
            self.log_result("Genesis Chapter 4", False, f"Request error: {str(e)}")
        except Exception as e:
            self.log_result("Genesis Chapter 4", False, f"Unexpected error: {str(e)}")
    
    def test_exodus_chapter_20(self):
        """Test GET /api/bible/chapter/Esodo/20?lang=it - Should return Exodus 20 (Ten Commandments)"""
        try:
            response = self.session.get(f"{API_BASE}/bible/chapter/Esodo/20?lang=it", timeout=15)
            
            if response.status_code != 200:
                self.log_result("Exodus Chapter 20", False, 
                              f"Status code {response.status_code}, expected 200")
                return
                
            data = response.json()
            
            # Verify response structure
            required_fields = ['book', 'chapter', 'verses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result("Exodus Chapter 20", False, 
                              f"Missing fields: {missing_fields}")
                return
                
            # Verify book and chapter
            if data['book'] != 'Esodo' or data['chapter'] != 20:
                self.log_result("Exodus Chapter 20", False, 
                              f"Wrong book/chapter: {data['book']} {data['chapter']}")
                return
                
            # Verify verses
            verses = data['verses']
            if not isinstance(verses, list) or len(verses) == 0:
                self.log_result("Exodus Chapter 20", False, "Empty or invalid verses array")
                return
                
            # Should have around 17-26 verses for Exodus 20
            if len(verses) < 15:
                self.log_result("Exodus Chapter 20", False, 
                              f"Too few verses for Exodus 20, got {len(verses)}")
                return
                
            # Check first verse content
            first_verse = verses[0]
            if 'verse' not in first_verse or 'text' not in first_verse:
                self.log_result("Exodus Chapter 20", False, "Invalid verse structure")
                return
                
            first_text = first_verse['text']
            
            # Check if it's a placeholder
            if '[Nuova Diodati]' in first_text or 'sarà presto disponibile' in first_text:
                self.log_result("Exodus Chapter 20", False, 
                              f"Got placeholder text: {first_text}")
                return
                
            # Look for Ten Commandments content in the verses
            all_text = ' '.join([v['text'] for v in verses[:10]])
            commandment_keywords = ['comandamenti', 'dio', 'signore', 'non avrai', 'non uccidere', 'non rubare']
            found_keywords = [kw for kw in commandment_keywords if kw.lower() in all_text.lower()]
            
            if len(found_keywords) < 2:
                self.log_result("Exodus Chapter 20", False, 
                              f"Doesn't look like Ten Commandments content. Found keywords: {found_keywords}")
                return
                
            self.log_result("Exodus Chapter 20", True, 
                          f"Found {len(verses)} verses with Ten Commandments content")
            
        except requests.exceptions.RequestException as e:
            self.log_result("Exodus Chapter 20", False, f"Request error: {str(e)}")
        except Exception as e:
            self.log_result("Exodus Chapter 20", False, f"Unexpected error: {str(e)}")
    
    def test_psalm_23(self):
        """Test GET /api/bible/chapter/Salmi/23?lang=it - Should return Psalm 23 with 6 verses from local database"""
        try:
            response = self.session.get(f"{API_BASE}/bible/chapter/Salmi/23?lang=it", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Psalm 23", False, 
                              f"Status code {response.status_code}, expected 200")
                return
                
            data = response.json()
            
            # Verify response structure
            required_fields = ['book', 'chapter', 'verses']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result("Psalm 23", False, 
                              f"Missing fields: {missing_fields}")
                return
                
            # Verify book and chapter
            if data['book'] != 'Salmi' or data['chapter'] != 23:
                self.log_result("Psalm 23", False, 
                              f"Wrong book/chapter: {data['book']} {data['chapter']}")
                return
                
            # Verify verses
            verses = data['verses']
            if not isinstance(verses, list) or len(verses) == 0:
                self.log_result("Psalm 23", False, "Empty or invalid verses array")
                return
                
            # Should have exactly 6 verses for Psalm 23
            if len(verses) != 6:
                self.log_result("Psalm 23", False, 
                              f"Expected 6 verses, got {len(verses)}")
                return
                
            # Check first verse content (should be "L'Eterno è il mio pastore")
            first_verse = verses[0]
            if 'verse' not in first_verse or 'text' not in first_verse:
                self.log_result("Psalm 23", False, "Invalid verse structure")
                return
                
            first_text = first_verse['text']
            
            # Verify it's the famous Psalm 23:1
            if 'pastore' not in first_text.lower() or 'eterno' not in first_text.lower():
                self.log_result("Psalm 23", False, 
                              f"First verse doesn't look like Psalm 23:1: {first_text}")
                return
                
            # Check that it's not a placeholder
            if '[Nuova Diodati]' in first_text or 'sarà presto disponibile' in first_text:
                self.log_result("Psalm 23", False, 
                              f"Got placeholder text: {first_text}")
                return
                
            self.log_result("Psalm 23", True, 
                          f"Found {len(verses)} verses from local database, first verse: {first_text}")
            
        except requests.exceptions.RequestException as e:
            self.log_result("Psalm 23", False, f"Request error: {str(e)}")
        except Exception as e:
            self.log_result("Psalm 23", False, f"Unexpected error: {str(e)}")
    
    def run_all_tests(self):
        """Run all Bible API tests"""
        print("🔍 Starting Bible API Tests for Amen! App")
        print(f"📡 Testing backend at: {BACKEND_URL}")
        print("=" * 60)
        
        # Test each endpoint
        self.test_bible_books_italian()
        self.test_genesis_chapter_1()
        self.test_genesis_chapter_4()
        self.test_exodus_chapter_20()
        self.test_psalm_23()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['details']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.results:
            if result['success']:
                print(f"  • {result['test']}: {result['details']}")
        
        return passed == total

def main():
    """Main test runner"""
    tester = BibleAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Bible API is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the details above.")
        sys.exit(1)

if __name__ == "__main__":
    main()