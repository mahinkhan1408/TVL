# Checksum Verification Guide

## Overview

The update system now includes SHA256 checksum verification to ensure download integrity and security.

## How It Works

1. **Checksum Extraction**: The update manager automatically looks for checksums in two places:
   - `.sha256` or `.sha256sum` files attached to GitHub releases
   - Release notes (text format)

2. **Verification**: During download, the updater:
   - Calculates SHA256 hash of the downloaded file
   - Compares it against the expected checksum
   - Rejects the download if checksums don't match

## For Release Managers

### Option 1: Checksum File (Recommended)

Create a `.sha256` file containing the SHA256 hash of your EXE:

```bash
# Generate checksum on Windows (PowerShell)
Get-FileHash -Path PreservationApp.exe -Algorithm SHA256 | Select-Object -ExpandProperty Hash | Out-File -Encoding ASCII PreservationApp.exe.sha256

# Or on Linux/Mac
sha256sum PreservationApp.exe > PreservationApp.exe.sha256
```

**File format**: The file can contain:
- Just the hash: `a1b2c3d4e5f6...` (64 hex characters)
- Hash with filename: `a1b2c3d4e5f6...  PreservationApp.exe`
- Any format - the system extracts the first 64-char hex string

**Upload to GitHub**: Attach `PreservationApp.exe.sha256` as a release asset alongside your EXE.

### Option 2: Release Notes

Include the checksum in your GitHub release notes:

```
## Version 1.0.1

SHA256: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456

Bug fixes and improvements...
```

The system will automatically extract the checksum from the release notes.

## Checksum Verification Process

1. **Download**: File is downloaded in chunks
2. **Hash Calculation**: SHA256 is calculated during download (streaming)
3. **Size Verification**: Downloaded size is compared to `Content-Length` header
4. **Checksum Verification**: Calculated hash is compared to expected checksum
5. **Replacement**: Only if all verifications pass, the old EXE is replaced

## Security Benefits

✅ **Integrity**: Ensures file wasn't corrupted during download  
✅ **Authenticity**: Verifies file matches what was published  
✅ **Protection**: Prevents malicious file substitution  
✅ **Reliability**: Catches network transmission errors  

## Fallback Behavior

If no checksum is provided:
- Download proceeds normally
- Size verification still occurs (if `Content-Length` header is present)
- File existence and non-empty checks are performed
- Warning is logged: "No expected checksum provided"

## Logging

Checksum verification is logged in `updater.log`:

```
[2024-01-01 12:00:00] Downloaded file SHA256: a1b2c3d4e5f6...
[2024-01-01 12:00:00] Checksum verification passed
```

If verification fails:
```
[2024-01-01 12:00:00] ERROR: Checksum mismatch!
[2024-01-01 12:00:00]   Expected: a1b2c3d4e5f6...
[2024-01-01 12:00:00]   Calculated: f6e5d4c3b2a1...
```

## Best Practices

1. **Always provide checksums** for production releases
2. **Use checksum files** for automated extraction
3. **Include in release notes** as backup/documentation
4. **Verify locally** before publishing release
5. **Test update process** with checksum verification enabled

## Troubleshooting

**"No checksum found"**
- Checksum file not attached to release
- Checksum not in release notes
- System will proceed with size verification only

**"Checksum mismatch"**
- File was corrupted during download
- Wrong file was uploaded
- Network transmission error
- **Action**: Download is rejected, backup is restored

**"Size mismatch"**
- Download was interrupted
- Network error occurred
- **Action**: Download is rejected, backup is restored

