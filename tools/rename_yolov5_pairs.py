# 建议先阅读 docs/cn(en)/rename_yolov5_pairs.md
# python tools/rename_yolov5_pairs.py --help
# python tools/rename_yolov5_pairs.py --root /path/to/dataset --splits train,val --dry-run
# python tools/rename_yolov5_pairs.py --root /path/to/dataset --splits train,val --apply
import argparse
import json
import os
from pathlib import Path
from uuid import uuid4

DEFAULT_CONFIG = {
    "root": "",
    "splits": ["train", "val"],
    "mode": "continuous",   # independent | continuous
    "start": 1,
    "digits": 6,
    "dry_run": True,
    "img_exts": [".jpg", ".jpeg", ".png"],
}


# 读取 JSON 配置文件并返回字典配置。
def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return {}

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Config file must be a JSON object.")
    return data


# 将扩展名列表标准化为小写且带点号的元组。
def normalize_exts(exts) -> tuple[str, ...]:
    if not exts:
        return tuple(DEFAULT_CONFIG["img_exts"])

    normalized = []
    for ext in exts:
        ext = str(ext).strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = "." + ext
        normalized.append(ext)

    if not normalized:
        raise ValueError("img_exts is empty after normalization.")
    return tuple(normalized)


# 将 split 输入解析为非空字符串列表。
def parse_splits(value) -> list[str]:
    if isinstance(value, list):
        splits = [str(x).strip() for x in value if str(x).strip()]
    else:
        splits = [x.strip() for x in str(value).split(",") if x.strip()]

    if not splits:
        raise ValueError("splits cannot be empty.")
    return splits


# 收集目录下所有匹配扩展名的图片文件并按名称排序。
def collect_images(images_dir: Path, img_exts: tuple[str, ...]) -> list[Path]:
    files = []
    for p in images_dir.iterdir():
        if p.is_file() and p.suffix.lower() in img_exts:
            files.append(p)
    files.sort(key=lambda p: p.name.lower())
    return files


# 为旧文件路径生成一个唯一、未占用的临时路径。
def build_tmp_path(old: Path, used_tmp_paths: set[Path]) -> Path:
    while True:
        candidate = old.with_name(f"{old.stem}.__tmp__.{uuid4().hex}{old.suffix}")
        if candidate not in used_tmp_paths and not candidate.exists():
            used_tmp_paths.add(candidate)
            return candidate


# 使用两段式重命名执行批量改名，避免覆盖冲突。
def two_phase_rename(pairs: list[tuple[Path, Path]], dry_run: bool = False):
    # 去掉 old == new 的无效操作
    pairs = [(old, new) for old, new in pairs if old != new]

    if not pairs:
        print("No files need renaming in this phase.")
        return

    old_paths = [old for old, _ in pairs]
    new_paths = [new for _, new in pairs]

    # 检查源文件存在
    for old in old_paths:
        if not old.exists():
            raise FileNotFoundError(f"Source file not found: {old}")

    # 检查目标名重复
    new_path_strs = [str(p) for p in new_paths]
    if len(set(new_path_strs)) != len(new_path_strs):
        raise RuntimeError("Target name collision detected (duplicate target filenames).")

    # 检查目标名是否已被外部文件占用
    old_set = set(old_paths)
    for new in new_paths:
        if new.exists() and new not in old_set:
            raise RuntimeError(f"Target already exists and is not part of current rename set: {new}")

    used_tmp_paths = set()
    tmp_map = []
    for old, new in pairs:
        tmp = build_tmp_path(old, used_tmp_paths)
        tmp_map.append((old, tmp, new))

    # old -> tmp
    for old, tmp, _ in tmp_map:
        print(f"[1] {old.name} -> {tmp.name}")
        if not dry_run:
            os.rename(old, tmp)

    # tmp -> new
    for _, tmp, new in tmp_map:
        print(f"[2] {tmp.name} -> {new.name}")
        if not dry_run:
            os.rename(tmp, new)


