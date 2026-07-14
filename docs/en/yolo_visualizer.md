# yolo_visualizer.py

Used to draw YOLO-format bounding boxes onto images, generating visualization results with annotated bounding boxes.

This script matches image files with their corresponding `.txt` label files by **filename**, automatically reads the annotation data, draws bounding boxes and class IDs on the images, and saves the results to a specified output directory.

---

## 1. Quick Start

### 1.1 Show help

```
python tools/yolo_visualizer.py --help
```

### 1.2 Basic usage

```
python tools/yolo_visualizer.py \
    --image_dir dataset/images \
    --label_dir dataset/labels \
    --output_dir dataset/visualization
```

### 1.3 Using a JSON config file

First prepare a config file, for example:

`json/yolo_visualizer.json`

```json
{
  "image_dir": "dataset/images",
  "label_dir": "dataset/labels",
  "output_dir": "dataset/visualization",
  "classes": ["person", "car", "dog"],
  "colors": [
    [0, 255, 0],
    [255, 0, 0],
    [0, 0, 255]
  ]
}
```

Run it with:

```
python tools/yolo_visualizer.py --config json/yolo_visualizer.json
```

The `classes` field in the config file supports two formats:

* **Inline list**: `["person", "car", "dog"]` — write class names directly in JSON
* **File path**: `"dataset/classes.txt"` — points to a classes.txt file, one class name per line

If `classes` is empty or omitted, labels fall back to the `class:0` format.

### 1.4 Argument description

| Argument | Description |
| -------- | ----------- |
| `--config` | Path to a JSON config file (optional) |
| `--image_dir` | Directory containing image files |
| `--label_dir` | Directory containing YOLO-format label files |
| `--output_dir` | Output directory for visualization results |

`--config` is optional; the other three can be provided via command line or JSON config. Command-line arguments take priority over config file values.

---

## 2. Overview

The script will:

* Iterate through all image files in `--image_dir`
* Look for a `.txt` label file with the same stem in `--label_dir`
* Parse YOLO-format annotation data if the label file exists
* Draw green rectangular bounding boxes with class IDs on the image
* Save visualization results to `--output_dir`, preserving the original filename

If an image has no corresponding label file, the image will be saved as-is to the output directory without any annotations.

---

## 3. Annotation Format

The script supports the YOLO annotation format with one object per line:

```
<class_id> <x_center> <y_center> <width> <height>
```

All coordinate values are **normalized** (relative to image width and height, ranging from `0.0` to `1.0`).

Example label file content:

```
0 0.523 0.456 0.234 0.345
1 0.300 0.600 0.150 0.200
```

---

## 4. Directory Structure Example

A typical directory structure for usage:

```
dataset/
├── images/
│   ├── 12835.jpg
│   └── ...
├── labels/
│   ├── 12835.txt
│   └── ...
└── visualization/
```

After running, the `visualization/` directory will contain visualizations with the same filenames as the images in `images/`.

---

## 5. Processing Logic

### 5.1 File matching rule

The script matches images and labels by **stem name**:

* `12835.jpg` ↔ `12835.txt`
* `abc.png` ↔ `abc.txt`

### 5.2 Coordinate conversion

Annotation data is converted from normalized coordinates to pixel coordinates:

```python
x_center_px = x_center * img_width
y_center_px = y_center * img_height
width_px = width * img_width
height_px = height * img_height
x1 = int(x_center_px - width_px / 2)
y1 = int(y_center_px - height_px / 2)
x2 = int(x_center_px + width_px / 2)
y2 = int(y_center_px + height_px / 2)
```

### 5.3 Drawing style

* Bounding box color: green `(0, 255, 0)`
* Line width: 2 px
* Text label: `class:<class_id>`, placed above the top-left corner of the bounding box
* Font: HERSHEY_SIMPLEX, size 0.6

---

## 6. Dependencies

* `opencv-python` — image I/O and drawing
* `argparse` — command-line argument parsing (Python standard library)
* `pathlib` — path manipulation (Python standard library)

Install dependencies:

```
pip install opencv-python