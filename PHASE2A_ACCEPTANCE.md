# Phase 2A Acceptance Evidence — Stabilized Photoshop Bridge

## Installation & Testing Record

**Date:** August 28, 2026  
**Photoshop Version:** 27.9.1  
**Branch:** `phase2a-bridge-stabilize`  
**Commit:** `977b45743c51abfe95e059ab954f2831d4a692c2`

---

## ✅ Acceptance Criteria Checklist

### 1. Extension Loads Successfully
- [ ] Extension appears in Photoshop 27.9.1: **Window → Extensions → MugX Panel**
- [ ] Panel opens without errors
- [ ] No console errors in Photoshop

### 2. Version Reporting
- [ ] Panel reports "Adobe Photoshop 27.9.1" correctly
- [ ] `pingPhotoshop()` returns correct version string
- [ ] `getPhotoshopInfo()` returns full application details

### 3. Five Verified Bridge Calls

#### ✅ pingPhotoshop()
**Expected Response:**
```javascript
{
  success: true,
  timestamp: <number>,
  appName: "Adobe Photoshop",
  version: "27.9.1",
  build: "27.9.1"
}
```
**Test Status:** [ ] PASS / [ ] FAIL

#### ✅ getPhotoshopInfo()
**Expected Response:**
```javascript
{
  success: true,
  name: "Adobe Photoshop",
  version: "27.9.1",
  build: "27.9.1",
  platform: "macOS" | "Windows",
  language: "en_US",
  path: "<photoshop_path>",
  preferencesFolder: "<prefs_path>",
  systemInformation: "<system_info>"
}
```
**Test Status:** [ ] PASS / [ ] FAIL

#### ✅ getDocumentInfo()
**Expected Response (with document open):**
```javascript
{
  success: true,
  documentCount: 1,
  name: "<filename>.psd",
  width: <number>,
  height: <number>,
  resolution: 300,
  mode: "RGBM" | "CMYK" | "GRAY",
  bitDepth: 8 | 16 | 32,
  layerCount: <number>,
  activeLayer: "<layer_name>",
  filePath: "<full_path>"
}
```
**Test Status:** [ ] PASS / [ ] FAIL

#### ✅ getLayerList()
**Expected Response:**
```javascript
{
  success: true,
  layerCount: <number>,
  layers: [
    {
      index: 0,
      name: "Layer 1",
      kind: "artLayer" | "layerSet",
      visible: true,
      opacity: 100,
      isBackgroundLayer: false,
      locked: false,
      parentIndex: -1
    }
  ]
}
```
**Test Status:** [ ] PASS / [ ] FAIL

#### ✅ addTestLayer()
**Expected Response:**
```javascript
{
  success: true,
  layerName: "MugX Test Layer",
  layerIndex: <number>,
  message: "Test layer added successfully"
}
```
**Test Status:** [ ] PASS / [ ] FAIL

### 4. Error Handling

#### ✅ EvalScript Error = FAILURE
- [ ] `main.js` treats `"EvalScript error."` as failure
- [ ] Panel displays error message, not false success
- [ ] Status indicator shows red/error state

#### ✅ Bridge Error Handling
- [ ] Errors return `{ _error: true, name, message, line }`
- [ ] Panel correctly identifies and displays errors
- [ ] No uncaught exceptions in panel

### 5. Panel Behavior
- [ ] Panel does NOT report false success
- [ ] Connection status updates correctly
- [ ] Error messages are user-friendly
- [ ] Results are properly formatted in JSON

---

## Installation Instructions

### Step 1: Enable Developer Mode

**macOS:**
```bash
defaults write com.adobe.CSXS.9 PlayerDebugMode 1
```

**Windows:**
```reg
HKEY_CURRENT_USER\Software\Adobe\CSXS.9
"PlayerDebugMode"="1"
```

### Step 2: Install Extension

