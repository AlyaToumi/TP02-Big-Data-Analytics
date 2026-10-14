
import ctypes
import os
import subprocess
import sys
import time

import psutil
from ctypes import wintypes


# ============================================
# CONFIGURATION
# ============================================

MEMORY_LIMIT_GIB = 3
MEMORY_LIMIT = MEMORY_LIMIT_GIB * 1024**3

TIMEOUT_SECONDS = 300
MONITOR_INTERVAL = 0.1

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

SELF_TEST = "--self-test" in sys.argv


# ============================================
# WINDOWS API
# ============================================

kernel32 = ctypes.WinDLL(
    "kernel32",
    use_last_error=True
)

SIZE_T = ctypes.c_size_t


class LARGE_INTEGER(ctypes.Structure):
    _fields_ = [
        ("QuadPart", ctypes.c_longlong)
    ]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_uint64)
        for name in [
            "ReadOperationCount",
            "WriteOperationCount",
            "OtherOperationCount",
            "ReadTransferCount",
            "WriteTransferCount",
            "OtherTransferCount",
        ]
    ]


class BASIC_LIMITS(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", LARGE_INTEGER),
        ("PerJobUserTimeLimit", LARGE_INTEGER),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", SIZE_T),
        ("MaximumWorkingSetSize", SIZE_T),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", SIZE_T),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class EXTENDED_LIMITS(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", BASIC_LIMITS),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", SIZE_T),
        ("JobMemoryLimit", SIZE_T),
        ("PeakProcessMemoryUsed", SIZE_T),
        ("PeakJobMemoryUsed", SIZE_T),
    ]


JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9


kernel32.CreateJobObjectW.argtypes = [
    ctypes.c_void_p,
    wintypes.LPCWSTR
]
kernel32.CreateJobObjectW.restype = wintypes.HANDLE


kernel32.SetInformationJobObject.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    ctypes.c_void_p,
    wintypes.DWORD
]
kernel32.SetInformationJobObject.restype = wintypes.BOOL


kernel32.AssignProcessToJobObject.argtypes = [
    wintypes.HANDLE,
    wintypes.HANDLE
]
kernel32.AssignProcessToJobObject.restype = wintypes.BOOL


kernel32.QueryInformationJobObject.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD)
]
kernel32.QueryInformationJobObject.restype = wintypes.BOOL


kernel32.CloseHandle.argtypes = [
    wintypes.HANDLE
]
kernel32.CloseHandle.restype = wintypes.BOOL


# ============================================
# WINDOWS JOB MEMORY LIMIT
# ============================================

def create_limited_job():

    job = kernel32.CreateJobObjectW(None, None)

    if not job:
        raise ctypes.WinError(ctypes.get_last_error())

    info = EXTENDED_LIMITS()

    info.BasicLimitInformation.LimitFlags = (
        JOB_OBJECT_LIMIT_JOB_MEMORY
        | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    )

    info.JobMemoryLimit = MEMORY_LIMIT

    success = kernel32.SetInformationJobObject(
        job,
        JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
        ctypes.byref(info),
        ctypes.sizeof(info)
    )

    if not success:
        error = ctypes.get_last_error()
        kernel32.CloseHandle(job)
        raise ctypes.WinError(error)

    return job


# ============================================
# GET WINDOWS JOB MEMORY PEAK
# ============================================

def get_job_memory_peak(job):

    info = EXTENDED_LIMITS()

    success = kernel32.QueryInformationJobObject(
        job,
        JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
        ctypes.byref(info),
        ctypes.sizeof(info),
        None
    )

    if not success:
        raise ctypes.WinError(ctypes.get_last_error())

    return info.PeakJobMemoryUsed


# ============================================
# PROCESS TREE MEMORY
# ============================================

def get_process_tree_memory(pid):

    total_rss = 0
    process_count = 0
    process_details = []

    try:
        parent = psutil.Process(pid)

        processes = [parent]
        processes.extend(
            parent.children(recursive=True)
        )

        for proc in processes:

            try:
                if not proc.is_running():
                    continue

                rss = proc.memory_info().rss

                total_rss += rss
                process_count += 1

                process_details.append(
                    (proc.pid, rss)
                )

            except psutil.Error:
                continue

    except psutil.Error:
        pass

    return total_rss, process_count, process_details


