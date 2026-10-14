
import os
import sys
import time
import subprocess
import psutil

# ==========================================
# TEST: Child Process Memory Monitoring
# ==========================================

MEMORY_MB = 100

# Code executed by the child Python process
child_code = """
import os
import time

data = bytearray(100 * 1024 * 1024)

# Touch memory pages to commit RAM
for i in range(0, len(data), 4096):
    data[i] = 1

print("100 MB allocated", flush=True)
print("Actual child PID:", os.getpid(), flush=True)

time.sleep(15)
"""

print("=" * 55)
print("CHILD PROCESS MEMORY TEST")
print("=" * 55)

print("Parent Python PID:", os.getpid())
print("Launching child process...", flush=True)

child = subprocess.Popen(
    [sys.executable, "-u", "-c", child_code],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

try:
    # Read information directly from actual child output
    first_line = child.stdout.readline().strip()
    second_line = child.stdout.readline().strip()

    print(first_line)
    print(second_line)

    actual_pid = None

    if second_line.startswith("Actual child PID:"):
        actual_pid = int(second_line.split(":")[1].strip())

    time.sleep(2)

    # Process returned by subprocess
    process = psutil.Process(child.pid)

    print("\n" + "=" * 55)
    print("PROCESS IDENTIFICATION")
    print("=" * 55)

    print("Parent Python PID:", os.getpid())
    print("Child PID from subprocess:", child.pid)
    print("Child PID from psutil:", process.pid)
    print("Actual Python PID:", actual_pid)
    print("Child name:", process.name())
    print("Child status:", process.status())
    print("Child running:", child.poll() is None)

    print("\n" + "=" * 55)
    print("PROCESS MEMORY")
    print("=" * 55)

    def show_memory(proc, label):
        try:
            info = proc.memory_info()

            print(f"\n{label}")
            print("PID:", proc.pid)
            print(
                f"Current RSS: "
                f"{info.rss / 1024**2:.2f} MB"
            )
            print(
                f"Current VMS: "
                f"{info.vms / 1024**2:.2f} MB"
            )

        except psutil.Error as error:
            print(f"Memory reading error: {error}")

    show_memory(process, "Subprocess Memory")

    # Monitor actual process PID
    if actual_pid is not None:
        try:
            real_process = psutil.Process(actual_pid)
            show_memory(real_process, "Actual Python Process Memory")
        except psutil.Error as error:
            print("Actual process error:", error)

    print("\n" + "=" * 55)
    print("CHILD PROCESS TREE")
    print("=" * 55)

    children = process.children(recursive=True)

    if not children:
        print("No child processes found.")
    else:
        for sub_process in children:
            try:
                print("------------------------------")
                print("PID:", sub_process.pid)
                print("Name:", sub_process.name())
                print("Status:", sub_process.status())
                print(
                    "RAM:",
                    round(
                        sub_process.memory_info().rss / 1024**2,
                        2
                    ),
                    "MB"
                )
            except psutil.Error as error:
                print("Process inspection error:", error)

    print("\n" + "=" * 55)
    print("TEST COMPLETED")
    print("=" * 55)

finally:
    # Terminate actual process if still running
    if actual_pid is not None and actual_pid != child.pid:
        try:
            actual_process = psutil.Process(actual_pid)

            if actual_process.is_running():
                actual_process.terminate()
                actual_process.wait(timeout=5)

        except psutil.Error:
            pass

    # Terminate any remaining child processes
    try:
        parent_process = psutil.Process(child.pid)

        for sub_process in parent_process.children(recursive=True):
            try:
                sub_process.terminate()
            except psutil.Error:
                pass

    except psutil.Error:
        pass

    if child.poll() is None:
        child.terminate()

    try:
        child.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        child.kill()
        child.communicate()

    print("Child process cleanup completed.")
