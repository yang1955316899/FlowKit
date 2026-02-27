# Quick Start Guide - Electron UI

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Installation

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies
```bash
cd src/frontend
npm install
```

## Running the Application

### Development Mode

**Terminal 1 - Start Python Backend:**
```bash
python -m src.app
```
The backend will start on `http://localhost:18900`

**Terminal 2 - Start Electron Frontend:**
```bash
cd src/frontend
npm run dev
```

The Electron app will launch automatically.

### Production Mode

**Build Frontend:**
```bash
cd src/frontend
npm run build
```

**Package Electron App:**
```bash
npm run electron:build
```

## New Features

### 1. Recorder (`/recorder`)
- Record keyboard and mouse operations
- Auto-generate flow steps
- Save recordings as flows

### 2. Script Editor (`/script-editor`)
- Write and execute Python scripts
- Real-time output display
- Syntax highlighting

### 3. Coordinate Picker
- Available in flow editor
- Click to pick screen coordinates
- Used for mouse actions

## API Endpoints

All APIs are available at `http://localhost:18900/api/v1/`

### Recorder
- `POST /recorder/start` - Start recording
- `POST /recorder/stop` - Stop and get steps
- `POST /recorder/pause` - Pause/resume
- `GET /recorder/status` - Get status

### Input Capture
- `POST /input/pick-coordinate` - Pick coordinates

### Stats
- `GET /stats/actions` - Action statistics
- `GET /stats/overview` - Overview stats

### Pages
- `GET /pages` - List pages
- `POST /pages` - Create page
- `PUT /pages/{idx}` - Update page
- `DELETE /pages/{idx}` - Delete page

### Scripts
- `GET /scripts` - List scripts
- `POST /scripts/execute` - Execute script

### Theme
- `PUT /theme` - Switch theme

## Testing

Run API tests:
```bash
./test_apis.sh
```

## Troubleshooting

### Backend not starting
- Check if port 18900 is available
- Verify Python dependencies are installed

### Frontend not connecting
- Ensure backend is running first
- Check browser console for errors
- Verify API base URL in frontend config

### Recorder not working
- Requires Windows (uses Windows hooks)
- Run with administrator privileges if needed

## Migration Notes

- Python UI (Tkinter) has been removed
- All UI functionality now in Electron
- Backend is pure API server
- Configuration file format unchanged

## Support

For issues or questions, check:
- `MIGRATION_COMPLETE.md` - Full migration details
- GitHub Issues - Report bugs
- Documentation - User guides
