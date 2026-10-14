
import ctypes
import subprocess
import sys
from ctypes import wintypes

class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]
    

psapi = ctypes.WinDLL("psapi", use_last_error=True)

psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
    wintypes.DWORD
]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

child_code = """
import time
data = bytearray(100 * 1024 * 1024)
for i in range(0, len(data), 4096):
    data[i] = 1
print("100 MB allocated", flush=True)
time.sleep(5)
"""

child = subprocess.Popen(
    [sys.executable, "-u", "-c", child_code]
)

try:
    import time
    time.sleep(2)

    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(counters)

    success = psapi.GetProcessMemoryInfo(
        child._handle,
        ctypes.byref(counters),
        counters.cb
    )

    if not success:
        raise ctypes.WinError(ctypes.get_last_error())

    print("WINDOWS CHILD MEMORY TEST")
    print(
        f"Current RAM: "
        f"{counters.WorkingSetSize / 1024**2:.2f} MB"
    )
    print(
        f"Peak RAM: "
        f"{counters.PeakWorkingSetSize / 1024**2:.2f} MB"
    )

finally:
    if child.poll() is None:
        child.terminate()
    child.wait()
