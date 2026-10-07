p = r"E:\my projects\pharmacy-system\backend\apps\medicines\views.py"
lines = open(p, encoding="utf-8").read().splitlines(keepends=True)

pat = 'category = self.request.query_params.get("category")'
starts = [i for i, l in enumerate(lines) if l.strip() == pat]
print("starts", starts)


def end_of_run(s):
    e = s
    while e + 1 < len(lines) and (lines[e + 1].startswith("        ") or lines[e + 1].strip() == ""):
        e += 1
    return e


to_remove = None
for s in starts:
    e = end_of_run(s)
    nxt = lines[e + 1] if e + 1 < len(lines) else ""
    print(s, e, repr(nxt))
    if "perform_create" in nxt:
        to_remove = (s, e)
        break

if to_remove:
    s, e = to_remove
    del lines[s:e + 1]
    open(p, "w", encoding="utf-8").write("".join(lines))
    print("REMOVED_TRAILING_RUN")
