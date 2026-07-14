# 建议先阅读 docs/cn(en)/yolo_visualizer.md
# python tools/yolo_visualizer.py --help
# python tools/yolo_visualizer.py --image_dir dataset/images --label_dir dataset/labels --output_dir dataset/visualization
# python tools/yolo_visualizer.py --config json/yolo_visualizer.json

import argparse
import json
from pathlib import Path
from typing import List, Optional, Tuple

import cv2


DEFAULT_CONFIG = {
    "image_dir": "",
    "label_dir": "",
    "output_dir": "",
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


# 解析 classes 配置，支持直接列表或文件路径两种写法
def load_classes(classes) -> list:
    if classes is None or classes == []:
        return []

    if isinstance(classes, str):
        # 字符串 → 当作文件路径读取，每行一个类名
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

    values = label.strip().split()

    if len(values) != 5:
        return None

    cls, xc, yc, w, h = map(float, values)

    xc *= img_width
    yc *= img_height
    w *= img_width
    h *= img_height

    x1 = int(xc - w / 2)
    y1 = int(yc - h / 2)

    x2 = int(xc + w / 2)
    y2 = int(yc + h / 2)

    return int(cls), x1, y1, x2, y2


def get_color(cls_id: int, colors: list) -> Tuple[int, int, int]:
    """根据类别 ID 获取对应颜色，超出范围则使用最后一个颜色。"""
    if not colors:
        return (0, 255, 0)
    idx = min(cls_id, len(colors) - 1)
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

    if classes is None:
        classes = []
    if colors is None:
        colors = []

    height, width = img.shape[:2]

    if not label_file.exists():
        return img

    with open(label_file, "r") as f:
        lines = f.readlines()

    for line in lines:
        result = yolo_to_xyxy(
            line,
            width,
            height
        )

        if result is None:
            continue

        cls, x1, y1, x2, y2 = result

        color = get_color(cls, colors)
        name = get_class_name(cls, classes)

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

    return img


def process_dataset(
        image_dir,
        label_dir,
        output_dir,
        classes: Optional[List] = None,
        colors: Optional[List] = None):

    if classes is None:
        classes = []
    if colors is None:
        colors = []

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    image_files = list(
        image_dir.glob("*")
    )

    for img_path in image_files:
        img = cv2.imread(
            str(img_path)
        )

        if img is None:
            continue

        label_path = (
            label_dir /
            (img_path.stem + ".txt")
        )

        img = draw_labels(
            img,
            label_path,
            classes,
            colors
        )

        save_path = (
            output_dir /
            img_path.name
        )

        cv2.imwrite(
            str(save_path),
            img
        )

        print(
            f"[OK] {img_path.name}"
        )


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

    classes = load_classes(cfg.get("classes", []))
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