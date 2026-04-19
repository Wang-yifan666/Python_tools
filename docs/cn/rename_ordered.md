# rename_files_in_order.py

按文件名顺序批量重命名指定文件夹中的文件。

## 功能说明

该脚本用于将一个文件夹中的文件按顺序重命名，

## 使用方法

先查看帮助：

```
python tools/rename_files_in_order.py --help
```

不真正修改文件：

```
python tools/rename_files_in_order.py --folder D:/data/files --dry-run
```

执行重命名：

```
python tools/rename_files_in_order.py --folder D:/data/files --prefix img_ --start 1 --digits 4 --apply
```

仅处理指定扩展名：

```bash
python tools/rename_files_in_order.py --folder D:/data/files --exts .jpg,.png --prefix file_ --apply
```

使用 JSON 配置文件：

```bash
python tools/rename_files_in_order.py --config json/rename_files_in_order.json
```

---

## 参数说明

### `--config`

可选，JSON 配置文件路径。

### `--folder`

目标文件夹路径。

例如：

```bash
--folder D:/data/files
```

### `--prefix`

重命名后的文件名前缀。

例如：

```bash
--prefix img_
```

### `--start`

起始编号。

例如：

```bash
--start 1
```

### `--digits`

编号补零位数。

例如：

* `4` -> `0001`
* `3` -> `001`
* `0` -> 不补零

```bash
--digits 4
```

### `--exts`

只处理指定扩展名，多个扩展名用英文逗号分隔。

例如：

```bash
--exts .jpg,.png,.txt
```

### `--dry-run`

只预览，不修改文件。

### `--apply`

实际执行重命名。

---

## 配置文件示例

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
