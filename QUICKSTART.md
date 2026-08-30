# MugX Print Plugin - Quick Start

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Run the Application

```bash
python main.py
```

This will:
- Create the `D:/SublimationBag` folder structure (or your configured root)
- Initialize all core services
- Scan for templates and photos

## 3. Folder Structure

The application expects this structure:

```
D:/SublimationBag/
├── Customer/Photo/       # Place customer photos here (01.jpg, 02.jpg, ...)
├── Templates/Mug/        # PSD templates for mugs
├── Templates/Bottle/     # PSD templates for bottles
├── Background/           # Background images
├── PNG Data/             # Bokeh, clipart, text, alphabet
└── Auto/                 # Auto-saved exports
```

## 4. Add Photos

Place customer photos in `D:/SublimationBag/Customer/Photo/`. The software will auto-rename them sequentially (01, 02, 03...).

## 5. Use the Photoshop Panel

Open Photoshop, then load the MugX panel (CEP extension). Use the panel buttons to:
- Open photos
- Select templates
- Auto-fill photos
- Customize designs
- Prepare for print

## 6. Test Auto-Fill

1. Place 6 photos in the Customer/Photo folder
2. Open a 6-photo mug template
3. Click "6 Photo" or "Auto Fill"
4. Photos 01-06 will be placed in order

## Configuration

Set `MUGX_DATA_ROOT` environment variable to change the data folder:

```bash
export MUGX_DATA_ROOT=/path/to/data  # Linux/Mac
set MUGX_DATA_ROOT=C:\path\to\data   # Windows CMD
$env:MUGX_DATA_ROOT="C:\path\to\data"  # PowerShell
```
