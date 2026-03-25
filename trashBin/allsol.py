import shutil

def restore_usb(image_file, new_usb_path):
    try:
        with open(image_file, 'rb') as src, open(new_usb_path, 'wb') as dst:
            print(f"משחזר מ-{image_file} ל-{new_usb_path}...")
            shutil.copyfileobj(src, dst, length=1024*1024)
        print("השחזור הסתיים בהצלחה.")
    except PermissionError:
        print("שגיאה: יש להריץ כמנהל.")

# דוגמה לשימוש (Windows):
restore_usb('Windows.iso', r'\\.\PhysicalDrive1')