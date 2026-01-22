# Quick Start: Update System Setup

## 1. Install Dependencies

```bash
pip install packaging psutil
```

## 2. Configure GitHub Repository

Edit `main.py` and update these lines:

```python
GITHUB_REPO = "your-org/your-repo"  # Change to your GitHub repository
APP_VERSION = "1.0.0"  # Update for each release
```

## 3. Build Updater Executable

Run:
```bash
build_updater.bat
```

Or manually:
```bash
pyinstaller updater.spec
```

Copy `dist/updater.exe` to your app directory (same folder as `PreservationApp.exe`).

## 4. Create Your First Release

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag: `v1.0.1` (use semantic versioning)
4. Title: `Version 1.0.1`
5. Upload `PreservationApp.exe` as a release asset
6. Add release notes
7. Click "Publish release"

## 5. Test the Update

1. Set `APP_VERSION = "1.0.0"` in `main.py`
2. Run your app
3. It should detect version `1.0.1` is available
4. Click "Update Now" to test the update flow

## File Structure After Setup

```
Your App Directory/
├── PreservationApp.exe    # Main application
├── updater.exe           # Update executable (from build)
├── version.txt           # Current version (auto-managed)
├── update.log            # Update manager logs
└── updater.log           # Updater process logs
```

## Troubleshooting

**Update not detected?**
- Check `update.log` for errors
- Verify GitHub repository name is correct
- Ensure release has `.exe` asset
- Check version format (must be semantic: `1.0.0`)

**Updater not found?**
- Make sure `updater.exe` is in the same directory as `PreservationApp.exe`
- Rebuild updater using `build_updater.bat`

**Manual update check?**
- Go to Settings → Updates → "Check for Updates"

## Next Steps

- Update `APP_VERSION` in `main.py` for each release
- Create GitHub releases with new EXE files
- Users will automatically be notified of updates

