import shutil
import os
import sys
import operations
from pathlib import Path


def load_file_to_usb(source_file_path, usb_mount_point):
    source = Path(source_file_path)
    usb_dest = Path(usb_mount_point)

    if not source.exists() or not source.is_file():
        print(f"❌ Error: Could not find file at absolute path: {source}")
        return

    final_destination = usb_dest / source.name

    try:
        print(f"📡 Transferring '{source.name}'...")
        print(f"   From: {source}")
        print(f"   To:   {final_destination}")

        # 3. Perform the copy (copy2 preserves original file metadata)
        shutil.copy2(source, final_destination)

        print("✅ Transfer Complete!")

    except Exception as e:
        print(f"❌ Failed to copy file: {e}")


# --- How you call it in your code ---
# load_file_to_usb("E:/as/dfgds/sfds/aa.pig", "G:/")

if __name__ == "__main__":
    print("🔍 Scanning for available USB drives...\n")
    available_drives = operations.get_removable_drives()

    if not available_drives:
        print("❌ No USB drives detected. Please plug one in and restart.")
        sys.exit(0)

    print("Select the TARGET USB drive:")
    for i, drive in enumerate(available_drives):
        print(f" [{i}] {drive.device} (Mounted at: {drive.mountpoint})")

    try:
        choice = int(input("\nEnter the number of the target drive: "))
        if choice < 0 or choice >= len(available_drives):
            print("❌ Invalid selection.")
            sys.exit(1)

        selected_drive = available_drives[choice]

        file_to_mount = input("\nEnter the full path to your file: ")
        load_file_to_usb(file_to_mount, selected_drive.device)  # Windows style

    except ValueError:
        print("❌ Please enter a valid number.")
