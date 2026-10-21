import json
import hashlib
import re
import sys
import os
# 计算本地文件 fan.txt 的 md5
def get_md5(filepath):
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            md5.update(chunk)
    return md5.hexdigest()

# 加载 JSON 文件
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 保存 JSON 文件（折叠字典数组为单行，空数组和基础数组一行）
class CompactJSONEncoder(json.JSONEncoder):
    def iterencode(self, o, _one_shot=False):
        def _compact_list(lst, indent_level):
            pad = '  ' * indent_level
            if not lst or all(isinstance(i, (str, int, float, bool, type(None))) for i in lst):
                return json.dumps(lst, ensure_ascii=False)
            if all(isinstance(i, dict) for i in lst):
                return '[\n' + ',\n'.join([pad + '  ' + json.dumps(i, ensure_ascii=False, separators=(',', ': ')) for i in lst]) + '\n' + pad + ']'
            return json.dumps(lst, ensure_ascii=False, indent=2)

        def _encode(obj, indent_level=0):
            pad = '  ' * indent_level
            if isinstance(obj, dict):
                lines = [f'"{k}": {_encode(v, indent_level+1)}' for k, v in obj.items()]
                return '{\n' + pad + '  ' + (',\n' + pad + '  ').join(lines) + '\n' + pad + '}'
            elif isinstance(obj, list):
                return _compact_list(obj, indent_level)
            return json.dumps(obj, ensure_ascii=False)

        return iter([_encode(o)])

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=CompactJSONEncoder)
    print(f"✅ 已保存：{path}")

# 插入 cleaned_sites 到目标 sites 中的目标条目之上
def insert_sites(base_sites, cleaned_sites, key_marker="奇优"):
    for i, item in enumerate(base_sites):
        if item.get("key") == key_marker:
            return base_sites[:i] + cleaned_sites + base_sites[i:]
    print(f"⚠️ 未找到 key 为 {key_marker} 的插入点，追加到末尾")
    return base_sites + cleaned_sites

if __name__ == "__main__":
    # 默认路径
    dianshi_path = "dianshi.json"
    cleaned_path = "tvbox_cleaned.json"

    # 覆盖默认路径（如果传了参数）
    if len(sys.argv) > 1:
        dianshi_path = sys.argv[1]
    if len(sys.argv) > 2:
        cleaned_path = sys.argv[2]

    try:
        # 获取 fan.txt 的 md5
        md5_value = get_md5("fan.txt")
        print(f"🔐 fan.txt 的 MD5: {md5_value}")

        # 加载两个 JSON 文件
        dianshi = load_json(dianshi_path)
        cleaned = load_json(cleaned_path)

        # 替换 spider md5
        if "spider" in dianshi:
            old_spider = dianshi["spider"]
            new_spider = re.sub(r'md5;[a-f0-9]+', f'md5;{md5_value}', old_spider)
            dianshi["spider"] = new_spider
            print(f"🔄 替换 spider 字段为: {new_spider}")
        else:
            print("⚠️ dianshi.json 中未找到 spider 字段")

        # 插入 sites
        cleaned_sites = cleaned.get("sites", [])
        dianshi["sites"] = insert_sites(dianshi.get("sites", []), cleaned_sites)
        name, ext = os.path.splitext(dianshi_path)
        output_path = f"{name}_merged{ext}"

        save_json(dianshi, output_path)
        # 保存最终合并文件
        # save_json(dianshi, "dianshi_merged.json")

    except Exception as e:
        print(f"❌ 出错: {e}")
