# yolo_visualizer.py

Used to draw YOLO-format bounding boxes onto images, generating visualization results with annotated bounding boxes and class names.

This script matches image files with their corresponding `.txt` label files by **filename**, automatically reads the annotation data, draws bounding boxes with class names on the images, saves the results to the specified output directory, and prints a processing summary.

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

`json/yolo_visualizer.example.json`

```json
{
  "image_dir": "dataset/images",
  "label_dir": "dataset/labels",
  "output_dir": "dataset/visualization",
  "data_yaml": "dataset/data.yaml",
  "classes": ["person", "car", "dog"],
  "colors": [
    [0, 255, 0],
    [0, 0, 255],
    [255, 0, 0]
  ]
}
```

Run it with:

```
python tools/yolo_visualizer.py --config json/yolo_visualizer.example.json
```

### 1.4 Argument description

| Argument | Description |
| -------- | ----------- |
| `--config` | Path to a JSON config file (optional) |
| `--image_dir` | Directory containing image files |
| `--label_dir` | Directory containing YOLO-format label files |
| `--output_dir` | Output directory for visualization results |

`--config` is optional; the other three can be provided via command line or JSON config. Command-line arguments take priority over config file values.

---

## 2. Config File Fields

| Field | Type | Required | Description |
| ------ | ------ | ------ | ------ |
| `image_dir` | str | ✅ | Image directory |
| `label_dir` | str | ✅ | YOLO-format label directory |
| `output_dir` | str | ✅ | Output directory for visualizations |
| `data_yaml` | str | ❌ | Path to standard YOLO data.yaml; class names are read from here first |
| `classes` | list or str | ❌ | Class name list or path to classes.txt (used when no data_yaml) |
| `colors` | list | ❌ | BGR color list by class index `[[B,G,R], ...]`; defaults to green |

### Class name resolution priority

1. `names` field in `data_yaml` (highest priority)
2. `classes` as an inline list in JSON
3. `classes` as a file path in JSON
4. Falls back to `class:0` format if none provided

### Two `classes` formats

* **Inline list**: `["person", "car", "dog"]` — write class names directly in JSON
* **File path**: `"dataset/classes.txt"` — points to a classes.txt file, one class name per line

---

## 3. Overview

The script will:

* Verify that `--image_dir` and `--label_dir` exist (raises an error if not)
* Iterate through all image files in `--image_dir`
* Look for a `.txt` label file with the same stem in `--label_dir`
* Parse YOLO-format annotation data and draw bounding boxes if the label exists
* Display class names (preferred) and BGR colors configured per class
* Save visualization results to `--output_dir`
* Print a processing summary (processed count, missing labels, invalid lines, etc.)

---

## 4. Annotation Format

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

### Data validation

The script validates each label line and outputs `[WARN]` for invalid data, **without stopping the entire batch**, when:

- The line does not have exactly 5 columns
- Non-numeric characters are present (e.g., `abc`)
- Class ID is not a non-negative integer
- Width or height ≤ 0
- Coordinates are outside the 0~1 range

---

## 5. Drawing Style

* Line width: 2 px
* Text label: class name from classes/data.yaml if available; otherwise `class:<class_id>`
* Font: HERSHEY_SIMPLEX, size 0.6
* Color: BGR value from `colors` list by class index

> ⚠️ **Important**: OpenCV uses **BGR** color order, not RGB.
>
> * `[0, 0, 255]` = **Red**
> * `[255, 0, 0]` = **Blue**
> * `[0, 255, 0]` = **Green**
>
> If you use the wrong color order, the bounding box color will differ from what you expect.

---

## 6. Directory Structure Example

A typical directory structure for usage:

```
dataset/
├── images/
│   ├── 12835.jpg
│   └── ...
├── labels/
│   ├── 12835.txt
│   └── ...
├── data.yaml
└── visualization/
```

After running, the `visualization/` directory will contain visualizations with the same filenames as the images in `images/`.

---

## 7. Processing Summary Example

After processing, a summary like this is printed:

```
=============================================
          Processing Summary
=============================================
  Processed      : 120
  Missing labels : 3
  Invalid lines  : 2
  Failed images  : 1
  Output dir     : dataset/visualization
=============================================
```

---

## 8. Processing Logic

### 8.1 File matching rule

The script matches images and labels by **stem name**:

* `12835.jpg` ↔ `12835.txt`
* `abc.png` ↔ `abc.txt`

### 8.2 Coordinate conversion

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

### 8.3 data.yaml format

Standard YOLO data.yaml format:

```yaml
names:
  0: person
  1: car
  2: dog
```

Or list format:

```yaml
names:
  - person
  - car
  - dog
```

The tool reads class names from `data.yaml` first.

---

## 9. Dependencies

* `opencv-python` — image I/O and drawing
* `PyYAML` — parsing data.yaml (optional, only needed when using `data_yaml`)
* `argparse` — command-line argument parsing (Python standard library)
* `pathlib` — path manipulation (Python standard library)

Install dependencies:

```
pip install opencv-python
pip install pyyaml