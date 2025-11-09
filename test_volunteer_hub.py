"""
Volunteer Hub API Test Suite for Windows
Easy testing of all platform features without curl commands
"""

import requests
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-user-windows-123"


class Colors:
    """ANSI color codes for Windows Terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")


def print_json(data: Any):
    """Pretty print JSON data"""
    print(f"{Colors.YELLOW}{json.dumps(data, indent=2)}{Colors.END}")


def test_api_connection() -> bool:
    """Test basic API connectivity"""
    print_header("1. Testing API Connection")

    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("API is running!")
            print_info(f"Service: {data['service']}")
            print_info(f"Version: {data['version']}")
            print_info(f"Status: {data['status']}")
            print_info(f"Features: {json.dumps(data.get('features', {}), indent=2)}")
            return True
        else:
            print_error(f"API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API. Is docker-compose running?")
        print_info("Run: docker-compose up -d")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_health_check() -> bool:
    """Test health endpoint"""
    print_header("2. Testing Health Check")

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Health check passed!")
            print_json(data)
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_create_offer() -> Optional[str]:
    """Test creating an offer"""
    print_header("3. Testing Offer Creation")

    offer_data = {
        "person_id": TEST_USER_ID,
        "item_type": "breadfruit",
        "quantity": 25,
        "unit": "lbs",
        "available_until": "2024-12-31T18:00:00Z"
    }

    print_info("Creating offer:")
    print_json(offer_data)

    try:
        response = requests.post(
            f"{API_BASE_URL}/offers",
            json=offer_data,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Offer created: {data['message']}")
            offer_id = data.get('offer_id')
            print_info(f"Offer ID: {offer_id}")
            return offer_id
        else:
            print_error(f"Failed to create offer: {response.status_code}")
            print_error(response.text)
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def test_find_needs() -> list:
    """Test finding needs"""
    print_header("4. Testing Need Search")

    try:
        # Search for breadfruit needs
        response = requests.get(
            f"{API_BASE_URL}/needs",
            params={"item_type": "breadfruit"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            needs = data.get('needs', [])
            print_success(f"Found {len(needs)} matching needs")

            if needs:
                print_info("Sample needs:")
                print_json(needs[:3])  # Show first 3
            else:
                print_info("No needs found (this is expected in fresh database)")

            return needs
        else:
            print_error(f"Failed to search needs: {response.status_code}")
            return []
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return []


def test_create_digital_twin_without_photo() -> Optional[str]:
    """Test digital twin creation with context only (no photo)"""
    print_header("5. Testing Digital Twin Creation (Context Only)")

    context = {
        "location": "backyard lo'i, Lower Puna, Hawaii",
        "backstory": "4-month-old Lehua Maoli kalo planted from Aunty Momi's huli from Waipi'o Valley",
        "notes": "Healthy growth, slight thrip damage on leaf margins, recent heavy rains",
        "type": "kalo plant",
        "variety": "Lehua Maoli"
    }

    print_info("Creating digital twin with context:")
    print_json(context)

    try:
        # For testing without actual photo, we'll create a minimal dummy file
        files = {
            'photo': ('test.txt', b'dummy photo content', 'text/plain')
        }
        data = {
            'owner_id': TEST_USER_ID,
            'context': json.dumps(context)
        }

        response = requests.post(
            f"{API_BASE_URL}/digital-twin/create",
            files=files,
            data=data,
            timeout=30  # Longer timeout for AI processing
        )

        if response.status_code == 200:
            result = response.json()
            print_success("Digital twin created!")
            print_info(f"Twin ID: {result.get('twin_id')}")
            print_info(f"Entity Type: {result.get('entity_type')}")
            print_info(f"\nInitial Greeting:")
            print(f"{Colors.CYAN}{result.get('initial_greeting', 'N/A')}{Colors.END}")
            print_info(f"\nPersonality Traits:")
            print_json(result.get('personality_traits', {}))
            return result.get('twin_id')
        else:
            print_error(f"Failed to create digital twin: {response.status_code}")
            print_error(response.text)
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def test_converse_with_twin(twin_id: str):
    """Test conversation with digital twin"""
    print_header("6. Testing Digital Twin Conversation")

    if not twin_id:
        print_error("No twin_id provided, skipping conversation test")
        return

    messages = [
        "How are you doing today?",
        "What do you need right now?",
        "Tell me about your connection to Waipi'o Valley"
    ]

    for i, message in enumerate(messages, 1):
        print_info(f"\nMessage {i}: {message}")

        try:
            response = requests.post(
                f"{API_BASE_URL}/digital-twin/{twin_id}/converse",
                json={"message": message},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                print(f"{Colors.GREEN}Twin Response:{Colors.END}")
                print(f"{Colors.CYAN}{data.get('response', 'No response')}{Colors.END}")
                time.sleep(1)  # Brief pause between messages
            else:
                print_error(f"Conversation failed: {response.status_code}")
                print_error(response.text)
        except Exception as e:
            print_error(f"Error: {str(e)}")


def test_twin_memories(twin_id: str):
    """Test retrieving twin memories"""
    print_header("7. Testing Digital Twin Memory Retrieval")

    if not twin_id:
        print_error("No twin_id provided, skipping memory test")
        return

    try:
        response = requests.get(
            f"{API_BASE_URL}/digital-twin/{twin_id}/memories",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {data.get('count', 0)} memories")

            memories = data.get('memories', [])
            if memories:
                print_info("Recent memories:")
                print_json(memories[:3])  # Show first 3
            else:
                print_info("No memories yet (expected if just created)")
        else:
            print_error(f"Failed to retrieve memories: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {str(e)}")


def test_voice_session():
    """Test voice session creation"""
    print_header("8. Testing Voice Session Creation")

    session_data = {
        "person_id": TEST_USER_ID,
        "language": "en"
    }

    print_info("Creating voice session:")
    print_json(session_data)

    try:
        response = requests.post(
            f"{API_BASE_URL}/voice/session",
            json=session_data,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success("Voice session created!")
            print_info(f"Session ID: {data.get('session_id')}")
            print_info(f"Active Agents: {data.get('active_agents')}")
            print_info(f"Language: {data.get('language')}")
            print_info(f"Status: {data.get('status')}")
            return data.get('session_id')
        else:
            print_error(f"Failed to create session: {response.status_code}")
            print_error(response.text)
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def test_debug_endpoints():
    """Test debug endpoints"""
    print_header("9. Testing Debug Endpoints")

    # Test active agents
    print_info("Checking active agents...")
    try:
        response = requests.get(f"{API_BASE_URL}/debug/agents", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Active agents: {data.get('active_agents', 0)}")
            if data.get('agents'):
                print_json(data['agents'])
    except Exception as e:
        print_error(f"Error checking agents: {str(e)}")

    # Test active conversations
    print_info("\nChecking active conversations...")
    try:
        response = requests.get(f"{API_BASE_URL}/debug/conversations", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Active conversations: {data.get('active_conversations', 0)}")
            if data.get('sessions'):
                print_json(data['sessions'])
    except Exception as e:
        print_error(f"Error checking conversations: {str(e)}")


def test_create_offer_with_photo():
    """Test creating offer with photo (if available)"""
    print_header("10. Testing Offer Creation with Photo (Optional)")

    # Look for image files in current directory
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    current_dir = Path('.')

    image_files = []
    for ext in image_extensions:
        image_files.extend(current_dir.glob(f'*{ext}'))

    if not image_files:
        print_info("No image files found in current directory - skipping photo test")
        print_info("To test with photos, place a .jpg or .png file in this directory")
        return

    image_file = image_files[0]
    print_info(f"Found image: {image_file.name}")

    context = {
        "location": "Community garden, Lower Puna",
        "type": "garden photo",
        "notes": "Test photo upload"
    }

    try:
        with open(image_file, 'rb') as f:
            files = {
                'photo': (image_file.name, f, 'image/jpeg')
            }
            data = {
                'owner_id': TEST_USER_ID,
                'context': json.dumps(context)
            }

            response = requests.post(
                f"{API_BASE_URL}/digital-twin/create",
                files=files,
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                print_success("Digital twin created with photo!")
                print_json(result)
            else:
                print_error(f"Failed: {response.status_code}")
                print_error(response.text)
    except Exception as e:
        print_error(f"Error: {str(e)}")


def run_all_tests():
    """Run complete test suite"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("   VOLUNTEER HUB API TEST SUITE FOR WINDOWS")
    print("=" * 60)
    print(f"{Colors.END}")

    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"Test User ID: {TEST_USER_ID}")
    print_info("Press Ctrl+C to stop at any time\n")

    time.sleep(1)

    # Run tests in sequence
    if not test_api_connection():
        print_error("\nAPI connection failed. Stopping tests.")
        print_info("Make sure Docker is running: docker-compose up -d")
        return

    if not test_health_check():
        print_error("\nHealth check failed. Some features may not work.")

    # Core functionality tests
    offer_id = test_create_offer()
    needs = test_find_needs()

    # Digital twin tests
    twin_id = test_create_digital_twin_without_photo()
    if twin_id:
        test_converse_with_twin(twin_id)
        test_twin_memories(twin_id)

    # Voice session test
    session_id = test_voice_session()

    # Debug endpoints
    test_debug_endpoints()

    # Optional: Photo test
    test_create_offer_with_photo()

    # Summary
    print_header("TEST SUMMARY")
    print_success("All tests completed!")
    print_info("\nWhat was tested:")
    print("  ✓ API connectivity")
    print("  ✓ Health checks")
    print("  ✓ Offer creation")
    print("  ✓ Need searching")
    print("  ✓ Digital twin generation")
    print("  ✓ Twin conversation")
    print("  ✓ Memory retrieval")
    print("  ✓ Voice session creation")
    print("  ✓ Debug endpoints")

    print_info("\nNext steps:")
    print("  1. View API docs: http://localhost:8000/docs")
    print("  2. Check logs: docker-compose logs -f api")
    print("  3. Access database: docker-compose exec postgres psql -U hub -d volunteer_hub")

    if twin_id:
        print_info(f"\nYour digital twin ID: {twin_id}")
        print_info("Try conversing with it using the /digital-twin/{twin_id}/converse endpoint!")


