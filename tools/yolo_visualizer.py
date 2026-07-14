# 建议先阅读 docs/cn(en)/yolo_visualizer.md
# python tools/yolo_visualizer.py --help
# python tools/yolo_visualizer.py --image_dir dataset/images --label_dir dataset/labels --output_dir dataset/visualization
# python tools/yolo_visualizer.py --config json/yolo_visualizer.json

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import cv2

# yaml 为可选依赖，仅在使用 data_yaml 时需要
try:
    import yaml as _yaml_lib
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

DEFAULT_CONFIG = {
    "image_dir": "",
    "label_dir": "",
    "output_dir": "",
    "data_yaml": "",
    "classes": [],
    "colors": [
        [0, 255, 0],
    ],
}


# 读取 JSON 配置文件并返回字典配置
def load_config(config_path: Optional[Path]) -> dict:
    if config_path is None:
        return {}

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Config file must be a JSON object.")
    return data


# 从 data.yaml 中读取类别名称（names 字段）
def load_classes_from_yaml(yaml_path: Path) -> list:
    if not _HAS_YAML:
        raise ImportError(
            "PyYAML is required to read data.yaml. "
            "Install it with: pip install pyyaml"
        )

    if not yaml_path.exists():
        raise FileNotFoundError(f"data.yaml not found: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = _yaml_lib.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("data.yaml must be a YAML mapping.")

    names = data.get("names")
    if names is None:
        raise ValueError("data.yaml does not contain 'names' field.")

    if isinstance(names, dict):
        # names: {0: "person", 1: "car"} 格式
        max_idx = max(names.keys())
        result = [""] * (max_idx + 1)
        for idx, name in names.items():
            result[int(idx)] = str(name).strip()
        return result

    if isinstance(names, list):
        return [str(n).strip() for n in names]

    raise ValueError("data.yaml 'names' field must be a list or dict.")


# 解析 classes 配置
# 优先级: data_yaml > JSON classes 列表 > JSON classes 文件路径
def load_classes(classes, data_yaml: Optional[str] = None) -> list:
    # 优先从 data.yaml 读取
    if data_yaml:
        return load_classes_from_yaml(Path(data_yaml))

    if classes is None or classes == []:
        return []

    if isinstance(classes, str):
        cls_file = Path(classes)
        if not cls_file.exists():
            raise FileNotFoundError(f"Classes file not found: {cls_file}")
        with open(cls_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    if isinstance(classes, list):
        return [str(c).strip() for c in classes if str(c).strip()]

    return []


def yolo_to_xyxy(
        label,
        img_width,
        img_height):
    """将单行 YOLO 标注转换为像素坐标。
    返回 (class_id, x1, y1, x2, y2)；若数据不合法返回 None。
    """

    line = label.strip()
    if not line:
        return None

    values = line.split()
    if len(values) != 5:
        return None

    # 先尝试解析浮点数
    try:
        cls_val, xc, yc, w, h = map(float, values)
    except ValueError:
        print(f"[WARN] Skipping invalid label line: {line}", file=sys.stderr)
        return None

    # 类别 ID 必须为非负整数
    if not cls_val.is_integer():
        print(f"[WARN] Skipping non-integer class ID: {cls_val}", file=sys.stderr)
        return None

    cls_id = int(cls_val)

    if cls_id < 0:
        print(f"[WARN] Skipping negative class ID: {cls_id}", file=sys.stderr)
        return None

    # 宽高必须大于 0
    if w <= 0 or h <= 0:
        print(f"[WARN] Skipping non-positive width/height: w={w}, h={h}", file=sys.stderr)
        return None

    # 坐标必须在 0~1 范围内
    if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0
            and 0.0 <= w <= 1.0 and 0.0 <= h <= 1.0):
        print(
            f"[WARN] Skipping out-of-range coordinates: "
            f"xc={xc}, yc={yc}, w={w}, h={h}",
            file=sys.stderr,
        )
        return None

    xc *= img_width
    yc *= img_height
    w *= img_width
    h *= img_height

    x1 = int(xc - w / 2)
    y1 = int(yc - h / 2)
    x2 = int(xc + w / 2)
    y2 = int(yc + h / 2)

    return cls_id, x1, y1, x2, y2


def get_color(cls_id: int, colors: list) -> Tuple[int, int, int]:
    """根据类别 ID 获取对应颜色。
    cls_id 超出范围时使用最后一个颜色；列表为空时返回默认绿色。
    """
    if not colors:
        return (0, 255, 0)
    # cls_id 已经由 yolo_to_xyxy 保证 >= 0
    idx = cls_id if cls_id < len(colors) else len(colors) - 1
    c = colors[idx]
    return (int(c[0]), int(c[1]), int(c[2]))


def get_class_name(cls_id: int, classes: list) -> str:
    """根据类别 ID 获取类别名，没有则返回 class:ID。"""
    if classes and 0 <= cls_id < len(classes):
        return classes[cls_id]
    return f"class:{cls_id}"


def draw_labels(
        img,
        label_file,
        classes: Optional[List] = None,
        colors: Optional[List] = None):
    """在图片上绘制标注框，返回 (img, invalid_count)。"""

    if classes is None:
        classes = []
    if colors is None:
        colors = []

    height, width = img.shape[:2]
    invalid_count = 0

    if not label_file.exists():
        return img, invalid_count

    with open(label_file, "r") as f:
        lines = f.readlines()

    for line in lines:
        result = yolo_to_xyxy(
            line,
            width,
            height
        )

        if result is None:
            invalid_count += 1
            continue

        cls_id, x1, y1, x2, y2 = result

        color = get_color(cls_id, colors)
        name = get_class_name(cls_id, classes)

        cv2.rectangle(
            img,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        cv2.putText(
            img,
            name,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

    return img, invalid_count


def process_dataset(
        image_dir,
        label_dir,
        output_dir,
        classes: Optional[List] = None,
        colors: Optional[List] = None):
    """批量处理数据集，完成后打印统计信息。"""

    if classes is None:
        classes = []
    if colors is None:
        colors = []

    # 检查输入目录是否存在
    if not image_dir.is_dir():
        raise NotADirectoryError(f"Image directory not found: {image_dir}")
    if not label_dir.is_dir():
        raise NotADirectoryError(f"Label directory not found: {label_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    image_files = list(image_dir.glob("*"))

    processed = 0
    missing_labels = 0
    total_invalid = 0
    failed_images = 0

    for img_path in image_files:
        img = cv2.imread(str(img_path))

        if img is None:
            failed_images += 1
            print(f"[SKIP] Cannot read image: {img_path.name}")
            continue

        label_path = label_dir / (img_path.stem + ".txt")

        if not label_path.exists():
            missing_labels += 1

        img, invalid_count = draw_labels(
            img,
            label_path,
            classes,
            colors
        )

        total_invalid += invalid_count

        save_path = output_dir / img_path.name
        cv2.imwrite(str(save_path), img)

        processed += 1
        print(f"[OK] {img_path.name}")

    # 输出统计信息
    print("\n" + "=" * 45)
    print("          Processing Summary")
    print("=" * 45)
    print(f"  Processed      : {processed}")
    print(f"  Missing labels : {missing_labels}")
    print(f"  Invalid lines  : {total_invalid}")
    print(f"  Failed images  : {failed_images}")
    print(f"  Output dir     : {output_dir}")
    print("=" * 45)


def main():
    parser = argparse.ArgumentParser(
        description="YOLO label visualization tool"
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Optional JSON config file path."
    )

    parser.add_argument(
        "--image_dir",
        type=str,
        help="Directory containing image files."
    )

    parser.add_argument(
        "--label_dir",
        type=str,
        help="Directory containing YOLO-format label files."
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        help="Output directory for visualization results."
    )

    args = parser.parse_args()

    # 合并配置：默认 < JSON 文件 < 命令行
    cfg = DEFAULT_CONFIG.copy()

    file_cfg = load_config(args.config)
    cfg.update(file_cfg)

    if args.image_dir is not None:
        cfg["image_dir"] = args.image_dir
    if args.label_dir is not None:
        cfg["label_dir"] = args.label_dir
    if args.output_dir is not None:
        cfg["output_dir"] = args.output_dir

    # 校验必填项
    if not cfg.get("image_dir"):
        raise ValueError("image_dir is required. Use --image_dir or provide it in config file.")
    if not cfg.get("label_dir"):
        raise ValueError("label_dir is required. Use --label_dir or provide it in config file.")
    if not cfg.get("output_dir"):
        raise ValueError("output_dir is required. Use --output_dir or provide it in config file.")

    data_yaml = cfg.get("data_yaml", "") or None
    classes = load_classes(cfg.get("classes", []), data_yaml)
    colors = cfg.get("colors", [])

    if not colors:
        colors = DEFAULT_CONFIG["colors"]

    process_dataset(
        Path(cfg["image_dir"]),
        Path(cfg["label_dir"]),
        Path(cfg["output_dir"]),
        classes,
        colors
    )


if __name__ == "__main__":
    main()