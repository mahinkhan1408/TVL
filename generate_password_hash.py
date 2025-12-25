#!/usr/bin/env python3
"""
Password Hash Generator
Generate bcrypt password hashes for Supabase users
"""

import bcrypt
import sys

def generate_password_hash(password):
    """Generate a bcrypt hash for a password"""
    # Generate a salt and hash the password
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt)
    return password_hash.decode('utf-8')

def main():
    print("=" * 60)
    print("Password Hash Generator for Supabase Users")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        # Password provided as command line argument
        password = sys.argv[1]
    else:
        # Ask for password interactively
        password = input("Enter password to hash: ").strip()
        if not password:
            print("Error: Password cannot be empty")
            return
    
    # Generate hash
    password_hash = generate_password_hash(password)
    
    print()
    print("Generated Password Hash:")
    print("-" * 60)
    print(password_hash)
    print("-" * 60)
    print()
    print("SQL INSERT statement:")
    print("-" * 60)
    print(f"INSERT INTO users (username, password_hash, created_at)")
    print(f"VALUES ('USERNAME_HERE', '{password_hash}', NOW());")
    print("-" * 60)
    print()
    print("Or use this hash directly in your SQL:")
    print(f"'{password_hash}'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

