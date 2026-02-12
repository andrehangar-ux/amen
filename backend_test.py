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
        
    def test_multi_language_bible_content(self):
        """Test CRITICAL requirement: Multi-language Bible content in different languages"""
        
        # Test cases: book/chapter combinations with expected language-specific content
        test_cases = [
            {
                "book": "Genesi", "chapter": 1, "lang": "it", 
                "expected_words": ["principio", "dio", "creò", "cieli", "terra"],
                "description": "Genesis 1 in Italian"
            },
            {
                "book": "Genesi", "chapter": 1, "lang": "es", 
                "expected_words": ["principio", "dios", "creó", "cielos", "tierra"],
                "description": "Genesis 1 in Spanish"
            },
            {
                "book": "Genesi", "chapter": 1, "lang": "en", 
                "expected_words": ["beginning", "god", "created", "heaven", "earth"],
                "description": "Genesis 1 in English"
            },
            {
                "book": "Genesi", "chapter": 1, "lang": "de", 
                "expected_words": ["anfang", "gott", "schuf", "himmel", "erde"],
                "description": "Genesis 1 in German"
            },
            {
                "book": "Genesi", "chapter": 1, "lang": "fr", 
                "expected_words": ["commencement", "dieu", "créa", "cieux", "terre"],
                "description": "Genesis 1 in French"
            },
            {
                "book": "Genesi", "chapter": 1, "lang": "pt", 
                "expected_words": ["princípio", "deus", "criou", "céu", "terra"],
                "description": "Genesis 1 in Portuguese"
            },
            {
                "book": "Salmi", "chapter": 23, "lang": "it", 
                "expected_words": ["eterno", "pastore", "nulla", "mancherà"],
                "description": "Psalm 23 in Italian"
            },
            {
                "book": "Salmi", "chapter": 23, "lang": "es", 
                "expected_words": ["jehová", "pastor", "nada", "faltará"],
                "description": "Psalm 23 in Spanish"
            },
            {
                "book": "Giovanni", "chapter": 3, "lang": "it", 
                "expected_words": ["dio", "amato", "mondo", "figlio", "vita", "eterna"],
                "description": "John 3 in Italian"
            },
            {
                "book": "Giovanni", "chapter": 3, "lang": "fr", 
                "expected_words": ["dieu", "aimé", "monde", "fils", "vie", "éternelle"],
                "description": "John 3 in French"
            }
        ]
        
        for test_case in test_cases:
            self._test_single_language_chapter(test_case)
    
    def _test_single_language_chapter(self, test_case):
        """Test a single book/chapter in a specific language"""
        book = test_case["book"]
        chapter = test_case["chapter"]
        lang = test_case["lang"]
        expected_words = test_case["expected_words"]
        description = test_case["description"]
        
        try:
            response = self.session.get(
                f"{API_BASE}/bible/chapter/{book}/{chapter}?lang={lang}", 
                timeout=15
            )
            
            if response.status_code != 200:
                self.log_result(description, False, 
                              f"Status code {response.status_code}, expected 200")
                return
                
            data = response.json()
            
            # Verify response structure
            required_fields = ['book', 'chapter', 'verses', 'language']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(description, False, 
                              f"Missing fields: {missing_fields}")
                return
            
            # Verify language matches
            if data.get('language') != lang:
                self.log_result(description, False, 
                              f"Wrong language in response: {data.get('language')}, expected {lang}")
                return
                
            # Verify verses exist
            verses = data['verses']
            if not isinstance(verses, list) or len(verses) == 0:
                self.log_result(description, False, "Empty or invalid verses array")
                return
            
            # Check if it's placeholder text (should be real content in target language)
            first_verse_text = verses[0].get('text', '').lower()
            
            # Check for placeholder indicators
            placeholder_indicators = [
                'sarà presto disponibile', 'estará disponible pronto', 
                'will be available soon', 'wird bald verfügbar sein',
                'sera bientôt disponible', 'estará disponível em breve',
                'questo capitolo', 'este capítulo', 'this chapter', 'dieses kapitel',
                'ce chapitre'
            ]
            
            if any(indicator in first_verse_text for indicator in placeholder_indicators):
                self.log_result(description, False, 
                              f"Got placeholder text instead of real Bible content: {first_verse_text[:100]}")
                return
            
            # Verify language-specific content
            all_text = ' '.join([v.get('text', '') for v in verses[:5]]).lower()
            
            # Check for expected words in the target language
            found_words = [word for word in expected_words if word.lower() in all_text]
            
            if len(found_words) < 2:  # At least 2 expected words should be found
                self.log_result(description, False, 
                              f"Content doesn't appear to be in {lang}. Expected words: {expected_words}, Found: {found_words}. Text sample: {all_text[:200]}")
                return
            
            # Check that it's not English fallback (for non-English languages)
            if lang != "en":
                english_indicators = ["god", "lord", "jesus", "christ", "heaven", "earth", "beginning", "created"]
                english_found = [word for word in english_indicators if word in all_text]
                
                # If we find too many English words, it might be English fallback
                if len(english_found) > 2 and len(found_words) < len(english_found):
                    self.log_result(description, False, 
                                  f"Appears to be English fallback instead of {lang}. English words found: {english_found}")
                    return
            
            self.log_result(description, True, 
                          f"✅ Real {lang.upper()} content found! Words: {found_words[:3]}... ({len(verses)} verses)")
            
        except requests.exceptions.RequestException as e:
            self.log_result(description, False, f"Request error: {str(e)}")
        except Exception as e:
            self.log_result(description, False, f"Unexpected error: {str(e)}")
    
    def test_user_registration(self):
        """Test POST /api/auth/register - Should create user and return session token"""
        try:
            # Use unique email to avoid conflicts
            unique_email = f"test_{int(time.time())}@cibospirituale.it"
            
            payload = {
                "email": unique_email,
                "password": TEST_PASSWORD,
                "name": TEST_NAME,
                "language": "it"
            }
            
            response = self.session.post(f"{API_BASE}/auth/register", 
                                       json=payload, timeout=10)
            
            if response.status_code != 200:
                self.log_result("User Registration", False, 
                              f"Status code {response.status_code}, expected 200. Response: {response.text}")
                return
                
            data = response.json()
            
            # Verify response structure
            required_fields = ['user', 'session_token']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result("User Registration", False, 
                              f"Missing fields: {missing_fields}")
                return
            
            # Verify user data
            user = data['user']
            if user.get('email') != unique_email or user.get('name') != TEST_NAME:
                self.log_result("User Registration", False, 
                              f"User data mismatch. Expected email: {unique_email}, got: {user.get('email')}")
                return
            
            # Verify session token
            session_token = data['session_token']
            if not session_token or len(session_token) < 10:
                self.log_result("User Registration", False, 
                              f"Invalid session token: {session_token}")
                return
            
            # Store token for later tests
            self.auth_token = session_token
            
            self.log_result("User Registration", True, 
                          f"User created successfully with email: {unique_email}")
            
        except requests.exceptions.RequestException as e:
            self.log_result("User Registration", False, f"Request error: {str(e)}")
        except Exception as e:
            self.log_result("User Registration", False, f"Unexpected error: {str(e)}")
    
    def test_user_login(self):
        """Test POST /api/auth/login - Should return session token for existing user"""
        try:
            payload = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", 
                                       json=payload, timeout=10)
            
            if response.status_code != 200:
                self.log_result("User Login", False, 
                              f"Status code {response.status_code}, expected 200. Response: {response.text}")
                return
                
            data = response.json()
            
            # Verify response structure
            required_fields = ['user', 'session_token']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result("User Login", False, 
                              f"Missing fields: {missing_fields}")
                return
            
            # Verify user data
            user = data['user']
            if user.get('email') != TEST_EMAIL:
                self.log_result("User Login", False, 
                              f"User email mismatch. Expected: {TEST_EMAIL}, got: {user.get('email')}")
                return
            
            # Verify session token
            session_token = data['session_token']
            if not session_token or len(session_token) < 10:
                self.log_result("User Login", False, 
                              f"Invalid session token: {session_token}")
                return
            
            # Store token for AI study tools test
            if not self.auth_token:  # Use this token if we don't have one from registration
                self.auth_token = session_token
            
            self.log_result("User Login", True, 
                          f"Login successful for user: {TEST_EMAIL}")
            
        except requests.exceptions.RequestException as e:
            self.log_result("User Login", False, f"Request error: {str(e)}")
        except Exception as e:
            self.log_result("User Login", False, f"Unexpected error: {str(e)}")
    
    def test_ai_study_tools(self):
        """Test POST /api/bible/study/ai-explain - Should return AI explanation with Bearer token"""
        if not self.auth_token:
            self.log_result("AI Study Tools", False, 
                          "No auth token available. Registration or login must succeed first.")
            return
            
        try:
            # Set Authorization header
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "verse_ref": "Giovanni 3:16",
                "verse_text": "Poiché Dio ha tanto amato il mondo, che ha dato il suo unigenito Figlio, affinché chiunque crede in lui non perisca, ma abbia vita eterna.",
                "question": "Cosa significa questo versetto per un cristiano?"
            }
            
            response = self.session.post(f"{API_BASE}/bible/study/ai-explain", 
                                       json=payload, headers=headers, timeout=30)
            
            if response.status_code == 401:
                self.log_result("AI Study Tools", False, 
                              "Authentication failed. Token might be invalid.")
                return
                
            if response.status_code != 200:
                self.log_result("AI Study Tools", False, 
                              f"Status code {response.status_code}, expected 200. Response: {response.text}")
                return
                
            data = response.json()
            
            # Verify response has explanation
            if 'explanation' not in data:
                self.log_result("AI Study Tools", False, 
                              f"Missing 'explanation' field in response: {data}")
                return
            
            explanation = data['explanation']
            if not explanation or len(explanation) < 50:
                self.log_result("AI Study Tools", False, 
                              f"AI explanation too short or empty: {explanation}")
                return
            
            # Check if explanation looks like AI-generated content
            if 'questo versetto' not in explanation.lower() and 'giovanni' not in explanation.lower():
                self.log_result("AI Study Tools", False, 
                              f"AI explanation doesn't seem relevant to the verse: {explanation[:200]}")
                return
            
            self.log_result("AI Study Tools", True, 
                          f"AI explanation generated successfully ({len(explanation)} chars)")
            
        except requests.exceptions.RequestException as e:
            self.log_result("AI Study Tools", False, f"Request error: {str(e)}")
        except Exception as e:
            self.log_result("AI Study Tools", False, f"Unexpected error: {str(e)}")
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
        """Run all Bible API tests as specified in the review request"""
        print("🔍 Starting Comprehensive Bible API Tests for Amen! App")
        print(f"📡 Testing backend at: {BACKEND_URL}")
        print("=" * 80)
        
        # 1. CRITICAL: Multi-language Bible Content Tests
        print("\n🌍 CRITICAL: Testing Multi-Language Bible Content")
        print("-" * 50)
        self.test_multi_language_bible_content()
        
        # 2. Authentication Tests
        print("\n🔐 Testing Authentication Endpoints")
        print("-" * 50)
        self.test_user_registration()
        self.test_user_login()
        
        # 3. AI Study Tools Tests
        print("\n🤖 Testing AI Study Tools")
        print("-" * 50)
        self.test_ai_study_tools()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Group results by category
        multi_lang_tests = [r for r in self.results if any(lang in r['test'] for lang in ['Italian', 'Spanish', 'English', 'German', 'French', 'Portuguese'])]
        auth_tests = [r for r in self.results if 'Registration' in r['test'] or 'Login' in r['test']]
        ai_tests = [r for r in self.results if 'AI Study' in r['test']]
        
        print(f"\n🌍 Multi-Language Tests: {sum(1 for r in multi_lang_tests if r['success'])}/{len(multi_lang_tests)} passed")
        print(f"🔐 Authentication Tests: {sum(1 for r in auth_tests if r['success'])}/{len(auth_tests)} passed")
        print(f"🤖 AI Study Tools Tests: {sum(1 for r in ai_tests if r['success'])}/{len(ai_tests)} passed")
        
        if total - passed > 0:
            print(f"\n❌ FAILED TESTS ({total - passed}):")
            for result in self.results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['details']}")
        
        print(f"\n✅ PASSED TESTS ({passed}):")
        for result in self.results:
            if result['success']:
                print(f"  • {result['test']}: {result['details']}")
        
        # Special focus on critical multi-language requirement
        multi_lang_passed = sum(1 for r in multi_lang_tests if r['success'])
        if multi_lang_passed < len(multi_lang_tests):
            print(f"\n⚠️  CRITICAL ISSUE: Multi-language Bible content not fully working!")
            print(f"   Only {multi_lang_passed}/{len(multi_lang_tests)} language tests passed.")
            print("   This is the PRIMARY requirement from the review request.")
        
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