# ============================================
# CHILD PROGRAM
# ============================================

if SELF_TEST:

    child_code = """
import os
import time

data = bytearray(100 * 1024 * 1024)

for i in range(0, len(data), 4096):
    data[i] = 1

print("SELF TEST: 100 MB allocated", flush=True)
print("Actual Python PID:", os.getpid(), flush=True)

time.sleep(5)

print("SELF TEST COMPLETED", flush=True)
"""

else:

    child_code = """
import runpy

runpy.run_path(
    "task1_pandas.py",
    run_name="__main__"
)
"""


# Wait until Windows Job limit is applied.
bootstrap_code = """
import sys

sys.stdin.buffer.read(1)

exec(
    compile(
        sys.argv[1],
        "<child_test>",
        "exec"
    )
)
"""


# ============================================
# MAIN PROGRAM
# ============================================

def main():

    job = None
    child = None

    peak_rss = 0
    max_process_count = 0
    peak_process_details = []

    start_time = time.perf_counter()

    print("=" * 55)
    print("TASK 1: PROTECTED MEMORY TEST")
    print("=" * 55)

    print("Memory limit:", MEMORY_LIMIT_GIB, "GiB")
    print("Monitoring: Complete Process Tree")
    print("Test mode:", "SELF TEST" if SELF_TEST else "PANDAS")
    print("=" * 55, flush=True)

    try:

        # Create Windows Job with memory limit.
        job = create_limited_job()

        # Create child that waits for permission.
        child = subprocess.Popen(
            [
                sys.executable,
                "-u",
                "-c",
                bootstrap_code,
                child_code
            ],
            cwd=PROJECT_DIR,
            stdin=subprocess.PIPE
        )

        print("Launcher PID:", child.pid, flush=True)

        # Assign launcher to Windows Job.
        # Descendant processes inherit Job limits.
        success = kernel32.AssignProcessToJobObject(
            job,
            int(child._handle)
        )

        if not success:
            raise ctypes.WinError(ctypes.get_last_error())

        print("Windows Job memory limit applied.")
        print("Starting child process...", flush=True)

        # Start the child only after the limit is set.
        child.stdin.write(b"1")
        child.stdin.flush()
        child.stdin.close()

        start_time = time.perf_counter()

        # ====================================
        # MONITOR PROCESS TREE
        # ====================================

        while child.poll() is None:

            elapsed = time.perf_counter() - start_time

            rss, count, details = get_process_tree_memory(
                child.pid
            )

            if rss > peak_rss:
                peak_rss = rss
                peak_process_details = details

            max_process_count = max(
                max_process_count,
                count
            )

            if elapsed >= TIMEOUT_SECONDS:

                print(
                    "TIMEOUT: stopping test.",
                    flush=True
                )

                child.kill()
                break

            time.sleep(MONITOR_INTERVAL)

        child.wait()

        elapsed = time.perf_counter() - start_time

        # ====================================
        # WINDOWS JOB MEMORY PEAK
        # ====================================

        peak_job_memory = get_job_memory_peak(job)

        # ====================================
        # RESULTS
        # ====================================

        print("\n" + "=" * 55)
        print("PROTECTED TEST SUMMARY")
        print("=" * 55)

        print(
            f"Elapsed time: {elapsed:.2f} seconds"
        )

        print(
            f"Observed peak RSS (process tree): "
            f"{peak_rss / 1024**2:.2f} MB"
        )

        print(
            f"Windows peak job committed memory: "
            f"{peak_job_memory / 1024**2:.2f} MB"
        )

        print(
            f"Maximum observed processes: "
            f"{max_process_count}"
        )

        print("Exit code:", child.returncode)

        print("\nProcesses at highest observed RSS:")

        for pid, rss in peak_process_details:
            print(
                f"PID: {pid} | "
                f"RAM: {rss / 1024**2:.2f} MB"
            )

        print("=" * 55)

    except Exception as error:

        print(
            f"Runner error: "
            f"{type(error).__name__}: {error}",
            flush=True
        )

    finally:

        # Close Job: terminate remaining processes
        # belonging to the Job.
        if job:
            kernel32.CloseHandle(job)

        if child is not None:

            if child.poll() is None:
                child.kill()

            child.wait()

        print(
            "Process cleanup completed.",
            flush=True
        )


if __name__ == "__main__":
    main()
