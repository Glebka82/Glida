import os
import pycdlib
import re
import hashlib


def get_safe_iso_name(original_name, is_dir=False):
    """
    Generates a strict ISO9660 compliant base name (A-Z, 0-9, _).
    This name is hidden by Joliet/Rock Ridge but required by the library.
    """
    name, ext = os.path.splitext(original_name)

    # Strip all non-compliant characters
    clean_name = re.sub(r'[^A-Z0-9_]', '', name.upper())
    clean_ext = re.sub(r'[^A-Z0-9_]', '', ext.upper()) if not is_dir else ""

    # If the name was purely Cyrillic, it might be empty now. Give it a default.
    if not clean_name:
        clean_name = "DIR" if is_dir else "FILE"

    # Add a short MD5 hash of the original name to guarantee uniqueness
    hash_suffix = hashlib.md5(original_name.encode('utf-8')).hexdigest()[:5].upper()

    # Assemble the compliant name (e.g., FILE_A1B2C.PNG)
    safe_name = f"{clean_name[:15]}_{hash_suffix}"
    if clean_ext and not is_dir:
        safe_name += f".{clean_ext[:3]}"

    return safe_name


def create_iso_from_folder(source_dir, output_iso_path):
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, rock_ridge='1.12')

    # We need to track the strict ISO paths as we walk through folders
    dir_iso_map = {".": "/"}

    for root, dirs, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)

        # Get the strict ISO directory path from our map
        current_iso_dir = dir_iso_map[rel_path]

        # Joliet uses the normal paths
        current_joliet_dir = "/" if rel_path == "." else f"/{rel_path.replace(os.sep, '/')}"

        # 1. Process Directories
        for d in dirs:
            child_rel = os.path.relpath(os.path.join(root, d), source_dir)

            # Generate a strict name and store it in the map
            safe_d = get_safe_iso_name(d, is_dir=True)
            child_iso_dir = f"{current_iso_dir}{safe_d}/" if current_iso_dir == "/" else f"{current_iso_dir}/{safe_d}/"
            dir_iso_map[child_rel] = child_iso_dir.rstrip('/')

            # The real path for display
            child_joliet_dir = f"{current_joliet_dir}{d}" if current_joliet_dir == "/" else f"{current_joliet_dir}/{d}"

            iso.add_directory(dir_iso_map[child_rel],
                              joliet_path=child_joliet_dir,
                              rr_name=d)

        # 2. Process Files
        for f in files:
            local_path = os.path.join(root, f)

            # Strict file path for ISO9660
            safe_f = get_safe_iso_name(f, is_dir=False)
            iso_file_path = f"{current_iso_dir}{safe_f}" if current_iso_dir == "/" else f"{current_iso_dir}/{safe_f}"

            # Real file path for Joliet/Rock Ridge
            joliet_file_path = f"{current_joliet_dir}{f}" if current_joliet_dir == "/" else f"{current_joliet_dir}/{f}"

            iso.add_file(local_path,
                         iso_path=iso_file_path + ";1",
                         joliet_path=joliet_file_path,
                         rr_name=f)

    iso.write(output_iso_path)
    iso.close()
    print(f"ISO created successfully at: {output_iso_path}")

# Run the function
if __name__ == '__main__':
    create_iso_from_folder("E:/", "disk.iso")