# 重命名单个 split 下的图片-标签配对样本，并返回下一起始编号。
def rename_split(
    images_dir: Path,
    labels_dir: Path,
    start_index: int = 1,
    digits: int = 0,
    dry_run: bool = True,
    img_exts: tuple[str, ...] = (".jpg", ".jpeg", ".png"),
) -> int:
    if not images_dir.exists():
        raise FileNotFoundError(f"Images dir not found: {images_dir}")
    if not labels_dir.exists():
        raise FileNotFoundError(f"Labels dir not found: {labels_dir}")

    # 收集当前 split 下所有符合扩展名的图片文件（按文件名排序）
    imgs = collect_images(images_dir, img_exts)

    pairs = []
    skipped_images = []

    # 仅保留“图片和同名 txt 标签同时存在”的样本
    for img in imgs:
        txt = labels_dir / f"{img.stem}.txt"
        if txt.exists() and txt.is_file():
            pairs.append((img, txt))
        else:
            skipped_images.append(img)

    if not pairs:
        print("\n=======================================")
        print(f"Images : {images_dir}")
        print(f"Labels : {labels_dir}")
        print("No matched image-label pairs found.")
        return start_index

    def fmt(i: int) -> str:
        return str(i).zfill(digits) if digits > 0 else str(i)

    img_renames = []
    txt_renames = []
    idx = start_index

    # 为每一对样本生成新文件名，图片保留原扩展名（统一为小写）
    for img, txt in pairs:
        new_stem = fmt(idx)
        new_img = img.with_name(new_stem + img.suffix.lower())
        new_txt = txt.with_name(new_stem + ".txt")
        img_renames.append((img, new_img))
        txt_renames.append((txt, new_txt))
        idx += 1

    print("\n=======================================")
    print(f"Images dir     : {images_dir}")
    print(f"Labels dir     : {labels_dir}")
    print(f"Matched pairs  : {len(pairs)}")
    print(f"Skipped images : {len(skipped_images)}")
    print(f"Start index    : {start_index}")
    print(f"Digits         : {digits}")
    print(f"Dry run        : {dry_run}")
    print(f"Extensions     : {', '.join(img_exts)}")
    print("Mode           : rename paired samples only\n")

    print("---- Renaming images ----")
    # 先重命名图片，再重命名标签
    two_phase_rename(img_renames, dry_run=dry_run)

    print("\n---- Renaming labels ----")
    two_phase_rename(txt_renames, dry_run=dry_run)

    # 返回下一个可用编号，供 continuous 模式衔接下一个 split
    return idx


# 构建命令行参数解析器并定义可用参数。
def build_parser():
    parser = argparse.ArgumentParser(
        description="Rename YOLO image-label pairs in dataset splits."
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Optional JSON config file path."
    )
    parser.add_argument(
        "--root",
        type=str,
        help="Dataset root path. Example: D:/data/dataset_1"
    )
    parser.add_argument(
        "--splits",
        type=str,
        help="Comma-separated splits. Example: train,val,test"
    )
    parser.add_argument(
        "--mode",
        choices=["independent", "continuous"],
        help="independent: each split starts from --start; continuous: next split continues numbering"
    )
    parser.add_argument(
        "--start",
        type=int,
        help="Start index"
    )
    parser.add_argument(
        "--digits",
        type=int,
        help="Zero padding digits. 0 means no zero-padding"
    )
    parser.add_argument(
        "--exts",
        type=str,
        help="Comma-separated image extensions. Example: .jpg,.jpeg,.png"
    )

    run_group = parser.add_mutually_exclusive_group()
    run_group.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Preview only, no file changes"
    )
    run_group.add_argument(
        "--apply",
        dest="dry_run",
        action="store_false",
        help="Actually rename files"
    )
    parser.set_defaults(dry_run=None)

    return parser


# 合并默认配置、文件配置和命令行参数，输出最终配置。
def build_config(args) -> dict:
    cfg = DEFAULT_CONFIG.copy()

    file_cfg = load_config(args.config)
    cfg.update(file_cfg)

    if args.root is not None:
        cfg["root"] = args.root
    if args.splits is not None:
        cfg["splits"] = parse_splits(args.splits)
    else:
        cfg["splits"] = parse_splits(cfg.get("splits", ["train", "val"]))

    if args.mode is not None:
        cfg["mode"] = args.mode
    if args.start is not None:
        cfg["start"] = args.start
    if args.digits is not None:
        cfg["digits"] = args.digits
    if args.exts is not None:
        cfg["img_exts"] = [x.strip() for x in args.exts.split(",") if x.strip()]
    if args.dry_run is not None:
        cfg["dry_run"] = args.dry_run

    if not cfg.get("root"):
        raise ValueError("Dataset root is required. Use --root or provide it in config file.")

    if cfg["mode"] not in ("independent", "continuous"):
        raise ValueError("mode must be 'independent' or 'continuous'.")

    if int(cfg["start"]) < 0:
        raise ValueError("start must be >= 0.")

    if int(cfg["digits"]) < 0:
        raise ValueError("digits must be >= 0.")

    cfg["img_exts"] = normalize_exts(cfg.get("img_exts"))
    cfg["root"] = Path(cfg["root"])

    return cfg


# 程序主入口
def main():
    # parser=参数解析器；args=命令行输入；cfg=最终配置
    # next_index=连续编号游标；current_start=当前 split 的起始编号
    parser = build_parser()
    args = parser.parse_args()
    cfg = build_config(args)

    root = cfg["root"]
    splits = cfg["splits"]
    mode = cfg["mode"]
    start = int(cfg["start"])
    digits = int(cfg["digits"])
    dry_run = bool(cfg["dry_run"])
    img_exts = cfg["img_exts"]

    next_index = start

    for split in splits:
        images_dir = root / "images" / split
        labels_dir = root / "labels" / split

        current_start = next_index if mode == "continuous" else start

        next_index = rename_split(
            images_dir=images_dir,
            labels_dir=labels_dir,
            start_index=current_start,
            digits=digits,
            dry_run=dry_run,
            img_exts=img_exts,
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
