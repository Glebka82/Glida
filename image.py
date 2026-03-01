import psutil
import os
import sys


def get_usb_partitions():
    """Returns a list of psutil partition objects for USB drives."""
    usb_drives = []
    for partition in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'removable' in partition.opts:
                usb_drives.append(partition)
        else:
            if partition.mountpoint.startswith('/media/') or \
                    partition.mountpoint.startswith('/run/media/') or \
                    partition.mountpoint.startswith('/Volumes/'):
                usb_drives.append(partition)
    return usb_drives


def create_disk_image(partition, output_filename):
    """Reads a partition byte-by-byte and writes it to an image file."""

    # 1. Format the raw device path depending on the OS
    if os.name == 'nt':
        # Windows requires a special prefix to read raw disks.
        # We turn "E:\" into "\\.\E:"
        drive_letter = partition.device.rstrip('\\')
        raw_device_path = fr"\\.\{drive_letter}"
    else:
        # Linux/Mac already use raw device paths like "/dev/sdb1"
        raw_device_path = partition.device

    # 2. Set a chunk size (4 Megabytes).
    # We read in chunks so we don't crash your RAM on a 64GB flash drive!
    chunk_size = 4 * 1024 * 1024

    print(f"\n🚀 Starting imaging process...")
    print(f"📖 Reading from: {raw_device_path}")
    print(f"💾 Writing to:   {os.path.abspath(output_filename)}")
    print("⏳ Please wait, this may take a while depending on the USB size...")

    try:
        # Open the USB for raw binary reading ('rb') and the file for binary writing ('wb')
        with open(raw_device_path, 'rb') as src_disk, open(output_filename, 'wb') as img_file:
            bytes_copied = 0

            while True:
                # Read a 4MB chunk
                chunk = src_disk.read(chunk_size)

                # If the chunk is empty, we reached the end of the drive
                if not chunk:
                    break

                # Write the chunk to our image file
                img_file.write(chunk)
                bytes_copied += len(chunk)

        print(f"\n✅ Success! Copied {bytes_copied / (1024 ** 2):.2f} MB to {output_filename}")

    except PermissionError:
        print("\n❌ PERMISSION DENIED!")
        print("To read raw disk bytes, you MUST run this script as Administrator (Windows) or root/sudo (Linux/Mac).")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    print("🔍 Scanning for USB drives...\n")
    drives = get_usb_partitions()

    if not drives:
        print("No USB drives found. Please plug one in.")
        sys.exit()

    # Display a simple interactive menu
    print("Select a USB drive to image:")
    for index, drive in enumerate(drives):
        print(f" [{index}] Device: {drive.device} (Mounted at: {drive.mountpoint})")

    # Get user input
    try:
        choice = int(input("\nEnter the number of the drive: "))
        if choice < 0 or choice >= len(drives):
            print("Invalid selection.")
            sys.exit()

        selected_drive = drives[choice]
        output_name = f"usb_backup_{choice}.img"

        # Start the imaging process
        create_disk_image(selected_drive, output_name)

    except ValueError:
        print("Please enter a valid number.")