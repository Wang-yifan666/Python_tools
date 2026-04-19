# 建议先阅读 docs/cn(en)/rename_files_in_order.md
# python tools/rename_ordered.py --help
# python tools/rename_ordered.py --folder /path/to/folder --dry-run
# python tools/rename_ordered.py --folder /path/to/folder --prefix img_ --start 1 --digits 4 --apply
# python tools/rename_ordered.py --folder /path/to/folder --exts .jpg,.png --prefix file_ --apply

import argparse
import json
import os
from pathlib import Path
from uuid import uuid4

DEFAULT_CONFIG = {
    "folder": "",
    "prefix": "",
    "start": 1,
    "digits": 4,
    "dry_run": True,
    "exts": [],
}


# 读取 JSON 配置文件并返回字典配置
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


# 将扩展名列表标准化为小写且带点号的元组；若为空则表示不过滤扩展名
def normalize_exts(exts) -> tuple[str, ...] | None:
    if not exts:
        return None

    normalized = []
    for ext in exts:
        ext = str(ext).strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = "." + ext
        normalized.append(ext)

    if not normalized:
        return None

    return tuple(normalized)


# 收集目录下所有匹配扩展名的文件并按名称排序
def collect_files(folder: Path, exts: tuple[str, ...] | None) -> list[Path]:
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Not a folder: {folder}")

    files = []
    for p in folder.iterdir():
        if not p.is_file():
            continue
        if exts is not None and p.suffix.lower() not in exts:
            continue
        files.append(p)

    files.sort(key=lambda p: p.name.lower())
    return files


# 为旧文件路径生成一个唯一、未占用的临时路径
def build_tmp_path(old: Path, used_tmp_paths: set[Path]) -> Path:
    while True:
        candidate = old.with_name(f"{old.stem}.__tmp__.{uuid4().hex}{old.suffix}")
        if candidate not in used_tmp_paths and not candidate.exists():
            used_tmp_paths.add(candidate)
            return candidate


# 使用两段式重命名执行批量改名，避免覆盖冲突
def two_phase_rename(pairs: list[tuple[Path, Path]], dry_run: bool = False):
    # 去掉 old == new 的无效操作
    pairs = [(old, new) for old, new in pairs if old != new]

    if not pairs:
        print("No files need renaming.")
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


# 按文件名顺序重命名目录下文件，保留原扩展名，并返回下一个可用编号
def rename_files_in_order(
    folder: Path,
    prefix: str = "",
    start_index: int = 1,
    digits: int = 4,
    dry_run: bool = True,
    exts: tuple[str, ...] | None = None,
) -> int:
    if start_index < 0:
        raise ValueError("start must be >= 0.")

    if digits < 0:
        raise ValueError("digits must be >= 0.")

    # 收集当前目录下所有符合扩展名的文件（按文件名排序）
    files = collect_files(folder, exts)

    if not files:
        print("\n=======================================")
        print(f"Folder : {folder}")
        print("No matched files found.")
        return start_index

    def fmt(i: int) -> str:
        return str(i).zfill(digits) if digits > 0 else str(i)

    renames = []
    idx = start_index

    # 为每个文件生成新文件名，保留原扩展名（统一为小写）
    for file_path in files:
        new_name = f"{prefix}{fmt(idx)}{file_path.suffix.lower()}"
        new_path = file_path.with_name(new_name)
        renames.append((file_path, new_path))
        idx += 1

    print("\n=======================================")
    print(f"Folder : {folder}")
    print(f"Matched files : {len(files)}")
    print(f"Prefix : {prefix}")
    print(f"Start index : {start_index}")
    print(f"Digits : {digits}")
    print(f"Dry run : {dry_run}")
    print(f"Extensions : {', '.join(exts) if exts else 'ALL'}")
    print("Sort rule : filename ascending\n")

    two_phase_rename(renames, dry_run=dry_run)

    return idx


# 构建命令行参数解析器并定义可用参数
def build_parser():
    parser = argparse.ArgumentParser(
        description="Rename files in a folder sequentially."
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional JSON config file path."
    )
    parser.add_argument(
        "--folder",
        type=str,
        help="Target folder path. Example: D:/data/files"
    )
    parser.add_argument(
        "--prefix",
        type=str,
        help="Filename prefix. Example: img_"
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
        help="Comma-separated file extensions. Example: .jpg,.png,.txt"
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


# 合并默认配置、文件配置和命令行参数，输出最终配置
def build_config(args) -> dict:
    cfg = DEFAULT_CONFIG.copy()

    file_cfg = load_config(args.config)
    cfg.update(file_cfg)

    if args.folder is not None:
        cfg["folder"] = args.folder

    if args.prefix is not None:
        cfg["prefix"] = args.prefix

    if args.start is not None:
        cfg["start"] = args.start

    if args.digits is not None:
        cfg["digits"] = args.digits

    if args.exts is not None:
        cfg["exts"] = [x.strip() for x in args.exts.split(",") if x.strip()]

    if args.dry_run is not None:
        cfg["dry_run"] = args.dry_run

    if not cfg.get("folder"):
        raise ValueError("Target folder is required. Use --folder or provide it in config file.")

    if int(cfg["start"]) < 0:
        raise ValueError("start must be >= 0.")

    if int(cfg["digits"]) < 0:
        raise ValueError("digits must be >= 0.")

    cfg["folder"] = Path(cfg["folder"])
    cfg["exts"] = normalize_exts(cfg.get("exts"))

    return cfg


# 程序主入口
def main():
    # parser=参数解析器；args=命令行输入；cfg=最终配置
    # folder=目标目录；prefix=文件名前缀；next_index=下一个可用编号
    parser = build_parser()
    args = parser.parse_args()
    cfg = build_config(args)

    folder = cfg["folder"]
    prefix = str(cfg["prefix"])
    start = int(cfg["start"])
    digits = int(cfg["digits"])
    dry_run = bool(cfg["dry_run"])
    exts = cfg["exts"]

    next_index = rename_files_in_order(
        folder=folder,
        prefix=prefix,
        start_index=start,
        digits=digits,
        dry_run=dry_run,
        exts=exts,
    )

    print(f"\nNext available index: {next_index}")
    print("Done.")


if __name__ == "__main__":
    main()