def interactive_mode():
    """Interactive testing mode"""
    print_header("INTERACTIVE MODE")
    print_info("Type 'help' for commands, 'quit' to exit")

    twin_id = None

    while True:
        try:
            command = input(f"\n{Colors.CYAN}> {Colors.END}").strip().lower()

            if command == 'quit' or command == 'exit':
                print_info("Goodbye!")
                break
            elif command == 'help':
                print_info("Available commands:")
                print("  test - Run all tests")
                print("  offer - Create an offer")
                print("  twin - Create digital twin")
                print("  talk - Talk to twin (requires twin creation first)")
                print("  session - Create voice session")
                print("  status - Check API status")
                print("  quit - Exit")
            elif command == 'test':
                run_all_tests()
            elif command == 'offer':
                test_create_offer()
            elif command == 'twin':
                twin_id = test_create_digital_twin_without_photo()
            elif command == 'talk':
                if twin_id:
                    msg = input(f"{Colors.YELLOW}Your message: {Colors.END}")
                    test_converse_with_twin(twin_id)
                else:
                    print_error("Create a twin first with 'twin' command")
            elif command == 'session':
                test_voice_session()
            elif command == 'status':
                test_api_connection()
                test_health_check()
            else:
                print_error(f"Unknown command: {command}")
                print_info("Type 'help' for available commands")
        except KeyboardInterrupt:
            print_info("\nGoodbye!")
            break
        except Exception as e:
            print_error(f"Error: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        interactive_mode()
    else:
        run_all_tests()
