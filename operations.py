import psutil
import os

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