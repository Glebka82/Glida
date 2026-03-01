import psutil
import os
import sys


def get_removable_drives():
    """Scans the system and returns a list of connected USB drives."""
    drives = []
    for partition in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'removable' in partition.opts:
                drives.append(partition)
        else:
            if partition.mountpoint.startswith(('/media/', '/run/media/', '/Volumes/')):
                drives.append(partition)
    return drives


def burn_image_to_usb(image_path, target_partition):
    """Bypasses the file system to write an image directly to the physical drive."""

    if not os.path.exists(image_path):
        print(f"❌ Error: Could not find the image file '{image_path}'")
        sys.exit(1)

    # 1. Format the raw hardware path based on the operating system
    if os.name == 'nt':
        # Windows requires \\.\ prefix to access physical drives
        drive_letter = target_partition.device.rstrip('\\')
        raw_device_path = fr"\\.\{drive_letter}"
    else:
        # Linux/macOS use device paths directly (e.g., /dev/sdb1 or /dev/disk2)
        raw_device_path = target_partition.device

    image_size = os.path.getsize(image_path)
    chunk_size = 4 * 1024 * 1024  # 4 Megabytes per chunk

    # 2. The Safety Catch
    print("\n" + "!" * 50)
    print(f"🧨 DANGER ZONE: You are about to overwrite {raw_device_path}")
    print("!" * 50)
    print(f"Source Image: {image_path} ({(image_size / (1024 ** 3)):.2f} GB)")
    print(f"Target Drive: Mounted at {target_partition.mountpoint}")
    print("\nALL EXISTING DATA ON THIS DRIVE WILL BE PERMANENTLY ERASED.")

    confirm = input("Type 'BURN' to proceed: ")
    if confirm != 'BURN':
        print("\nOperation cancelled. No data was changed.")
        sys.exit(0)

    print("\n🚀 Starting the flashing process...")

    # 3. The Write Loop
    try:
        # 'rb' = read binary from the image, 'wb' = write binary to the hardware
        with open(image_path, 'rb') as img_file, open(raw_device_path, 'wb') as usb_drive:
            bytes_written = 0

            while True:
                chunk = img_file.read(chunk_size)
                if not chunk:
                    break  # Reached the end of the image file

                usb_drive.write(chunk)
                bytes_written += len(chunk)

                # Dynamic progress calculation
                percent = (bytes_written / image_size) * 100
                mb_written = bytes_written / (1024 ** 2)

                # \r animates the progress bar on a single line
                print(f"\r⏳ Flashing: {percent:.1f}% ({mb_written:.1f} MB written)", end="")

        print(f"\n\n✅ Success! The image has been loaded onto {raw_device_path}")

    except PermissionError:
        print("\n\n❌ PERMISSION DENIED!")
        print("Bypassing the file system requires elevated privileges.")
        print("Please restart your terminal as Administrator (Windows) or use 'sudo' (Mac/Linux).")
    except OSError as e:
        print(f"\n\n❌ Hardware/OS Error: {e}")
        print("Ensure no other programs (like File Explorer) are currently viewing the USB drive.")


if __name__ == "__main__":
    print("🔍 Scanning for available USB drives...\n")
    available_drives = get_removable_drives()

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

        image_file = input("\nEnter the full path to your .img or .iso file: ")

        burn_image_to_usb(image_file, selected_drive)

    except ValueError:
        print("❌ Please enter a valid number.")