**macOS:**
```bash
# Copy extension folder to:
~/Library/Application Support/Adobe/CEP/extensions/mugx-photoshop/
```

**Windows:**
```bash
# Copy extension folder to:
%APPDATA%\Adobe\CEP\extensions\mugx-photoshop\
```

### Step 3: Restart Photoshop
1. Close Photoshop completely
2. Reopen Photoshop 27.9.1
3. Go to **Window → Extensions → MugX Panel**

### Step 4: Verify Installation
1. Panel should appear with "MugX Photoshop Bridge" title
2. Status should show "Connecting..." then "Connected"
3. All test buttons should be enabled

---

## Test Procedure

### Test 1: Basic Connectivity
1. Click **"Ping Photoshop"** button
2. Verify response shows:
   - `success: true`
   - Correct `appName`, `version`, `build`
3. Status should show green "Connected"

### Test 2: Application Info
1. Click **"Get PS Info"** button
2. Verify response includes:
   - `platform` (macOS/Windows)
   - `language`
   - `path` to Photoshop
   - `systemInformation`

### Test 3: Document Info
1. Open any PSD file in Photoshop
2. Click **"Get Doc Info"** button
3. Verify response includes:
   - Document `name`, `width`, `height`
   - `resolution`, `mode`, `layerCount`
   - `activeLayer` name

### Test 4: Layer List
1. With document still open
2. Click **"Get Layers"** button
3. Verify response includes:
   - `layerCount` matches Photoshop
   - `layers` array with correct layer info
   - Each layer has `index`, `name`, `kind`, `visible`

### Test 5: Add Test Layer
1. Click **"Add Test Layer"** button
2. Verify response shows:
   - `success: true`
   - `layerName: "MugX Test Layer"`
3. Check Photoshop Layers panel - new layer should appear

### Test 6: Error Handling
1. Close all documents in Photoshop
2. Click **"Get Doc Info"** button
3. Verify response shows:
   - `success: false`
   - `error: "No open documents"`
4. Status should show red error state

---

## Evidence Log

### Test Execution Record

| Test | Timestamp | Result | Notes |
|------|-----------|--------|-------|
| Extension Load | | PASS / FAIL | |
| Ping Photoshop | | PASS / FAIL | |
| Get PS Info | | PASS / FAIL | |
| Get Doc Info | | PASS / FAIL | |
| Get Layers | | PASS / FAIL | |
| Add Test Layer | | PASS / FAIL | |
| Error Handling | | PASS / FAIL | |

### Screenshot Evidence

1. **Panel loaded in Photoshop 27.9.1**
   - [ ] Screenshot captured

2. **Ping Photoshop response**
   - [ ] Screenshot captured

3. **Get Layers response**
   - [ ] Screenshot captured

4. **Add Test Layer in Photoshop**
   - [ ] Screenshot captured

5. **Error handling (no document)**
   - [ ] Screenshot captured

---

## Sign-off

**Tester:** _________________  
**Date:** _________________  
**Photoshop Version:** 27.9.1  
**Platform:** macOS / Windows  

**Overall Result:** [ ] PASS / [ ] FAIL  

**Notes:**
```
[Add any observations, issues, or comments here]
```

---

## Next Phase

Upon successful completion of Phase 2A acceptance:
- Merge `phase2a-bridge-stabilize` to `v2` branch
- Begin Phase 2B: Template Browser Integration
- Proceed to Milestone 2: Product Catalog

---

## File Manifest

| File | Purpose |
|------|---------|
| `CSXS/manifest.xml` | CEP extension manifest |
| `host/index.jsx` | ExtendScript bridge functions |
| `client/index.html` | Panel UI |
| `client/CSInterface.js` | CEP interface library |
| `main.js` | Error handling (EvalScript = FAILURE) |
| `README_PHASE2A.md` | Installation & testing guide |
| `PHASE2A_ACCEPTANCE.md` | This acceptance document |
