#!/usr/bin/env python3

import os
from pi4.auth.utils import get_password_hash

# Test with a long password that exceeds 72 bytes
long_password = "a" * 80  # 80 characters - well over the limit

print(f"Testing long password: {len(long_password)} characters")
print(f"First 50 chars: '{long_password[:50]}'")

try:
    hashed_password = get_password_hash(long_password)
    print("SUCCESS: Long password hash created")
    print(f"Hash length: {len(hashed_password)}")
except Exception as e:
    print(f"ERROR: {e}")

# Now test with a shorter one to make sure we didn't break anything
short_password = "password123"
print(f"\nTesting short password: {len(short_password)} characters")

try:
    hashed_password = get_password_hash(short_password)
    print("SUCCESS: Short password hash created")
    print(f"Hash length: {len(hashed_password)}")
except Exception as e:
    print(f"ERROR: {e}")
