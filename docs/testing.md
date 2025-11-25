# Testing Documentation

This project includes comprehensive unit tests for the Koa Sonos StreamDeck controller.

## Test Coverage

### Files Tested
- **`sonos_streamdeck.py`**: Main StreamDeck controller logic (29 tests)
  - Network utilities (IP detection)
  - Sonos playback control (toggle loop, podcast playback)
  - StreamDeck UI (button images, volume display)
  - Event handlers (button presses, dial turns)
  
- **`fetch_podcasts.py`**: Podcast RSS feed management (20 tests)
  - Text slugification
  - Episode downloading
  - Directory management
  - Cleanup of old episodes

## Running Tests

### Run All Tests
```bash
python3 -m pytest -v
```

### Run Specific Test File
```bash
python3 -m pytest tests/test_sonos_streamdeck.py -v
python3 -m pytest tests/test_fetch_podcasts.py -v
```

### Run Specific Test
```bash
python3 -m pytest tests/test_sonos_streamdeck.py::test_toggle_loop_starts_playback_when_stopped -v
```

### Run Tests Matching a Pattern
```bash
python3 -m pytest -k "dial" -v  # Run all dial-related tests
python3 -m pytest -k "podcast" -v  # Run all podcast-related tests
```

## Test Architecture

### Hardware Mocking
The tests mock out hardware dependencies to run without actual hardware:
- **StreamDeck**: Mocked in `conftest.py` - no physical StreamDeck device required
- **Sonos Speaker**: Mocked with a `MockSpeaker` class that simulates volume control and playback
- **Network Requests**: Mocked using `requests-mock` for podcast downloads

### Key Test Fixtures
- `mock_speaker`: Simulated Sonos speaker with volume control
- `mock_deck`: Simulated StreamDeck device
- `temp_podcast_dir`: Temporary directory for testing file operations
- `requests_mock`: HTTP request mocking for podcast downloads

### Test Organization
- **`tests/`**: Test directory containing all test files
  - **`conftest.py`**: Shared test configuration and hardware mocking setup
  - **`test_sonos_streamdeck.py`**: Tests for StreamDeck control and Sonos integration
  - **`test_fetch_podcasts.py`**: Tests for podcast feed parsing and downloading
  - **`__init__.py`**: Package initialization

## Important Notes

1. **Hardware Independence**: Tests run completely without hardware - StreamDeck and Sonos are fully mocked
2. **Test Isolation**: Each test runs independently with fresh fixtures
3. **No Side Effects**: Tests use temporary directories and don't modify actual files
4. **Fast Execution**: Full test suite runs in ~0.1 seconds

## Continuous Development

These tests ensure that functionality remains intact when refactoring or adding features. Always run the test suite before and after making changes:

```bash
# Before changes
python3 -m pytest -v

# Make your changes...

# After changes
python3 -m pytest -v
```

If tests fail, the output will show exactly which functionality broke, making debugging much easier.

