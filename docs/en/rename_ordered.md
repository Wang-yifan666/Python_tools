# rename_files_in_order.py

Batch rename files in a specified folder in filename order.

## Description

This script is used to rename files in a folder sequentially.

## Usage

Show help first:

```
python tools/rename_files_in_order.py --help
```

Preview only without modifying files:

```
python tools/rename_files_in_order.py --folder D:/data/files --dry-run
```

Run the renaming operation:

```
python tools/rename_files_in_order.py --folder D:/data/files --prefix img_ --start 1 --digits 4 --apply
```

Process only specific file extensions:

```
python tools/rename_files_in_order.py --folder D:/data/files --exts .jpg,.png --prefix file_ --apply
```

Use a JSON config file:

```
python tools/rename_files_in_order.py --config json/rename_files_in_order.json
```

---

## Arguments

### `--config`

Optional. Path to the JSON config file.

### `--folder`

Path to the target folder.

For example:

```bash
--folder D:/data/files
```

### `--prefix`

Prefix for renamed filenames.

For example:

```bash
--prefix img_
```

### `--start`

Starting index.

For example:

```bash
--start 1
```

### `--digits`

Number of zero-padding digits.

For example:

* `4` -> `0001`
* `3` -> `001`
* `0` -> no zero-padding

```bash
--digits 4
```

### `--exts`

Only process specified file extensions. Multiple extensions should be separated by commas.

For example:

```bash
--exts .jpg,.png,.txt
```

### `--dry-run`

Preview only, without modifying files.

### `--apply`

Actually perform the renaming.

---

## Example Config File

```json
{
  "folder": "D:/data/files",
  "prefix": "img_",
  "start": 1,
  "digits": 4,
  "dry_run": true,
  "exts": [".jpg", ".png"]
}
```
---
