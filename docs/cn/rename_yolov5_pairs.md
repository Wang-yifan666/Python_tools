# rename_yolov5_pairs.py

用于批量重命名 YOLOv5 数据集中的 **图片文件** 与 **对应标签文件**。

该脚本只处理“**图片存在，且同名 `.txt` 标签也存在**”的样本对，并保持图片与标签的一一对应关系。

---

## 1. 快速使用

### 1.1 查看帮助

```
python tools/rename_yolov5_pairs.py --help
```

### 1.2 先预览，不直接改文件

下面命令会处理 `train` 和 `val`，但不会真正修改文件：

```
python tools/rename_yolov5_pairs.py \
    --root /path/to/dataset \
    --splits train,val \
    --mode continuous \
    --start 1 \
    --digits 6 \
    --dry-run
```

### 1.3 确认无误后正式执行

```
python tools/rename_yolov5_pairs.py \
    --root /path/to/dataset \
    --splits train,val \
    --mode continuous \
    --start 1 \
    --digits 6 \
    --apply
```

### 或者使用 JSON 配置文件

先准备配置文件，例如：

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

运行方式：

```bash
python tools/rename_yolov5_pairs.py --config json/rename_yolov5_pairs.json
```

如果要直接执行实际重命名：

```bash
python tools/rename_yolov5_pairs.py --config json/rename_yolov5_pairs.json --apply
```

---

## 2. 功能简介

在 YOLO 数据集中，常见的目录结构如下：

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

脚本会遍历指定的 `split`（如 `train`、`val`），在每个 split 中：

* 扫描 `images/<split>/` 下的图片文件
* 查找 `labels/<split>/` 下是否存在同名 `.txt` 标签
* 仅对“图片 + 标签”成对存在的样本进行重命名
* 按设定规则生成新的文件名
* 保留图片原始扩展名（统一转为小写）
* 标签文件统一改为同名 `.txt`

---

## 3. 支持功能

* 支持多个 split 批量处理，如 `train,val,test`
* 支持两种编号模式：
  * `independent`：每个 split 从同一个起始编号重新开始
  * `continuous`：跨 split 连续编号
* 支持设置：
  * 起始编号
  * 补零位数
  * 可处理的图片扩展名
* 默认启用 `dry-run` 预览模式，避免误操作

---

## 4. 数据集目录要求

脚本默认要求数据集结构满足下面这种形式：

```
dataset/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

### 匹配规则

脚本按“**同名 stem**”匹配图片和标签：

* `a.jpg` ↔ `a.txt`
* `b.png` ↔ `b.txt`

只有配对成功的样本才会被处理。

---

## 5. 默认配置

脚本内置默认配置如下：

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

### 字段说明

| 字段         | 含义                                |
| ---------- | --------------------------------- |
| `root`     | 数据集根目录                            |
| `splits`   | 需要处理的数据划分列表                       |
| `mode`     | 编号模式：`independent` 或 `continuous` |
| `start`    | 起始编号                              |
| `digits`   | 编号补零位数                            |
| `dry_run`  | 是否仅预览，不实际修改文件                     |
| `img_exts` | 允许处理的图片扩展名                        |

---

## 6. 命令行参数

你可以直接通过命令行传参运行。

### 参数列表

| 参数          | 说明                                |
| ----------- | --------------------------------- |
| `--config`  | JSON 配置文件路径                       |
| `--root`    | 数据集根目录                            |
| `--splits`  | 逗号分隔的 split 列表，如 `train,val,test` |
| `--mode`    | 编号模式：`independent` 或 `continuous` |
| `--start`   | 起始编号                              |
| `--digits`  | 补零位数，`0` 表示不补零                    |
| `--exts`    | 逗号分隔的图片扩展名，如 `.jpg,.png`          |
| `--dry-run` | 仅预览，不执行重命名                        |
| `--apply`   | 实际执行重命名                           |

---

## 7. 编号模式说明

脚本支持两种编号模式。

### 7.1 `independent`

每个 split 独立从 `start` 开始编号。

例如：

* `train` 从 `000001` 开始
* `val` 也从 `000001` 开始

示例：

```bash
python tools/rename_yolov5_pairs.py \
    --root /path/to/dataset \
    --splits train,val \
    --mode independent \
    --start 1 \
    --digits 6 \
    --apply
```

处理后可能得到：

```text
images/train/000001.jpg
images/train/000002.jpg
...

images/val/000001.jpg
images/val/000002.jpg
...
```

### 7.2 `continuous`

跨 split 连续编号。

例如：

* `train` 编号到 `000120`
* `val` 会从 `000121` 继续

示例：

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


## 8. 处理逻辑说明

### 8.1 文件收集顺序

脚本会读取图片目录下所有符合扩展名条件的文件，并按文件名排序：

```python
files.sort(key=lambda p: p.name.lower())
```

也就是说，最终编号顺序取决于 **图片文件名的字典序**，而不是文件创建时间。

如果你对编号顺序有要求，最好先确保原始文件名排序符合你的预期。

### 8.2 只处理成对样本

脚本只处理：

* 图片存在
* 同名 `.txt` 标签也存在

的样本。

如果图片存在但标签不存在，该图片会被统计到 `Skipped images` 中，但不会报错终止。

---
