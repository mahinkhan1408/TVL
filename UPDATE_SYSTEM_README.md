# Automatic Update System Documentation

## Overview

The Preservation Universe App includes a robust automatic update system that:
- Checks for updates from GitHub Releases
- Downloads and installs updates automatically
- Works reliably on Windows
- Handles failures gracefully
- Does not require user reinstallation

## Architecture

### Components

1. **update_manager.py** - Update checking and UI (used by main app)
2. **updater.py** - Standalone updater executable
3. **updater.exe** - Compiled updater (built from updater.py)
4. **version.txt** - Stores current app version

### Update Flow

```
App Startup
  ↓
Background Thread: Check GitHub Releases
  ↓
If Update Available → Show Modal Dialog
  ↓
User Accepts → Launch updater.exe → Exit App
  ↓
updater.exe:
  1. Wait for main.exe to exit
  2. Download new EXE
  3. Backup old EXE
  4. Replace old with new
  5. Update version.txt
  6. Restart main.exe
  7. Exit
```

## Setup Instructions

### 1. Configure GitHub Repository

Edit `main.py` and update:
```python
GITHUB_REPO = "your-org/your-repo"  # Your GitHub repository
APP_VERSION = "1.0.0"  # Current version
```

### 2. Install Dependencies

```bash
pip install packaging psutil
```

### 3. Build Updater Executable

```bash
pyinstaller updater.spec
```

This creates `dist/updater.exe`. Copy it to your app directory alongside `PreservationApp.exe`.

### 4. Create GitHub Release

1. Create a new release on GitHub
2. Tag it with version (e.g., `v1.0.1`)
3. Upload `PreservationApp.exe` as a release asset
4. Add release notes

### 5. Version Management

- Update `APP_VERSION` in `main.py` for each release
- Update `version.txt` file (or let updater handle it)
- Use semantic versioning: `MAJOR.MINOR.PATCH`

## Usage

### Automatic Check (Default)

Updates are checked automatically on app startup. If an update is available, a dialog appears.

### Manual Check

Add a menu option or button to check for updates:
```python
update_manager.check_for_updates(show_no_update_message=True)
```

## File Structure

```
App Directory/
├── PreservationApp.exe      # Main application
├── updater.exe             # Update executable
├── version.txt             # Current version
├── update.log              # Update manager logs
└── updater.log             # Updater process logs
```

## GitHub Release Format

Your GitHub releases should:
- Use semantic version tags: `v1.0.0`, `v1.0.1`, etc.
- Include `PreservationApp.exe` as a release asset
- Have release notes (shown in update dialog)

Example release:
- Tag: `v1.0.1`
- Asset: `PreservationApp.exe`
- Notes: "Bug fixes and improvements"

## Error Handling

The update system handles:
- **Network failures**: App continues normally, logs error
- **Partial downloads**: Validates file before replacing
- **Locked files**: Retries with exponential backoff
- **GitHub unreachable**: Silent failure, app continues
- **Update failures**: Restores backup automatically

## Logging

- `update.log` - Update manager operations
- `updater.log` - Updater process operations

Check these files for debugging update issues.

## Security Considerations

- Updates are downloaded from GitHub Releases (HTTPS)
- File integrity is verified (size checks)
- Backups are created before replacement
- Failed updates automatically restore previous version

## Testing

### Test Update Flow

1. Set `APP_VERSION` to `1.0.0` in `main.py`
2. Create GitHub release `v1.0.1` with new EXE
3. Run app - should detect update
4. Accept update - should download and restart

### Test Failure Cases

1. **Network failure**: Disconnect internet, app should continue
2. **Invalid release**: Create release without EXE asset, should handle gracefully
3. **Partial download**: Interrupt download, should restore backup

## Troubleshooting

### Update Not Detected

- Check `update.log` for errors
- Verify GitHub repository name is correct
- Ensure release has `.exe` asset
- Check version format (semantic versioning)

### Updater Fails

- Check `updater.log` for details
- Verify `updater.exe` exists in app directory
- Check file permissions
- Ensure main app exits before update

### App Won't Restart

- Check if EXE was replaced correctly
- Verify `version.txt` was updated
- Check `updater.log` for errors
- Manually restart app if needed

## Production Checklist

- [ ] Update `GITHUB_REPO` with actual repository
- [ ] Set correct `APP_VERSION` in `main.py`
- [ ] Build `updater.exe` using `updater.spec`
- [ ] Include `updater.exe` in distribution
- [ ] Test update flow end-to-end
- [ ] Create first GitHub release
- [ ] Verify update detection works
- [ ] Test rollback on failure

## Future Enhancements

Possible improvements:
- Checksum verification (SHA256)
- Delta updates (smaller downloads)
- Background download while app runs
- Update scheduling (check weekly)
- Rollback to previous version option

