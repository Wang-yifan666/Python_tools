# rename_yolov5_pairs.py

Used to batch rename **image files** and their **corresponding label files** in a YOLOv5 dataset.

This script only processes samples where **the image exists and the label file with the same name and a `.txt` extension also exists**, while preserving the one-to-one correspondence between images and labels.

---

## 1. Quick Start

### 1.1 Show help

```
python tools/rename_yolov5_pairs.py --help
```

### 1.2 Preview first without modifying files

The following command processes `train` and `val`, but does not actually rename any files:

```
python tools/rename_yolov5_pairs.py \
    --root /path/to/dataset \
    --splits train,val \
    --mode continuous \
    --start 1 \
    --digits 6 \
    --dry-run
```

### 1.3 Apply the changes after confirmation

```
python tools/rename_yolov5_pairs.py \
    --root /path/to/dataset \
    --splits train,val \
    --mode continuous \
    --start 1 \
    --digits 6 \
    --apply
```

### Or use a JSON config file

First prepare a config file, for example:

`json/rename_yolov5_pairs.json`

```
{
  "root": "D:/datasets/my_yolo_dataset",
  "splits": ["train", "val"],
  "mode": "continuous",
  "start": 1,
  "digits": 6,
  "dry_run": true,
  "img_exts": [".jpg", ".jpeg", ".png"]
}
```

Run it with:

```
python tools/rename_yolov5_pairs.py --config json/rename_yolov5_pairs.json
```

To perform the actual renaming directly:

```
python tools/rename_yolov5_pairs.py --config json/rename_yolov5_pairs.json --apply
```

---

## 2. Overview

In a YOLO dataset, the typical directory structure looks like this:

```
root/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

The script iterates through the specified splits (such as `train` and `val`), and for each split it will:

* Scan image files under `images/<split>/`
* Check whether a label file with the same name and a `.txt` extension exists under `labels/<split>/`
* Rename only samples where both the image and label exist as a pair
* Generate new filenames according to the specified numbering rule
* Preserve the original image extension, while converting it to lowercase
* Rename label files to the same stem with a `.txt` extension

---

## 3. Supported Features

* Supports batch processing of multiple splits, such as `train,val,test`
* Supports two numbering modes:

  * `independent`: each split restarts numbering from the same starting index
  * `continuous`: numbering continues across splits
* Supports customization of:

  * starting index
  * zero-padding width
  * allowed image extensions
* `dry-run` preview mode is enabled by default to help avoid accidental operations

---

## 4. Dataset Directory Requirements

By default, the script expects the dataset to follow a structure like this:

```text
dataset/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

### Matching rule

The script matches images and labels by the **same stem name**:

* `a.jpg` ↔ `a.txt`
* `b.png` ↔ `b.txt`

Only successfully matched pairs will be processed.

---

## 5. Default Configuration

The script includes the following default configuration:

```python
DEFAULT_CONFIG = {
    "root": "",
    "splits": ["train", "val"],
    "mode": "continuous",
    "start": 1,
    "digits": 6,
    "dry_run": True,
    "img_exts": [".jpg", ".jpeg", ".png"],
}
```

### Field descriptions

| Field      | Meaning                                                 |
| ---------- | ------------------------------------------------------- |
| `root`     | Dataset root directory                                  |
| `splits`   | List of dataset splits to process                       |
| `mode`     | Numbering mode: `independent` or `continuous`           |
| `start`    | Starting index                                          |
| `digits`   | Zero-padding width                                      |
| `dry_run`  | Whether to preview only without actually renaming files |
| `img_exts` | Allowed image file extensions                           |

---

## 6. Command-Line Arguments

You can run the script directly from the command line.

### Argument list

| Argument    | Description                                           |
| ----------- | ----------------------------------------------------- |
| `--config`  | Path to a JSON config file                            |
| `--root`    | Dataset root directory                                |
| `--splits`  | Comma-separated split list, such as `train,val,test`  |
| `--mode`    | Numbering mode: `independent` or `continuous`         |
| `--start`   | Starting index                                        |
| `--digits`  | Zero-padding width; `0` means no zero-padding         |
| `--exts`    | Comma-separated image extensions, such as `.jpg,.png` |
| `--dry-run` | Preview only, do not perform renaming                 |
| `--apply`   | Actually perform renaming                             |

---

## 7. Numbering Modes

The script supports two numbering modes.

### 7.1 `independent`

Each split starts numbering independently from `start`.

For example:

* `train` starts from `000001`
* `val` also starts from `000001`

Example:

```
python tools/rename_yolov5_pairs.py \
    --root /path/to/dataset \
    --splits train,val \
    --mode independent \
    --start 1 \
    --digits 6 \
    --apply
```

After processing, the result may look like:

```
images/train/000001.jpg
images/train/000002.jpg
...

images/val/000001.jpg
images/val/000002.jpg
...
```

### 7.2 `continuous`

Numbering continues across splits.

For example:

* `train` is numbered up to `000120`
* `val` continues from `000121`

Example:

```bash
python tools/rename_yolov5_pairs.py \
    --root /path/to/dataset \
    --splits train,val \
    --mode continuous \
    --start 1 \
    --digits 6 \
    --apply
```

---

## 8. Processing Logic

### 8.1 File collection order

The script reads all files in the image directory that match the allowed extensions and sorts them by filename:

```python
files.sort(key=lambda p: p.name.lower())
```

That means the final numbering order depends on the **lexicographical order of image filenames**, not on file creation time.

If you care about the numbering order, make sure the original filenames are already arranged as expected.

### 8.2 Only paired samples are processed

The script only processes samples where:

* the image exists
* and a `.txt` label file with the same stem also exists

If an image exists but the corresponding label does not, that image will be counted under `Skipped images`, but the script will not terminate with an error.

---
