import sys
import os
import subprocess
import re
from datetime import datetime

VERSION = "7.5.0"
LOG_FILE = "log.txt"

# --- UTILITY LIBRARY ---

def log(action, status, detail="", code=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    divider = "=" * 60
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{divider}\n")
        f.write(f"[{timestamp}] ACTION: {action} | STATUS: {status}")
        if code is not None: f.write(f" | EXIT_CODE: {code}")
        f.write("\n")
        if detail: f.write(f"DETAILS:\n{detail}\n")

def decode_binary(filename):
    with open(filename, "r") as f:
        bin_str = f.read().strip()
    return ''.join(chr(int(bin_str[i:i+8], 2)) for i in range(0, len(bin_str), 8))

# --- CORE FUNCTIONS ---

def make_file(filename, text, extension):
    try:
        base_name = filename.replace(".mkr", "")
        mkr_name = f"{base_name}.mkr"
        inf_name = f"info.{base_name}.inf"

        # 1. Create .mkr (Binary)
        binary_data = ''.join(format(ord(c), '08b') for c in text)
        with open(mkr_name, "w") as f:
            f.write(binary_data)
        
        # 2. Create .inf (Metadata)
        with open(inf_name, "w") as f:
            f.write(extension.lower())

        log("MAKE", "SUCCESS", detail=f"Files: {mkr_name}, {inf_name}\nExt: {extension}")
        print(f"Success: Created {mkr_name} and {inf_name} (Type: {extension})")
    except Exception as e:
        log("MAKE", "ERROR", detail=str(e))
        print(f"Encoding Error: {e}")

def smart_run(filename):
    """Automatically detects type from .inf file and runs it."""
    base_name = filename.replace(".mkr", "")
    mkr_path = f"{base_name}.mkr"
    inf_path = f"info.{base_name}.inf"

    if not os.path.exists(mkr_path):
        print(f"Error: {mkr_path} not found."); return

    # Detect extension
    if os.path.exists(inf_path):
        with open(inf_path, "r") as f:
            ext = f.read().strip()
    else:
        print(f"Warning: No .inf file found for {filename}. Defaulting to Python.")
        ext = "py"

    # Route to correct runner
    if ext == "java":
        run_java(mkr_path)
    else:
        run_python(mkr_path)

def run_java(filename):
    try:
        code = decode_binary(filename)
        class_match = re.search(r'public\s+class\s+(\w+)', code)
        class_name = class_match.group(1) if class_match else "Runner"
        java_file = f"{class_name}.java"

        with open(java_file, "w", encoding="utf-8") as j:
            j.write(code)
        
        print(f"Executing Java: {class_name}...")
        process = subprocess.Popen(["java", java_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        print(stdout if process.returncode == 0 else stderr)
        
        for ext in [".java", ".class"]:
            if os.path.exists(f"{class_name}{ext}"): os.remove(f"{class_name}{ext}")
    except Exception as e: print(f"Java System Error: {e}")

def run_python(filename):
    try:
        code = decode_binary(filename)
        temp_py = "temp_exec.py"
        with open(temp_py, "w", encoding="utf-8") as f: f.write(code)
        print(f"Executing Python: {filename}...")
        result = subprocess.run([sys.executable, temp_py], capture_output=True, text=True)
        print(result.stdout if result.returncode == 0 else result.stderr)
        if os.path.exists(temp_py): os.remove(temp_py)
    except Exception as e: print(f"Python System Error: {e}")

# --- CLI ROUTER ---

def main():
    args = sys.argv[1:]
    
    if "--version" in args:
        print(f"MAKER CLI Version: {VERSION}"); return

    if not args or "--help" in args:
        print("\nMAKER CLI v7.5.0\n" + "-"*30)
        print("maker --file [name] --text [code] --extension [py/java]")
        print("maker --run [file].mkr             (Auto-detects via .inf)")
        print("maker --delete [file]              (Deletes .mkr and .inf)")
    
    elif "--file" in args:
        try:
            f_idx, t_idx, e_idx = args.index("--file"), args.index("--text"), args.index("--extension")
            make_file(args[f_idx+1], " ".join(args[t_idx+1:e_idx]), args[e_idx+1])
        except (ValueError, IndexError):
            print("Error: Usage: maker --file [name] --text [code] --extension [py/java]")
            
    elif "--run" in args:
        try:
            smart_run(args[args.index("--run") + 1])
        except: print("Error: Specify .mkr file.")

    elif "--delete" in args:
        try:
            name = args[args.index("--delete") + 1].replace(".mkr", "")
            for f in [f"{name}.mkr", f"info.{name}.inf"]:
                if os.path.exists(f): os.remove(f); print(f"Deleted {f}")
        except: print("Error: Specify file to delete.")

if __name__ == "__main__":
    main()