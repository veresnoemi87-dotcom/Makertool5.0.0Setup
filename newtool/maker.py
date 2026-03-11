import sys
import os
import subprocess
import re
import glob
import http.server
import socketserver
from datetime import datetime

VERSION = "7.7.0"
LOG_FILE = "log.txt"

# --- UTILITY LIBRARY ---

def log(action, status, detail="", code=None):
    """Generates a detailed, scannable log entry."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    divider = "=" * 60
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{divider}\n")
        f.write(f"[{timestamp}] ACTION: {action} | STATUS: {status}")
        if code is not None: f.write(f" | EXIT_CODE: {code}")
        f.write("\n")
        if detail: f.write(f"DETAILS:\n{detail}\n")

def fix_java_syntax(text):
    """Wraps println content in quotes if the user forgot them."""
    pattern = r'System\.out\.println\((?!"|\\")(.*?)(?!"|\\")\);'
    replacement = r'System.out.println("\1");'
    return re.sub(pattern, replacement, text)

def decode_binary(filename):
    """Helper to convert .mkr binary back to string."""
    with open(filename, "r") as f:
        bin_str = f.read().strip()
    return ''.join(chr(int(bin_str[i:i+8], 2)) for i in range(0, len(bin_str), 8))

# --- CORE FUNCTIONS ---

def make_file(filename, text, extension):
    try:
        base_name = filename.replace(".mkr", "")
        mkr_name = f"{base_name}.mkr"
        inf_name = f"info.{base_name}.inf"
        
        # Apply Java auto-fix if needed
        if extension.lower() == "java":
            text = fix_java_syntax(text)

        binary_data = ''.join(format(ord(c), '08b') for c in text)
        with open(mkr_name, "w") as f: f.write(binary_data)
        with open(inf_name, "w") as f: f.write(extension.lower())
        
        print(f"✅ Success: Created {mkr_name} and {inf_name} (Type: {extension})")
        log("MAKE", "SUCCESS", f"File: {mkr_name} | Ext: {extension}")
    except Exception as e:
        print(f"❌ Encoding Error: {e}")
        log("MAKE", "ERROR", str(e))

def import_java():
    """Imports an existing .java file and converts it to .mkr"""
    path = input("Enter path to .java file: ").strip().replace('"', '')
    if not os.path.exists(path):
        print("❌ Error: File not found."); return
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        name = os.path.basename(path).replace(".java", "")
        make_file(name, content, "java")
        log("IMPORT", "SUCCESS", f"Imported: {path}")
    except Exception as e:
        print(f"❌ Import Error: {e}")
        log("IMPORT", "ERROR", str(e))

def list_files():
    """Lists all .mkr and .inf files."""
    mkr_files = glob.glob("*.mkr")
    inf_files = glob.glob("*.inf")
    print(f"\n📂 MAKER PROJECT FILES (v{VERSION})")
    print("-" * 35)
    for f in mkr_files:
        base = f.replace(".mkr", "")
        ext_info = "unknown"
        if os.path.exists(f"info.{base}.inf"):
            with open(f"info.{base}.inf", "r") as i: ext_info = i.read().strip()
        print(f"  [BIN] {f:15} | Type: {ext_info}")
    print("-" * 35)

def start_host(port):
    """Starts a local server."""
    try:
        port = int(port)
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"🚀 Host online at http://localhost:{port}")
            print("Press Ctrl+C to shutdown.")
            httpd.serve_forever()
    except Exception as e: print(f"❌ Host Error: {e}")

def smart_run(filename):
    """Detects type and runs."""
    base_name = filename.replace(".mkr", "")
    inf_path = f"info.{base_name}.inf"
    ext = "py" # Default
    if os.path.exists(inf_path):
        with open(inf_path, "r") as f: ext = f.read().strip()
    
    if ext == "java": run_java(f"{base_name}.mkr")
    else: run_python(f"{base_name}.mkr")

def run_java(filename):
    try:
        code = decode_binary(filename)
        class_match = re.search(r'public\s+class\s+(\w+)', code)
        class_name = class_match.group(1) if class_match else "Runner"
        java_file = f"{class_name}.java"
        with open(java_file, "w", encoding="utf-8") as j: j.write(code)
        
        print(f"☕ Executing Java: {class_name}...")
        process = subprocess.Popen(["java", java_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        print(stdout if process.returncode == 0 else stderr)
        
        for ext in [".java", ".class"]:
            if os.path.exists(f"{class_name}{ext}"): os.remove(f"{class_name}{ext}")
    except Exception as e: print(f"❌ Java Error: {e}")

def run_python(filename):
    try:
        code = decode_binary(filename)
        temp_py = "temp_exec.py"
        with open(temp_py, "w", encoding="utf-8") as f: f.write(code)
        print(f"🐍 Executing Python: {filename}...")
        result = subprocess.run([sys.executable, temp_py], capture_output=True, text=True)
        print(result.stdout if result.returncode == 0 else result.stderr)
        if os.path.exists(temp_py): os.remove(temp_py)
    except Exception as e: print(f"❌ Python Error: {e}")

# --- CLI ROUTER ---

def main():
    args = sys.argv[1:]
    
    if "--version" in args:
        print(f"MAKER CLI Version: {VERSION}"); return

    if "--list" in args:
        list_files(); return

    if "--import" in args:
        import_java(); return

    if not args or "--help" in args:
        print(f"\n🛠️  MAKER TOOLKIT v{VERSION}")
        print("-" * 40)
        print("maker --file [n] --text [t] --extension [py/java]")
        print("maker --import                     : Convert .java to .mkr")
        print("maker --run [file].mkr             : Auto-detect & Run")
        print("maker --list                       : Show all project files")
        print("maker --host [port]                : Start local server")
        print("maker --delete [file]              : Wipe .mkr and .inf")
        print("maker --clear                      : Reset log.txt")
        print("maker --version                    : Show version")
    
    elif "--host" in args:
        try: start_host(args[args.index("--host") + 1])
        except: print("❌ Error: Provide a port number.")

    elif "--file" in args:
        try:
            f_idx, t_idx, e_idx = args.index("--file"), args.index("--text"), args.index("--extension")
            make_file(args[f_idx+1], " ".join(args[t_idx+1:e_idx]), args[e_idx+1])
        except: print("❌ Error: Missing arguments for --file.")
            
    elif "--run" in args:
        try: smart_run(args[args.index("--run") + 1])
        except: print("❌ Error: Specify .mkr file.")

    elif "--delete" in args:
        try:
            name = args[args.index("--delete") + 1].replace(".mkr", "")
            for f in [f"{name}.mkr", f"info.{name}.inf"]:
                if os.path.exists(f): os.remove(f); print(f"🗑️  Deleted {f}")
        except: print("❌ Error: Specify file to delete.")

    elif "--clear" in args:
        with open(LOG_FILE, "w") as f: f.write(f"[{datetime.now()}] Log Reset\n")
        print("📝 Log cleared.")

if __name__ == "__main__":
    main()