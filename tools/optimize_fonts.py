#!/usr/bin/env python3
"""ลดขนาดฟอนต์ที่ฝังใน index.html: ตัดเหลือเฉพาะอักษรไทย/อังกฤษ/สัญลักษณ์ที่ใช้บ่อย (คงเป็น TrueType เพื่อให้เว็บตรวจตาราง PUA ของสระ/วรรณยุกต์ได้เหมือนเดิม)
ใช้: python tools/optimize_fonts.py index.html   (ต้องมี: pip install fonttools)"""
import base64, io, json, re, sys
from fontTools import subset
from fontTools.ttLib import TTFont

UNICODES = "U+0020-007E,U+00A0-00FF,U+0E00-0E7F,U+2000-206F,U+20A0-20CF,U+2190-21FF,U+2600-27BF,U+F700-F71F"
LIMIT = 400_000  # ฟอนต์ที่ใหญ่กว่านี้ (base64) จะถูกลดขนาด

def shrink(data_url):
    raw = base64.b64decode(data_url.split(",", 1)[1])
    f = TTFont(io.BytesIO(raw))
    opt = subset.Options(); opt.layout_features = ["*"]; opt.name_IDs = ["*"]; opt.notdef_outline = True
    s = subset.Subsetter(opt); s.populate(unicodes=subset.parse_unicodes(UNICODES)); s.subset(f)
    out = io.BytesIO(); f.flavor = None; f.save(out)
    return "data:font/ttf;base64," + base64.b64encode(out.getvalue()).decode()

def main(path):
    html = open(path, encoding="utf-8").read()
    pat = re.compile(r'(<script type="application/json" id="cfg">)([\s\S]*?)(</script>)')
    m = pat.search(html)
    if not m: print("no cfg"); return 0
    cfg = json.loads(m.group(2)); changed = 0
    for f in cfg.get("fonts", []):
        d = f.get("data") or ""
        if len(d) > LIMIT:
            try:
                nd = shrink(d)
            except Exception as e:
                print("skip", f.get("name"), e); continue
            if len(nd) < len(d):
                print(f"{f.get('name')}: {len(d):,} -> {len(nd):,}"); f["data"] = nd; changed += 1
    if not changed: print("nothing to optimize"); return 0
    js = json.dumps(cfg, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html = html[:m.start(2)] + js + html[m.end(2):]
    open(path, "w", encoding="utf-8").write(html); return changed

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "index.html")
