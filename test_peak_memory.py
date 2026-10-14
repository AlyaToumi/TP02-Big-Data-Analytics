
import ctypes
import os
from ctypes import wintypes

# Windows API
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

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

kernel32.OpenProcess.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.DWORD
]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
    wintypes.DWORD
]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

# Open current process
handle = kernel32.OpenProcess(
    PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
    False,
    os.getpid()
)

if not handle:
    raise ctypes.WinError(ctypes.get_last_error())

try:
    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(counters)

    success = psapi.GetProcessMemoryInfo(
        handle,
        ctypes.byref(counters),
        counters.cb
    )

    if not success:
        raise ctypes.WinError(ctypes.get_last_error())

    print("=" * 45)
    print("WINDOWS MEMORY COUNTER TEST")
    print("=" * 45)

    print(
        f"Current RAM: "
        f"{counters.WorkingSetSize / 1024**2:.2f} MB"
    )

    print(
        f"Peak RAM: "
        f"{counters.PeakWorkingSetSize / 1024**2:.2f} MB"
    )

    print("=" * 45)
    print("Memory counter test completed.")

finally:
    kernel32.CloseHandle(handle)
