# yolo_visualizer.py

用于将 YOLO 格式的标注框绘制到图片上，生成带标注框的可视化结果图。

该脚本按**图片文件名匹配同名 `.txt` 标签文件**，自动读取标注数据并在图片上绘制边界框和类别名称，最终保存到指定输出目录并打印处理统计。

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

运行方式：

```
python tools/yolo_visualizer.py --config json/yolo_visualizer.example.json
```

### 1.4 参数说明

| 参数 | 含义 |
| ------ | ------ |
| `--config` | JSON 配置文件路径（可选） |
| `--image_dir` | 图片所在目录 |
| `--label_dir` | YOLO 格式标注文件所在目录 |
| `--output_dir` | 可视化结果输出目录 |

`--config` 为可选，其余三个参数可通过命令行或 JSON 配置提供。命令行参数优先级高于配置文件。

---

## 2. 配置文件字段说明

| 字段 | 类型 | 必填 | 说明 |
| ------ | ------ | ------ | ------ |
| `image_dir` | str | ✅ | 图片目录 |
| `label_dir` | str | ✅ | YOLO 格式标注目录 |
| `output_dir` | str | ✅ | 可视化结果输出目录 |
| `data_yaml` | str | ❌ | 标准 YOLO data.yaml 路径，优先从中读取类别名称 |
| `classes` | list 或 str | ❌ | 类别名称列表或 classes.txt 路径（没有 data_yaml 时生效） |
| `colors` | list | ❌ | 按类别索引的 BGR 颜色列表 `[[B,G,R], ...]`，不配置则默认绿色 |

### 类别名称加载优先级

1. `data_yaml` 中的 `names` 字段（最高优先级）
2. JSON 中 `classes` 的直接列表写法
3. JSON 中 `classes` 的文件路径写法
4. 都不提供时回退显示 `class:0` 格式

### classes 字段的两种写法

* **直接列表**：`["person", "car", "dog"]` — 直接在 JSON 中写明类别名
* **文件路径**：`"dataset/classes.txt"` — 指向 classes.txt 文件，每行一个类别名

---

## 3. 功能简介

脚本会：

* 检查 `--image_dir` 和 `--label_dir` 是否存在（不存在则报错退出）
* 遍历 `--image_dir` 目录下的所有图片文件
* 在 `--label_dir` 中查找同名 `.txt` 标签文件
* 如果标签文件存在，解析 YOLO 格式标注数据并绘制边界框
* 标注文字优先显示类别名称，颜色按配置中的 BGR 顺序取色
* 将可视化结果保存到 `--output_dir`
* 处理完成后打印统计摘要（处理数、缺失标签数、异常标签行数等）

---

## 4. 标注格式说明

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

### 数据合法性检查

脚本会对每行标注进行验证，遇到以下情况会输出 `[WARN]` 并跳过该行，**不会中断整个批量处理**：

- 数值不是 5 列
- 存在非数字字符（如 `abc`）
- 类别 ID 不是非负整数
- 宽高 ≤ 0
- 坐标超出 0~1 范围

---

## 5. 绘制样式

* 边界框线条宽度：2 px
* 文字标签：优先显示 classes/data.yaml 中对应的类别名；未配置时显示 `class:<class_id>`
* 字体：HERSHEY_SIMPLEX，大小 0.6
* 颜色：按 `colors` 列表取对应索引的 BGR 值

> ⚠️ **注意**：OpenCV 使用 **BGR** 颜色顺序，而非 RGB。
>
> * `[0, 0, 255]` = **红色**
> * `[255, 0, 0]` = **蓝色**
> * `[0, 255, 0]` = **绿色**
>
> 如果配置了错误的颜色顺序，框的颜色会与预期不同。

---

## 6. 目录结构示例

典型用法对应的目录结构：

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

运行后，`visualization/` 目录将包含与 `images/` 同名的可视化图片。

---

## 7. 处理统计示例

处理完成后会输出类似以下摘要：

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

## 8. 处理逻辑说明

### 8.1 文件匹配规则

脚本按**同名 stem** 匹配图片和标签：

* `12835.jpg` ↔ `12835.txt`
* `abc.png` ↔ `abc.txt`

### 8.2 坐标转换

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

### 8.3 data.yaml 格式

标准的 YOLO data.yaml 文件结构：

```yaml
names:
  0: person
  1: car
  2: dog
```

或列表格式：

```yaml
names:
  - person
  - car
  - dog
```

工具优先从 `data.yaml` 读取类别名称。

---

## 9. 依赖

* `opencv-python` — 图像读写与绘制
* `PyYAML` — 解析 data.yaml（可选，仅在使用 `data_yaml` 时需要）
* `argparse` — 命令行参数解析（Python 标准库）
* `pathlib` — 路径操作（Python 标准库）

安装依赖：

```
pip install opencv-python
pip install pyyaml