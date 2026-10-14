import os, sys, zipfile

def build_epub(src_dir, out_path):
    src_dir = os.path.abspath(src_dir)
    mimetype = os.path.join(src_dir, "mimetype")
    if not os.path.isfile(mimetype):
        raise SystemExit("mimetype missing in %s" % src_dir)
    if os.path.exists(out_path):
        os.remove(out_path)
    with zipfile.ZipFile(out_path, "w") as z:
        # 1) mimetype first, STORED (uncompressed), no extra fields
        zi = zipfile.ZipInfo("mimetype")
        zi.compress_type = zipfile.ZIP_STORED
        with open(mimetype, "rb") as f:
            z.writestr(zi, f.read())
        # 2) everything else, deflated, deterministic order
        for root, dirs, files in os.walk(src_dir):
            dirs.sort()
            for name in sorted(files):
                full = os.path.join(root, name)
                rel = os.path.relpath(full, src_dir).replace(os.sep, "/")
                if rel == "mimetype":
                    continue
                with open(full, "rb") as f:
                    z.writestr(
                        zipfile.ZipInfo(rel), f.read(),
                        compress_type=zipfile.ZIP_DEFLATED,
                    )
    return out_path

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    p = build_epub(src, out)
    size = os.path.getsize(p)
    with zipfile.ZipFile(p) as z:
        names = z.namelist()
        first = names[0]
        first_info = z.getinfo("mimetype")
        stored = first_info.compress_type == zipfile.ZIP_STORED
    print("OK %s bytes=%d entries=%d first=%s mimetype_stored=%s" % (
        p, size, len(names), first, stored))
