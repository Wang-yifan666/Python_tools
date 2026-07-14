# yolo_visualizer.py

用于将 YOLO 格式的标注框绘制到图片上，生成带标注框的可视化结果图。

该脚本按**图片文件名匹配同名 `.txt` 标签文件**，自动读取标注数据并在图片上绘制边界框和类别编号，最终保存到指定输出目录。

---

## 1. 快速使用

### 1.1 查看帮助

```
python tools/yolo_visualizer.py --help
```

### 1.2 基本用法

```
python tools/yolo_visualizer.py \
    --image_dir dataset/images \
    --label_dir dataset/labels \
    --output_dir dataset/visualization
```

### 1.3 使用 JSON 配置文件

先准备配置文件，例如：

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

运行方式：

```
python tools/yolo_visualizer.py --config json/yolo_visualizer.json
```

配置文件中的 `classes` 支持两种写法：

* **直接列表**：`["person", "car", "dog"]` — 直接在 JSON 中写明类别名
* **文件路径**：`"dataset/classes.txt"` — 指向 classes.txt 文件，每行一个类别名

如果 `classes` 留空或不配置，标注文字回退显示 `class:0` 格式。

### 1.4 参数说明

| 参数 | 含义 |
| ------ | ------ |
| `--config` | JSON 配置文件路径（可选） |
| `--image_dir` | 图片所在目录 |
| `--label_dir` | YOLO 格式标注文件所在目录 |
| `--output_dir` | 可视化结果输出目录 |

`--config` 为可选，其余三个参数可通过命令行或 JSON 配置提供。命令行参数优先级高于配置文件。

---

## 2. 功能简介

脚本会：

* 遍历 `--image_dir` 目录下的所有图片文件
* 在 `--label_dir` 中查找同名 `.txt` 标签文件
* 如果标签文件存在，解析 YOLO 格式标注数据
* 在图片上绘制绿色矩形边界框，并标注类别编号
* 将可视化结果保存到 `--output_dir`，保持原文件名

如果某张图片缺少对应的标签文件，该图片将原样保存到输出目录（不绘制任何标注）。

---

## 3. 标注格式说明

脚本支持的 YOLO 标注格式为每行一个目标：

```
<class_id> <x_center> <y_center> <width> <height>
```

所有坐标值均为**归一化值**（相对于图片宽高的比例，范围 `0.0 ~ 1.0`）。

示例标签文件内容：

```
0 0.523 0.456 0.234 0.345
1 0.300 0.600 0.150 0.200
```

---

## 4. 目录结构示例

典型用法对应的目录结构：

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

运行后，`visualization/` 目录将包含与 `images/` 同名的可视化图片。

---

## 5. 处理逻辑说明

### 5.1 文件匹配规则

脚本按**同名 stem** 匹配图片和标签：

* `12835.jpg` ↔ `12835.txt`
* `abc.png` ↔ `abc.txt`

### 5.2 坐标转换

标注数据从归一化坐标转换到像素坐标：

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

### 5.3 绘制样式

* 边界框颜色：绿色 `(0, 255, 0)`
* 线条宽度：2 px
* 文字标签：`class:<类别编号>`，位于边界框左上角上方
* 字体：HERSHEY_SIMPLEX，大小 0.6

---

## 6. 依赖

* `opencv-python` — 图像读写与绘制
* `argparse` — 命令行参数解析（Python 标准库）
* `pathlib` — 路径操作（Python 标准库）

安装依赖：

```
pip install opencv-python