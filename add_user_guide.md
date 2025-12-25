# Guide: Adding New Users to Supabase

This guide shows you how to add new users to your Supabase database.

## Method 1: Using the Password Hash Generator Script (Recommended)

### Step 1: Generate Password Hash

Run the password hash generator script:

```bash
python generate_password_hash.py
```

When prompted, enter the password you want to use.

**Example:**
```
$ python generate_password_hash.py
Enter password to hash: mypassword123

Generated Password Hash:
------------------------------------------------------------
$2b$12$gNzmaTA3LTEAuZ10yUA5iOfJSR20ZcqnE58lh9bmFKbGpJBM08dv.
------------------------------------------------------------
```

### Step 2: Copy the Generated Hash

Copy the hash string that was generated.

### Step 3: Use in SQL Insert Statement

Go to Supabase Dashboard → SQL Editor and run:

```sql
INSERT INTO users (username, password_hash, created_at)
VALUES ('NewUsername', '$2b$12$gNzmaTA3LTEAuZ10yUA5iOfJSR20ZcqnE58lh9bmFKbGpJBM08dv.', NOW())
ON CONFLICT (username) DO UPDATE 
SET password_hash = EXCLUDED.password_hash;
```

Replace:
- `'NewUsername'` with the actual username
- `'$2b$12$...'` with the hash you copied from Step 2

---

## Method 2: Using Python Command Line (Quick)

If you know the password, you can generate the hash directly:

```bash
python -c "import bcrypt; print(bcrypt.hashpw('yourpassword'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))"
```

Replace `'yourpassword'` with the actual password.

**Example:**
```bash
python -c "import bcrypt; print(bcrypt.hashpw('abcde'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))"
```

Then use the generated hash in the SQL INSERT statement as shown in Method 1.

---

## Method 3: Update Existing User Password

To change an existing user's password:

```sql
UPDATE users 
SET password_hash = 'PASTE_GENERATED_HASH_HERE'
WHERE username = 'UsernameHere';
```

---

## Complete Example: Adding a New User

1. **Generate hash:**
   ```bash
   python generate_password_hash.py
   # Enter: mynewpassword
   ```

2. **Copy the hash** from the output

3. **Run SQL in Supabase:**
   ```sql
   INSERT INTO users (username, password_hash, created_at)
   VALUES ('John', '$2b$12$gNzmaTA3LTEAuZ10yUA5iOfJSR20ZcqnE58lh9bmFKbGpJBM08dv.', NOW());
   ```

4. **Verify the user was created:**
   ```sql
   SELECT id, username, created_at FROM users WHERE username = 'John';
   ```

---

## Troubleshooting

**Error: "bcrypt module not found"**
- Install bcrypt: `pip install bcrypt`

**Error: "Username already exists"**
- Use `ON CONFLICT` clause in INSERT to update existing user
- Or use UPDATE statement to change password only

**Password doesn't work after adding user**
- Make sure you copied the entire hash string (it should start with `$2b$12$`)
- Verify the hash was inserted correctly: `SELECT password_hash FROM users WHERE username = 'YourUsername';`

