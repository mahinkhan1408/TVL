# Simple Guide: Adding New Users to Supabase

Since passwords are stored in plain text, adding new users is very simple!

## Quick Method

Just run this SQL in Supabase Dashboard → SQL Editor:

```sql
INSERT INTO users (username, password_hash, created_at)
VALUES ('NewUsername', 'PlainTextPassword', NOW())
ON CONFLICT (username) DO UPDATE 
SET password_hash = EXCLUDED.password_hash;
```

**Example:**
```sql
-- Add a user named "John" with password "mypassword123"
INSERT INTO users (username, password_hash, created_at)
VALUES ('John', 'mypassword123', NOW())
ON CONFLICT (username) DO UPDATE 
SET password_hash = EXCLUDED.password_hash;
```

## Update Existing User Password

```sql
UPDATE users 
SET password_hash = 'NewPassword'
WHERE username = 'UsernameHere';
```

## Verify User Was Created

```sql
SELECT id, username, created_at FROM users WHERE username = 'NewUsername';
```

That's it! No hashing needed - just plain text passwords.

