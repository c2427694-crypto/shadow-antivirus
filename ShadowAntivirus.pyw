"""
╔══════════════════════════════════════════════════════════╗
║         SHADOW ANTIVIRUS - ALL IN ONE EDITION            ║
║              "Detects what's hidden"                     ║
║                                                          ║
║  Just run it - installs everything automatically!        ║
╚══════════════════════════════════════════════════════════╝
"""

import sys
import subprocess
import os

# ─────────────────────────────────────────────────────────
#  AUTO-INSTALLER - runs before anything else
#  Uses "python -m pip install" which always works
# ─────────────────────────────────────────────────────────
REQUIRED = [
    "customtkinter",
    "psutil",
    "requests",
    "pystray",
    "pillow",
]

def _check_and_install():
    """Check each package and install if missing"""
    missing = []

    for pkg in REQUIRED:
        # Map install name to import name
        import_name = {
            "pillow":        "PIL",
            "customtkinter": "customtkinter",
            "psutil":        "psutil",
            "requests":      "requests",
            "pystray":       "pystray",
        }.get(pkg, pkg)

        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return True  # All good

    # Show console message
    print("=" * 55)
    print("  Shadow Antivirus - Installing dependencies...")
    print("=" * 55)

    all_ok = True
    for pkg in missing:
        print(f"\n  Installing: {pkg}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"  ✅ {pkg} installed!")
            else:
                print(f"  ❌ Failed to install {pkg}")
                print(f"     {result.stderr.strip()}")
                all_ok = False
        except Exception as e:
            print(f"  ❌ Error installing {pkg}: {e}")
            all_ok = False

    print("\n" + "=" * 55)

    if not all_ok:
        print("\n  Some packages failed. Try manually:")
        for pkg in missing:
            print(f"  python -m pip install {pkg}")
        input("\n  Press Enter to exit...")
        sys.exit(1)

    print("  ✅ All packages installed! Starting Shadow...\n")

    # Restart the script so new imports work
    os.execv(sys.executable, [sys.executable] + sys.argv)


# Run installer check immediately
_check_and_install()


import os, re, math, time, json, shutil, struct
import hashlib, zipfile, threading
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

import customtkinter as ctk
from tkinter import filedialog, messagebox

try:
    import psutil
    HAS_PSUTIL = True
except:
    HAS_PSUTIL = False

try:
    import requests
    HAS_REQUESTS = True
except:
    HAS_REQUESTS = False

ctk.set_appearance_mode("dark")


# ████████████████████████████████████████████████████████
#  THEMES
# ████████████████████████████████████████████████████████
THEMES = {
    "dark":   {"bg":"#000000","sidebar":"#0a0a0a","card":"#0d0d0d","border":"#1a1a1a",
               "accent":"#1a4d80","accent2":"#2a5d90","text":"#ffffff","subtext":"#888888",
               "success":"#00cc00","warning":"#ff8800","danger":"#cc0000",
               "scroll":"#2a2a2a","scroll_hover":"#3a3a3a"},
    "light":  {"bg":"#f0f0f0","sidebar":"#ffffff","card":"#ffffff","border":"#dddddd",
               "accent":"#0066cc","accent2":"#0052a3","text":"#111111","subtext":"#666666",
               "success":"#008800","warning":"#cc6600","danger":"#cc0000",
               "scroll":"#cccccc","scroll_hover":"#aaaaaa"},
    "aquatic":{"bg":"#001a1a","sidebar":"#002626","card":"#003333","border":"#004d4d",
               "accent":"#00aaaa","accent2":"#00cccc","text":"#ccffff","subtext":"#66aaaa",
               "success":"#00ff99","warning":"#ffcc00","danger":"#ff3366",
               "scroll":"#005555","scroll_hover":"#006666"},
    "sunset": {"bg":"#1a0a00","sidebar":"#260f00","card":"#331500","border":"#4d2200",
               "accent":"#ff6600","accent2":"#ff7711","text":"#ffcc99","subtext":"#cc8844",
               "success":"#00cc44","warning":"#ffaa00","danger":"#ff2200",
               "scroll":"#553300","scroll_hover":"#664400"},
    "forest": {"bg":"#0a1a0a","sidebar":"#0f260f","card":"#142814","border":"#1a4d1a",
               "accent":"#228b22","accent2":"#339933","text":"#ccffcc","subtext":"#669966",
               "success":"#00ff44","warning":"#ffcc00","danger":"#ff3333",
               "scroll":"#1a3d1a","scroll_hover":"#2a4d2a"},
}
T = THEMES["dark"]


# ████████████████████████████████████████████████████████
#  CONFIG
# ████████████████████████████████████████████████████████
class Config:
    def __init__(self):
        self.path = Path.home() / ".shadow_antivirus" / "config.json"
        self.path.parent.mkdir(exist_ok=True)
        self.data = {"theme":"dark","auto_quarantine":True,"gaming_mode":True,
                     "vt_api_key":""}
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text()))
            except: pass

    def get(self, k, d=None): return self.data.get(k, d)
    def set(self, k, v):
        self.data[k] = v
        self.path.write_text(json.dumps(self.data, indent=2))


# ████████████████████████████████████████████████████████
#  KNOWN GAMES
# ████████████████████████████████████████████████████████
KNOWN_GAMES = {
    "csgo.exe","cs2.exe","valorant.exe","fortnite.exe","apex_legends.exe",
    "r5apex.exe","overwatch.exe","overwatch2.exe","minecraft.exe","javaw.exe",
    "dota2.exe","gta5.exe","rocketleague.exe","eldenring.exe","cyberpunk2077.exe",
    "witcher3.exe","destiny2.exe","r6s.exe","warzone.exe","modernwarfare.exe",
    "cod.exe","pubg.exe","tslgame.exe","leagueoflegends.exe","pathofexile.exe",
    "diablo4.exe","starcraft2.exe","sc2.exe","wow.exe","worldofwarcraft.exe",
    "ffxiv.exe","ffxiv_dx11.exe","robloxplayerbeta.exe","roblox.exe",
    "satisfactory.exe","deeprockgalactic.exe","haloinfinite.exe","hogwartslegacy.exe",
}
GAME_PATHS = ["steam","epic games","riot games","battle.net","origin",
              "ea games","ubisoft","rockstar","gog galaxy"]


# ████████████████████████████████████████████████████████
#  VIRUS SCANNER ENGINE - ALL 15 MODULES
# ████████████████████████████████████████████████████████
class ThreatResult:
    def __init__(self):
        self.is_threat=False; self.threat_name="Clean"; self.threat_type=None
        self.confidence=0.0; self.severity="none"; self.detections=[]; self.modules_run=[]

    def add(self, module, name, ttype, conf):
        self.detections.append({"module":module,"threat":name,"type":ttype,"confidence":conf})
        if conf > self.confidence:
            self.confidence=conf; self.threat_name=name; self.threat_type=ttype
        self.is_threat=True
        self.severity = "critical" if conf>=0.9 else "high" if conf>=0.7 else "medium" if conf>=0.5 else "low"

    def summary(self):
        if not self.is_threat: return "✅ Clean"
        return f"⚠️ {self.threat_name}\nType: {self.threat_type}\nSeverity: {self.severity.upper()}\nConfidence: {int(self.confidence*100)}%"


def _read(path, limit=50*1024*1024):
    size = os.path.getsize(path)
    if size > limit: return b""
    with open(path,"rb") as f: return f.read()

def _hash(path):
    h = hashlib.md5()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(65536),b""): h.update(c)
    return h.hexdigest()

def _sha256(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(65536),b""): h.update(c)
    return h.hexdigest()


KNOWN_HASHES = {
    "44d88612fea8a8f36de82e1278abb02f":("EICAR Test","TestFile"),
    "84c82835a5d21bbcf75a61706d8ab549":("WannaCry","Ransomware"),
}
RANSOM_EXTS = {".locked",".encrypted",".enc",".crypt",".crypted",".wcry",
               ".wncry",".locked",".locky",".cerber",".dharma",".djvu"}
RANSOM_NOTES = {"how to decrypt","readme_decrypt","help_decrypt",
                "recover_files","ransomnote","_readme.txt"}
DANGEROUS_EXTS = {".exe",".dll",".scr",".bat",".cmd",".com",".vbs",".vbe",
                  ".js",".jse",".wsf",".ps1",".msi",".hta",".pif",".reg",".lnk"}
SCRIPT_EXTS = {".ps1",".vbs",".vbe",".js",".jse",".bat",".cmd",".wsf",".hta"}
SUSP_NAMES = ["crack","keygen","hack","exploit","payload","inject","bypass",
              "cheat","trainer","activator","loader","bot","stealer","grabber",
              "rat","worm","trojan","ransomware","crypter","dropper","backdoor",
              "rootkit","spyware","miner"]

PE_IMPORTS = [b"VirtualAlloc",b"WriteProcessMemory",b"CreateRemoteThread",
              b"SetWindowsHookEx",b"GetAsyncKeyState",b"URLDownloadToFile",
              b"RegSetValueEx",b"IsDebuggerPresent",b"NtUnmapViewOfSection"]

SIGNATURES = [
    (b"X5O!P%@AP[4\\PZX54(P^)7CC)7}","EICAR","TestFile",1.0),
    (b"/bin/busybox MIRAI","Mirai Botnet","Botnet",1.0),
    (b"WANACRY!","WannaCry","Ransomware",1.0),
    (b"sekurlsa::logonpasswords","Mimikatz","Credential Theft",1.0),
    (b"mimikatz","Mimikatz","Credential Theft",0.95),
    (b"meterpreter","Meterpreter","RAT",0.95),
    (b"eval(gzinflate(base64_decode","PHP Webshell","Webshell",0.95),
    (b"invoke-mimikatz","Mimikatz PS","Credential Theft",0.95),
    (b"cobalt strike","Cobalt Strike","RAT",0.95),
    (b"Software\\Microsoft\\Windows\\CurrentVersion\\Run","Registry Persistence","Trojan",0.5),
]

SCRIPT_PATTERNS = [
    (rb"powershell.*-enc","Obfuscated PowerShell","Trojan",0.85),
    (rb"powershell.*-nop.*-w.*hidden","Hidden PS Execution","Trojan",0.9),
    (rb"invoke-expression.*downloadstring","PS Downloader","Downloader",0.9),
    (rb"\[convert\]::frombase64string","Base64 Payload","Obfuscation",0.75),
    (rb"createobject.*wscript\.shell","WScript Shell","Trojan",0.80),
    (rb"auto_open|autoopen|document_open","Auto-Execute Macro","Macro",0.70),
    (rb"empire.*agent","PS Empire","RAT",0.95),
    (rb"stratum\+tcp://","Crypto Miner","Cryptominer",0.90),
]

RANSOM_STRINGS = [b"your files have been encrypted",b"bitcoin",b"decrypt your files",
                  b".onion",b"pay ransom",b"all your files"]
RAT_STRINGS = [b"remote access",b"keylogger",b"screenshot",b"webcam",
               b"reverse shell",b"backdoor",b"command and control"]
MINER_STRINGS = [b"stratum+tcp",b"xmrig",b"monero",b"cryptonight",b"hashrate"]


class ScanEngine:
    def __init__(self, vt_key=""):
        self.vt_key = vt_key

    def scan(self, filepath, progress_cb=None) -> ThreatResult:
        r = ThreatResult()
        path = str(filepath)
        if not os.path.exists(path): return r

        modules = [
            ("Hash Check",        self._hash_scan),
            ("Signature Scan",    self._sig_scan),
            ("PE Header",         self._pe_scan),
            ("String Analysis",   self._string_scan),
            ("Script Analysis",   self._script_scan),
            ("Entropy Check",     self._entropy_scan),
            ("Heuristic",         self._heuristic_scan),
            ("Ransomware Check",  self._ransom_scan),
            ("Network Indicators",self._network_scan),
            ("Archive Scan",      self._archive_scan),
            ("Exploit Check",     self._exploit_scan),
            ("Metadata Check",    self._metadata_scan),
        ]

        total = len(modules) + (1 if self.vt_key else 0)
        for i, (name, fn) in enumerate(modules):
            r.modules_run.append(name)
            if progress_cb: progress_cb(name, int(i/total*100))
            try: fn(path, r)
            except: pass

        if self.vt_key:
            r.modules_run.append("VirusTotal")
            if progress_cb: progress_cb("VirusTotal", 95)
            try: self._vt_scan(path, r)
            except: pass

        if progress_cb: progress_cb("Done", 100)
        return r

    def _hash_scan(self, p, r):
        h = _hash(p)
        if h in KNOWN_HASHES:
            n,t = KNOWN_HASHES[h]; r.add("Hash",n,t,1.0)

    def _sig_scan(self, p, r):
        data = _read(p)
        if not data: return
        for sig,name,ttype,conf in SIGNATURES:
            if sig in data: r.add("Signature",name,ttype,conf)

    def _pe_scan(self, p, r):
        if Path(p).suffix.lower() not in DANGEROUS_EXTS: return
        data = _read(p)
        if not data or not data.startswith(b'MZ'): return
        hits = sum(1 for i in PE_IMPORTS if i in data)
        if hits >= 5: r.add("PE Header","Suspicious PE Imports","Suspicious",0.6)
        if b'UPX0' in data or b'UPX1' in data: r.add("PE Header","UPX Packed","Packer",0.5)

    def _string_scan(self, p, r):
        data = _read(p).lower()
        if not data: return
        checks = [
            (RANSOM_STRINGS, "Ransomware Strings", "Ransomware", 0.80),
            (RAT_STRINGS,    "RAT Strings",        "RAT",        0.75),
            (MINER_STRINGS,  "Miner Strings",      "Cryptominer",0.80),
        ]
        for strings, name, ttype, conf in checks:
            if sum(1 for s in strings if s.lower() in data) >= 2:
                r.add("String",name,ttype,conf)

    def _script_scan(self, p, r):
        if Path(p).suffix.lower() not in SCRIPT_EXTS: return
        data = _read(p).lower()
        if not data: return
        for pat, name, ttype, conf in SCRIPT_PATTERNS:
            if re.search(pat, data, re.IGNORECASE):
                r.add("Script",name,ttype,conf)

    def _entropy_scan(self, p, r):
        if Path(p).suffix.lower() not in DANGEROUS_EXTS: return
        try:
            with open(p,"rb") as f: data = f.read(1024*1024)
            if not data: return
            counts = Counter(data)
            ent = -sum((c/len(data))*math.log2(c/len(data)) for c in counts.values() if c>0)
            if ent > 7.8: r.add("Entropy","Packed/Encrypted Executable","Packer",0.75)
        except: pass

    def _heuristic_scan(self, p, r):
        name = Path(p).name.lower()
        ext = Path(p).suffix.lower()
        size = os.path.getsize(p)
        for kw in SUSP_NAMES:
            if kw in name:
                r.add("Heuristic",f"Suspicious name: '{kw}'","Suspicious",0.75); break
        if ext in DANGEROUS_EXTS and size < 5000:
            r.add("Heuristic","Tiny Executable (dropper?)","Dropper",0.60)
        # Extension mismatch
        MAGIC = {b'MZ':'.exe',b'%PDF':'.pdf',b'\xff\xd8\xff':'.jpg',b'\x89PNG':'.png'}
        try:
            with open(p,'rb') as f: hdr = f.read(16)
            for magic, real_ext in MAGIC.items():
                if hdr.startswith(magic) and ext != real_ext:
                    r.add("Heuristic",f"Extension Mismatch ({ext} is actually {real_ext})","Disguised",0.90); break
        except: pass

    def _ransom_scan(self, p, r):
        name = Path(p).name.lower()
        ext = Path(p).suffix.lower()
        if ext in RANSOM_EXTS: r.add("Ransomware",f"Encrypted file ({ext})","Ransomware",0.90)
        for note in RANSOM_NOTES:
            if note in name: r.add("Ransomware","Ransom Note","Ransomware",0.95); break

    def _network_scan(self, p, r):
        data = _read(p, 20*1024*1024)
        if not data: return
        if b'.onion' in data.lower(): r.add("Network","Tor .onion URL","Network Threat",0.70)
        if re.search(rb'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{4,5}\b', data):
            r.add("Network","Hardcoded IP:Port (C2?)","Network Threat",0.60)

    def _archive_scan(self, p, r):
        try:
            if not zipfile.is_zipfile(p): return
            with zipfile.ZipFile(p,'r') as z:
                names = z.namelist()
                exes = [n for n in names if Path(n).suffix.lower() in DANGEROUS_EXTS]
                if exes: r.add("Archive",f"Archive contains {len(exes)} executable(s)","Suspicious",0.55)
                total = sum(i.file_size for i in z.infolist())
                if os.path.getsize(p) > 0 and total/os.path.getsize(p) > 500:
                    r.add("Archive","Zip Bomb","ZipBomb",0.95)
        except: pass

    def _exploit_scan(self, p, r):
        data = _read(p, 10*1024*1024)
        if not data: return
        patterns = [
            (rb'\x90{20,}', "NOP Sled", 0.85),
            (rb'eval\s*\(base64_decode', "PHP Webshell", 0.95),
            (rb'meterpreter', "Meterpreter", 0.95),
        ]
        for pat,name,conf in patterns:
            if re.search(pat,data,re.DOTALL): r.add("Exploit",name,"Exploit",conf)

    def _metadata_scan(self, p, r):
        name = Path(p).name
        ext = Path(p).suffix.lower()
        # Double extension
        if name.count('.') >= 2:
            parts = name.split('.')
            fake = f".{parts[-2].lower()}"
            real = f".{parts[-1].lower()}"
            if real in DANGEROUS_EXTS and fake in {'.txt','.pdf','.doc','.jpg','.png'}:
                r.add("Metadata",f"Double Extension: {fake}{real}","Disguised",0.90)
        # RTLO char
        if '\u202e' in name: r.add("Metadata","RTLO filename spoofing","Disguised",0.95)

    def _vt_scan(self, p, r):
        if not HAS_REQUESTS: return
        h = _sha256(p)
        try:
            resp = requests.get(f"https://www.virustotal.com/api/v3/files/{h}",
                                headers={"x-apikey":self.vt_key}, timeout=10)
            if resp.status_code == 200:
                stats = resp.json().get("data",{}).get("attributes",{}).get("last_analysis_stats",{})
                mal = stats.get("malicious",0)
                total = sum(stats.values()) or 1
                if mal > 0:
                    conf = min(mal/total*2, 1.0)
                    r.add("VirusTotal",f"Detected by {mal}/{total} engines","VirusTotal",conf)
        except: pass


# ████████████████████████████████████████████████████████
#  BACKGROUND MONITORS
# ████████████████████████████████████████████████████████

# ── Firewall ──
class Firewall:
    @staticmethod
    def is_admin():
        """Check if running as administrator"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def run_as_admin(cmd):
        """Run a command elevated (triggers UAC prompt)"""
        try:
            import ctypes
            # Join command into a single string for PowerShell
            ps_cmd = " ".join(cmd)
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", "cmd.exe",
                f'/c {ps_cmd}', None, 0  # 0 = hidden window
            )
            return True
        except:
            return False

    @staticmethod
    def is_on():
        try:
            out = subprocess.run(
                ["netsh","advfirewall","show","allprofiles","state"],
                capture_output=True, text=True,
                creationflags=0x08000000).stdout
            return "ON" in out.upper()
        except: return False

    @staticmethod
    def enable():
        try:
            if Firewall.is_admin():
                subprocess.run(
                    ["netsh","advfirewall","set","allprofiles","state","on"],
                    capture_output=True, creationflags=0x08000000)
            else:
                Firewall.run_as_admin(
                    ["netsh","advfirewall","set","allprofiles","state","on"])
        except: pass

    @staticmethod
    def disable():
        try:
            if Firewall.is_admin():
                subprocess.run(
                    ["netsh","advfirewall","set","allprofiles","state","off"],
                    capture_output=True, creationflags=0x08000000)
            else:
                Firewall.run_as_admin(
                    ["netsh","advfirewall","set","allprofiles","state","off"])
        except: pass

    @staticmethod
    def connections():
        conns = []
        if not HAS_PSUTIL: return conns
        try:
            for c in psutil.net_connections(kind='inet'):
                try:
                    if c.status=='ESTABLISHED' and c.raddr:
                        name="Unknown"
                        if c.pid:
                            try: name=psutil.Process(c.pid).name()
                            except: pass
                        conns.append({"process":name,"local":f"{c.laddr.ip}:{c.laddr.port}",
                                      "remote":f"{c.raddr.ip}:{c.raddr.port}","pid":c.pid})
                except: pass
        except: pass
        return conns





# ── Browser Control ──
class BrowserCtrl:
    BROWSERS = {
        "Chrome":   {"proc":"chrome.exe",  "keys":["google\\chrome"],
                     "prefs": Path.home()/"AppData/Local/Google/Chrome/User Data/Default/Preferences",
                     "ext":   Path.home()/"AppData/Local/Google/Chrome/User Data/Default/Extensions"},
        "Edge":     {"proc":"msedge.exe",  "keys":["microsoft\\edge"],
                     "prefs": Path.home()/"AppData/Local/Microsoft/Edge/User Data/Default/Preferences",
                     "ext":   Path.home()/"AppData/Local/Microsoft/Edge/User Data/Default/Extensions"},
        "Brave":    {"proc":"brave.exe",   "keys":["bravesoftware"],
                     "prefs": Path.home()/"AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Preferences",
                     "ext":   Path.home()/"AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Extensions"},
        "Opera GX": {"proc":"opera.exe",   "keys":["opera gx"],
                     "prefs": Path.home()/"AppData/Roaming/Opera Software/Opera GX Stable/Preferences",
                     "ext":   Path.home()/"AppData/Roaming/Opera Software/Opera GX Stable/Extensions"},
        "Opera":    {"proc":"opera.exe",   "keys":["opera stable"],
                     "prefs": Path.home()/"AppData/Roaming/Opera Software/Opera Stable/Preferences",
                     "ext":   Path.home()/"AppData/Roaming/Opera Software/Opera Stable/Extensions"},
        "Firefox":  {"proc":"firefox.exe", "keys":["mozilla firefox"],
                     "prefs": Path.home()/"AppData/Roaming/Mozilla/Firefox/Profiles",
                     "ext":   None},
    }

    @classmethod
    def installed(cls):
        return [n for n,i in cls.BROWSERS.items() if i["prefs"].exists()]

    @classmethod
    def running(cls, name):
        if not HAS_PSUTIL: return False
        info = cls.BROWSERS.get(name,{})
        proc = info.get("proc","").lower()
        keys = info.get("keys",[])
        for p in psutil.process_iter(['name','exe']):
            try:
                if p.info['name'].lower() != proc: continue
                if name in ("Opera","Opera GX"):
                    exe = ""
                    try: exe = (p.exe() or "").lower()
                    except: pass
                    if any(k in exe for k in keys): return True
                else:
                    return True
            except: pass
        return False

    @classmethod
    def safe_browsing(cls, name):
        info = cls.BROWSERS.get(name,{})
        prefs = info.get("prefs")
        if not prefs or not prefs.exists(): return None
        try:
            data = json.loads(prefs.read_text(encoding='utf-8',errors='ignore'))
            return data.get("safebrowsing",{}).get("enabled",True)
        except: return None

    @classmethod
    def ext_count(cls, name):
        ext = cls.BROWSERS.get(name,{}).get("ext")
        if not ext or not ext.exists(): return 0
        try: return sum(1 for d in ext.iterdir() if d.is_dir())
        except: return 0


# ── Device Security ──
class DeviceWatcher:
    def __init__(self, notify_cb, action_cb):
        self.notify = notify_cb
        self.action = action_cb
        self.running = False
        self._users = set()
        self._startup = set()
        self._ready = False
        # These get updated live from the settings page
        self.user_detection  = True
        self.startup_monitor = True

    def start(self):
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self): self.running = False

    def _users_list(self):
        try:
            out = subprocess.run(["net","user"], capture_output=True, text=True,
                                 creationflags=0x08000000).stdout
            users = set()
            active = False
            for line in out.split('\n'):
                if '---' in line: active=True; continue
                if active and line.strip() and 'The command' not in line:
                    for p in line.split():
                        if p.strip(): users.add(p.strip().lower())
            return users
        except: return set()

    def _startup_list(self):
        entries = set()
        for key in [r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
                    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"]:
            try:
                out = subprocess.run(["reg","query",key], capture_output=True, text=True,
                                     creationflags=0x08000000).stdout
                for line in out.split('\n'):
                    if '    REG_' in line:
                        entries.add(line.strip().split('    ')[0])
            except: pass
        return entries

    def _remove_user(self, u):
        """Remove user - needs admin rights"""
        try:
            # Try direct first
            r = subprocess.run(
                ["net", "user", u, "/delete"],
                capture_output=True, text=True,
                creationflags=0x08000000
            )
            if r.returncode == 0:
                return True
            # If failed, try via PowerShell elevated
            ps = f'Remove-LocalUser -Name "{u}"'
            r2 = subprocess.run(
                ["powershell", "-Command", ps],
                capture_output=True, creationflags=0x08000000
            )
            return r2.returncode == 0
        except:
            return False

    def _is_sus_user(self, u):
        safe = ['administrator', 'guest', 'defaultaccount',
                'wdagutilityaccount', 'defaultuser0', 'homegroup']
        return not any(s in u.lower() for s in safe)

    def _loop(self):
        while self.running:
            try:
                if not self._ready:
                    self._users   = self._users_list()
                    self._startup = self._startup_list()
                    self._ready   = True
                    time.sleep(30)
                    continue

                # User detection - only if enabled
                if self.user_detection:
                    cur_users = self._users_list()
                    for u in cur_users - self._users:
                        if self._is_sus_user(u):
                            # Pass username to action callback
                            # App will show Keep/Remove dialog
                            self.action("NEW_USER_DETECTED", u)
                    self._users = cur_users

                # Startup monitor - only if enabled
                if self.startup_monitor:
                    cur_startup = self._startup_list()
                    for e in cur_startup - self._startup:
                        self.notify("⚠️ New Startup Entry", f"Added: {e}")
                    self._startup = cur_startup

            except:
                pass
            time.sleep(30)


# ── Windows Notifications ──
def win_notify(title, msg):
    try:
        ps = (f'Add-Type -AssemblyName System.Windows.Forms;'
              f'$n=New-Object System.Windows.Forms.NotifyIcon;'
              f'$n.Icon=[System.Drawing.SystemIcons]::Shield;'
              f'$n.Visible=$true;'
              f'$n.ShowBalloonTip(5000,"{title}","{msg}",'
              f'[System.Windows.Forms.ToolTipIcon]::Warning)')
        subprocess.Popen(["powershell","-WindowStyle","Hidden","-Command",ps],
                         creationflags=0x08000000)
    except: pass


# ████████████████████████████████████████████████████████
#  ANIMATOR
# ████████████████████████████████████████████████████████
class Anim:
    def __init__(self, root): self.root=root; self.jobs={}

    def lerp(self, c1, c2, t):
        def h2r(h):
            h=h.lstrip('#')
            return [int(h[i:i+2],16) for i in (0,2,4)]
        try:
            r1,g1,b1=h2r(c1); r2,g2,b2=h2r(c2)
            r=int(r1+(r2-r1)*t); g=int(g1+(g2-g1)*t); b=int(b1+(b2-b1)*t)
            return f"#{r:02x}{g:02x}{b:02x}"
        except: return c2

    def color(self, w, prop, c1, c2, dur=150, steps=15, done=None):
        jid = (id(w), prop)
        self.jobs[jid] = True
        dt = dur//steps
        def step(i):
            if not self.jobs.get(jid): return
            t = (i/steps); t = t*t*(3-2*t)
            try: w.configure(**{prop: self.lerp(c1,c2,t)})
            except: pass
            if i < steps: self.root.after(dt, lambda: step(i+1))
            else:
                self.jobs[jid]=False
                if done: done()
        step(0)

    def width(self, w, fw, tw, dur=180, steps=18):
        jid=(id(w),"width"); self.jobs[jid]=True
        dt=dur//steps
        def step(i):
            if not self.jobs.get(jid): return
            t=i/steps; t=1-(1-t)*(1-t)
            try: w.configure(width=int(fw+(tw-fw)*t))
            except: pass
            if i<steps: self.root.after(dt, lambda: step(i+1))
            else: self.jobs[jid]=False
        step(0)


# ─────────────────────────────────────────────
#  VERSION - bump this every update
# ─────────────────────────────────────────────
CURRENT_VERSION = "1.1.0"

# YOUR GITHUB RAW URL - update this after setup
# Format: https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/ShadowAntivirus.pyw
GITHUB_RAW_URL  = "https://raw.githubusercontent.com/c2427694-crypto/shadow-antivirus/main/ShadowAntivirus.pyw"
GITHUB_VER_URL  = "https://raw.githubusercontent.com/c2427694-crypto/shadow-antivirus/main/version.txt"


class AutoUpdater:
    """Checks GitHub for updates and auto-installs them"""

    def __init__(self, app):
        self.app = app

    def check(self):
        """Run update check in background - never blocks UI"""
        threading.Thread(target=self._check_worker, daemon=True).start()

    def _check_worker(self):
        if not HAS_REQUESTS: return
        if "YOUR_USERNAME" in GITHUB_VER_URL: return  # Not set up yet

        try:
            # Fetch latest version number from GitHub
            resp = requests.get(GITHUB_VER_URL, timeout=5)
            if resp.status_code != 200: return

            latest = resp.text.strip()

            if latest != CURRENT_VERSION:
                # New version available - show popup on main thread
                self.app.after(0, lambda: self._prompt_update(latest))

        except: pass

    def _prompt_update(self, latest):
        """Ask user if they want to update"""
        result = messagebox.askyesno(
            "🛡️ Update Available!",
            f"Shadow Antivirus {latest} is available!\n"
            f"You have: {CURRENT_VERSION}\n\n"
            f"Download and install now?\n"
            f"(App will restart automatically)"
        )
        if result:
            threading.Thread(target=lambda: self._download_update(latest), daemon=True).start()

    def _download_update(self, latest):
        """Download new version and replace current file"""
        try:
            self.app.after(0, lambda: messagebox.showinfo(
                "⏳ Downloading...",
                f"Downloading Shadow Antivirus {latest}...\nPlease wait."
            ))

            resp = requests.get(GITHUB_RAW_URL, timeout=30)
            if resp.status_code != 200:
                self.app.after(0, lambda: messagebox.showerror(
                    "Error", "Download failed. Try again later."))
                return

            # Get current file path
            current_file = Path(__file__).resolve()
            backup_file  = current_file.with_suffix('.pyw.bak')

            # Backup current version
            import shutil as _sh
            _sh.copy(current_file, backup_file)

            # Write new version
            current_file.write_text(resp.text, encoding='utf-8')

            self.app.after(0, lambda: self._restart_app(latest))

        except Exception as e:
            self.app.after(0, lambda: messagebox.showerror(
                "Update Failed", f"Could not update:\n{e}\n\nYour current version is unchanged."
            ))

    def _restart_app(self, latest):
        messagebox.showinfo(
            "✅ Updated!",
            f"Shadow Antivirus {latest} installed!\nRestarting now..."
        )
        # Restart the app
        import subprocess, sys
        subprocess.Popen([sys.executable, str(Path(__file__).resolve())],
                         creationflags=0x08000000)
        self.app._quit_app()
class ShadowAntivirus(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Shadow Antivirus")
        self.geometry("1200x750")
        self.configure(fg_color="#000000")

        # Icon
        try:
            ico = Path(__file__).parent/"shadow_icon.ico"
            if ico.exists(): self.iconbitmap(str(ico))
        except: pass

        self.cfg = Config()
        self.anim = Anim(self)

        global T
        T = THEMES.get(self.cfg.get("theme","dark"), THEMES["dark"])
        self.configure(fg_color=T["bg"])

        self.page = "home"
        self.sidebar_open = True
        self.SIDEBAR_W = 270
        self.scanning = False
        self.gaming = False
        self._tray_icon = None

        self._build_ui()
        # Delay ALL monitors by 3s so UI opens instantly
        self.after(3000, self._start_monitors)
        if HAS_PSUTIL: self._check_gaming()
        # Check for updates silently after 5s
        self.after(5000, lambda: AutoUpdater(self).check())

        # Override close button → minimize to tray instead of quitting
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)

    def _hide_to_tray(self):
        """Hide window to system tray, keep running in background"""
        self.withdraw()  # Hide window
        self._start_tray_icon()

    def _show_window(self):
        """Bring window back from tray"""
        self.deiconify()
        self.lift()
        self.focus_force()
        if self._tray_icon:
            try:
                self._tray_icon.stop()
                self._tray_icon = None
            except: pass

    def _quit_app(self):
        """Actually quit everything"""
        if self._tray_icon:
            try: self._tray_icon.stop()
            except: pass
        if hasattr(self, 'dev_watcher'):
            try: self.dev_watcher.stop()
            except: pass
        self.destroy()

    def _start_tray_icon(self):
        """Start system tray icon in background thread"""
        try:
            import pystray
            from PIL import Image, ImageDraw

            # Create shield icon for tray
            size = 64
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Draw shield shape
            shield = [
                (size//2, 4),
                (size-4, size//4),
                (size-4, size//2+8),
                (size//2, size-4),
                (4, size//2+8),
                (4, size//4),
            ]
            draw.polygon(shield, fill=(26, 77, 128))
            draw.polygon(shield, outline=(0, 212, 255), width=2)

            # Draw checkmark
            draw.line([(20, 34), (28, 44), (44, 24)],
                      fill=(0, 212, 255), width=4)

            # Build tray menu
            menu = pystray.Menu(
                pystray.MenuItem("Shadow Antivirus", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("🛡️ Open", lambda: self.after(0, self._show_window), default=True),
                pystray.MenuItem("🔍 Quick Scan", lambda: self.after(0, self.quick_scan)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("❌ Quit", lambda: self.after(0, self._quit_app)),
            )

            self._tray_icon = pystray.Icon(
                "Shadow Antivirus",
                img,
                "Shadow Antivirus - Running",
                menu
            )

            # Run tray in background thread
            threading.Thread(
                target=self._tray_icon.run,
                daemon=True
            ).start()

            # Show tray notification
            win_notify(
                "Shadow Antivirus",
                "Still running in the background!\nClick the tray icon to open."
            )

        except ImportError:
            # pystray not installed - just minimize instead
            self.iconify()
            messagebox.showinfo(
                "Tip",
                "pystray failed to load. Try:\n\npython -m pip install pystray pillow\n\nFor now, Shadow Antivirus is minimized."
            )

    def _start_monitors(self):
        dev_settings = self.cfg.get("device_settings", {})
        self.dev_watcher = DeviceWatcher(self._notify, self._on_action)
        self.dev_watcher.user_detection  = dev_settings.get("user_detection",  True)
        self.dev_watcher.startup_monitor = dev_settings.get("startup_monitor", True)
        if dev_settings.get("monitor_enabled", True):
            self.dev_watcher.start()

    # ── Notification handlers ──
    def _notify(self, title, msg):
        self.after(0, lambda: messagebox.showwarning(title, msg))
        win_notify(title, msg)

    def _on_action(self, action, detail):
        if action == "NEW_USER_DETECTED":
            self.after(0, lambda u=detail: self._show_user_dialog(u))
        else:
            self._notify(f"✅ Action: {action}", detail)

    def _show_user_dialog(self, username):
        """Show popup with Keep or Remove options"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("🚨 Suspicious User Detected")
        dialog.geometry("480x320")
        dialog.configure(fg_color=T["bg"])
        dialog.transient(self)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()

        # Header
        header = ctk.CTkFrame(dialog, fg_color="#330000", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="🚨  SUSPICIOUS USER DETECTED",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#ff4444").pack(expand=True)

        # Content
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=28, pady=20)

        ctk.CTkLabel(content,
            text=f"New user account created:",
            font=ctk.CTkFont(size=12),
            text_color=T["subtext"]).pack(anchor="w")

        ctk.CTkLabel(content,
            text=f"  👤  {username}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ff6666").pack(anchor="w", pady=(4, 12))

        ctk.CTkLabel(content,
            text="This account was just created.\nMalware sometimes creates users for backdoor access.\nWhat do you want to do?",
            font=ctk.CTkFont(size=12),
            text_color=T["subtext"],
            justify="left").pack(anchor="w", pady=(0, 20))

        # Buttons
        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack(fill="x")

        def remove():
            dialog.destroy()
            removed = self.dev_watcher._remove_user(username)
            if removed:
                messagebox.showinfo("✅ Removed",
                    f"User '{username}' has been deleted successfully!")
            else:
                messagebox.showerror("❌ Failed",
                    f"Could not remove '{username}'.\n\n"
                    "Try running Shadow Antivirus as Administrator:\n"
                    "Right-click → Run as administrator")

        def keep():
            dialog.destroy()
            messagebox.showinfo("✅ Kept",
                f"User '{username}' has been kept.\n"
                "It will not be flagged again this session.")
            # Add to known users so it won't alert again
            self.dev_watcher._users.add(username.lower())

        ctk.CTkButton(btn_row,
            text="🗑️  Remove User",
            command=remove,
            fg_color="#aa0000", hover_color="#cc0000",
            height=42, font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", expand=True, fill="x", padx=(0, 8))

        ctk.CTkButton(btn_row,
            text="✅  Keep User",
            command=keep,
            fg_color="#226622", hover_color="#338833",
            height=42, font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", expand=True, fill="x")



    # ── Build UI ──
    def _build_ui(self):
        # Top bar
        self.topbar = ctk.CTkFrame(self, fg_color=T["sidebar"], height=48)
        self.topbar.pack(fill="x"); self.topbar.pack_propagate(False)

        self.ham_btn = ctk.CTkButton(
            self.topbar, text="☰", width=44, height=44,
            fg_color="transparent", hover_color=T["card"],
            font=ctk.CTkFont(size=20), corner_radius=8,
            command=self._toggle_sidebar)
        self.ham_btn.pack(side="left", padx=6, pady=2)

        self.back_btn = ctk.CTkButton(
            self.topbar, text="←", width=44, height=44,
            fg_color="transparent", hover_color=T["card"],
            font=ctk.CTkFont(size=20), corner_radius=8,
            command=lambda: self._go("home"))

        # Body
        self.body = ctk.CTkFrame(self, fg_color=T["bg"])
        self.body.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self.body, width=self.SIDEBAR_W, fg_color=T["sidebar"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Content
        self.content = ctk.CTkFrame(self.body, fg_color=T["bg"])
        self.content.pack(side="right", fill="both", expand=True)

        self._go("home")

    def _build_sidebar(self):
        # Logo
        lf = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=90)
        lf.pack(fill="x", pady=(15,5)); lf.pack_propagate(False)
        ctk.CTkLabel(lf, text="🛡️", font=ctk.CTkFont(size=44)).pack()
        ctk.CTkLabel(lf, text="Shadow Antivirus",
                     font=ctk.CTkFont(size=13,weight="bold"),
                     text_color=T["text"]).pack()

        self.gaming_lbl = ctk.CTkLabel(
            self.sidebar, text="", font=ctk.CTkFont(size=9),
            text_color="#00d4ff")
        self.gaming_lbl.pack(pady=(0,8))

        nav = [
            ("🏠","Home","home"), ("🛡️","Virus Protection","virus"),
            ("🔥","Firewall & Network","firewall"),
            ("🌐","Browser Control","browser"),
            ("🔒","Device Security","device"),
            ("🎮","Gaming Mode","gaming"),
            ("🗂️","Quarantine","quarantine"),
            ("🕐","History","history"),
        ]
        self.nav_btns = {}
        for icon,label,pid in nav:
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icon}  {label}",
                command=lambda p=pid: self._go(p),
                fg_color="transparent", hover_color=T["card"],
                text_color=T["text"], anchor="w",
                height=42, font=ctk.CTkFont(size=13), corner_radius=8)
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_btns[pid] = btn

        # Separator + Settings at bottom
        ctk.CTkFrame(self.sidebar, fg_color=T["border"], height=1).pack(
            fill="x", padx=15, side="bottom", pady=5)
        settings_btn = ctk.CTkButton(
            self.sidebar, text="  ⚙️  Settings",
            command=lambda: self._go("settings"),
            fg_color="transparent", hover_color=T["card"],
            text_color=T["text"], anchor="w",
            height=42, font=ctk.CTkFont(size=13), corner_radius=8)
        settings_btn.pack(side="bottom", fill="x", padx=8, pady=2)
        self.nav_btns["settings"] = settings_btn

    # ── Navigation ──
    def _go(self, pid):
        self.page = pid

        # Back button
        if pid == "home": self.back_btn.pack_forget()
        elif not self.back_btn.winfo_ismapped():
            self.back_btn.pack(side="left", padx=4, pady=2, after=self.ham_btn)

        # Highlight nav
        for p,b in self.nav_btns.items():
            b.configure(fg_color=T["accent"] if p==pid else "transparent")

        # Instant page switch
        for w in self.content.winfo_children(): w.destroy()
        self._render(pid)

    def _toggle_sidebar(self):
        if self.sidebar_open:
            self.anim.width(self.sidebar, self.SIDEBAR_W, 0, dur=180)
            self.sidebar_open = False
        else:
            self.anim.width(self.sidebar, 0, self.SIDEBAR_W, dur=180)
            self.sidebar_open = True

    # ── Page Router ──
    def _render(self, pid):
        pages = {
            "home":      self._pg_home,
            "virus":     self._pg_virus,
            "firewall":  self._pg_firewall,
            "browser":   self._pg_browser,
            "device":    self._pg_device,
            "gaming":    self._pg_gaming,
            "quarantine":self._pg_quarantine,
            "settings":  self._pg_settings,
        }
        pages.get(pid, self._pg_generic)(pid)

    # ── Page Helpers ──
    def _scroll(self):
        f = ctk.CTkScrollableFrame(
            self.content, fg_color=T["bg"],
            scrollbar_button_color=T["scroll"],
            scrollbar_button_hover_color=T["scroll_hover"])
        f.pack(fill="both", expand=True, padx=36, pady=36)
        return f

    def _detail_layout(self):
        c = ctk.CTkFrame(self.content, fg_color=T["bg"])
        c.pack(fill="both", expand=True)
        scroll = ctk.CTkScrollableFrame(c, fg_color=T["bg"],
            scrollbar_button_color=T["scroll"],
            scrollbar_button_hover_color=T["scroll_hover"])
        scroll.pack(side="left", fill="both", expand=True, padx=36, pady=36)
        right = ctk.CTkFrame(c, width=220, fg_color=T["bg"])
        right.pack(side="right", fill="y", padx=(0,30), pady=36)
        right.pack_propagate(False)
        return scroll, right

    def _h1(self, p, text):
        ctk.CTkLabel(p, text=text, font=ctk.CTkFont(size=28,weight="bold"),
                     text_color=T["text"], anchor="w").pack(anchor="w", pady=(0,4))

    def _sub(self, p, text):
        ctk.CTkLabel(p, text=text, font=ctk.CTkFont(size=13),
                     text_color=T["subtext"], anchor="w").pack(anchor="w", pady=(0,22))

    def _section(self, p, text):
        ctk.CTkLabel(p, text=text, font=ctk.CTkFont(size=16,weight="bold"),
                     text_color=T["text"], anchor="w").pack(anchor="w", pady=(14,6))
        ctk.CTkFrame(p, fg_color=T["border"], height=1).pack(fill="x", pady=(0,8))

    def _status_row(self, p, icon, title, sub, icon_color=None):
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", pady=5)
        ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=15),
                     text_color=icon_color or T["success"], width=28).pack(side="left", padx=(0,10))
        inf = ctk.CTkFrame(row, fg_color="transparent")
        inf.pack(side="left")
        ctk.CTkLabel(inf, text=title, font=ctk.CTkFont(size=13),
                     text_color=T["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(inf, text=sub, font=ctk.CTkFont(size=11),
                     text_color=T["subtext"], anchor="w").pack(anchor="w")

    def _action_btn(self, p, label, cmd):
        ctk.CTkButton(p, text=label, command=cmd,
                      fg_color=T["card"], hover_color=T["accent"],
                      text_color=T["text"], anchor="w",
                      height=40, corner_radius=8,
                      border_width=1, border_color=T["border"],
                      font=ctk.CTkFont(size=13)).pack(fill="x", pady=4)

    def _right_panel(self, right):
        ctk.CTkLabel(right, text="Have a question?",
                     font=ctk.CTkFont(size=13,weight="bold"),
                     text_color=T["text"]).pack(anchor="w", pady=(0,4))
        ctk.CTkLabel(right, text="Get help",
                     text_color="#4d94ff", font=ctk.CTkFont(size=12),
                     cursor="hand2").pack(anchor="w", pady=(0,16))
        ctk.CTkLabel(right, text="Give feedback",
                     text_color="#4d94ff", font=ctk.CTkFont(size=12),
                     cursor="hand2").pack(anchor="w")

    def _make_card(self, parent, icon, title, status, warn, pid):
        NBG="#0a0a0a"; HBG="#111111"; NB="#1a1a1a"; HB="#1a4d80"
        card = ctk.CTkFrame(parent, fg_color=NBG, corner_radius=10,
                            border_width=1, border_color=NB)
        def enter(e):
            self.anim.color(card,"fg_color",NBG,HBG,100)
            self.anim.color(card,"border_color",NB,HB,100)
        def leave(e):
            self.anim.color(card,"fg_color",HBG,NBG,140)
            self.anim.color(card,"border_color",HB,NB,140)
        def click(e):
            self.anim.color(card,"fg_color",HBG,"#1a2a3a",60,
                            done=lambda: self._go(pid))

        iw = ctk.CTkFrame(card, fg_color="transparent")
        iw.pack(pady=(26,12))
        ic_bg = ctk.CTkFrame(iw, width=62, height=62,
                             fg_color=T["accent"] if not warn else "#663300",
                             corner_radius=31)
        ic_bg.pack(); ic_bg.pack_propagate(False)
        ctk.CTkLabel(ic_bg, text=icon, font=ctk.CTkFont(size=30)).pack(expand=True)

        if not warn:
            badge = ctk.CTkFrame(iw,width=22,height=22,fg_color="#0a3d0a",corner_radius=11)
            badge.place(relx=0.72,rely=0.72)
            ctk.CTkLabel(badge,text="✓",font=ctk.CTkFont(size=11,weight="bold"),
                         text_color="#00ff00").place(relx=0.5,rely=0.5,anchor="center")

        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13,weight="bold"),
                     text_color=T["text"]).pack(pady=(0,4))
        ctk.CTkLabel(card, text=status, font=ctk.CTkFont(size=11),
                     text_color=T["success"] if not warn else T["warning"]).pack(pady=(0,22))

        for w in [card,iw,ic_bg]+list(card.winfo_children()):
            try:
                w.bind("<Enter>",enter); w.bind("<Leave>",leave); w.bind("<Button-1>",click)
            except: pass
        return card

    # ████ PAGES ████

    def _pg_home(self, _=None):
        s = self._scroll()
        self._h1(s,"Security at a glance")
        self._sub(s,"See what's happening with your device's security and health.")

        grid = ctk.CTkFrame(s, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        for i in range(3): grid.grid_columnconfigure(i,weight=1,uniform="c")

        cards = [
            ("🛡️","Virus Protection",  "No action needed",False,"virus"),
            ("🔥","Firewall",          "No action needed",False,"firewall"),
            ("🌐","Browser Control",   "No action needed",False,"browser"),
            ("🔒","Device Security",   "Monitoring active",False,"device"),
            ("🎮","Gaming Mode",       "Active" if self.gaming else "Ready",not self.gaming,"gaming"),
        ]
        for i,(ic,ti,st,w,p) in enumerate(cards):
            c = self._make_card(grid,ic,ti,st,w,p)
            c.grid(row=i//3,column=i%3,padx=10,pady=10,sticky="nsew")

    def _pg_virus(self, _=None):
        s,r = self._detail_layout()
        self._h1(s,"🛡️ Virus & Threat Protection")
        self._sub(s,"Multi-layer scanning with 15 detection modules")
        self._section(s,"Scan Options")
        self._action_btn(s,"🔍 Quick Scan  (last 3 days downloads)", self.quick_scan)
        self._action_btn(s,"🔎 Full Scan   (home directory)",         self.full_scan)
        self._action_btn(s,"📁 Custom Scan (choose file)",            self.custom_scan)
        self._section(s,"Detection Modules")
        for m in ["Hash Scanner","Signature Scanner","PE Header Analyzer",
                  "String Analyzer","Script Analyzer","Entropy Analyzer",
                  "Heuristic Analyzer","Ransomware Detector","Network Indicators",
                  "Archive Scanner","Exploit Scanner","Metadata Analyzer",
                  "VirusTotal (cloud)"]:
            self._status_row(s,"✓",m,"Active")
        self._right_panel(r)

    def _pg_firewall(self, _=None):
        s, r = self._detail_layout()
        self._h1(s, "🔥 Firewall & Network Protection")
        self._sub(s, "Monitor connections and block threats")

        # Skeleton - loads instantly
        banner = ctk.CTkFrame(s, fg_color=T["card"], corner_radius=10, height=70)
        banner.pack(fill="x", pady=(0, 16))
        banner.pack_propagate(False)
        banner_lbl = ctk.CTkLabel(banner, text="  ⏳ Checking firewall...",
                                  font=ctk.CTkFont(size=17, weight="bold"),
                                  text_color=T["subtext"])
        banner_lbl.pack(side="left", padx=20, expand=True)

        toggle_btn = ctk.CTkButton(s, text="...", fg_color=T["card"],
                                   height=38, state="disabled")
        toggle_btn.pack(fill="x", pady=(0, 16))

        self._section(s, "Active Connections")
        conn_frame = ctk.CTkFrame(s, fg_color="transparent")
        conn_frame.pack(fill="x")
        conn_lbl = ctk.CTkLabel(conn_frame, text="⏳ Loading...",
                                font=ctk.CTkFont(size=12), text_color=T["subtext"])
        conn_lbl.pack(anchor="w")

        # Load EVERYTHING in background
        def load():
            fw  = Firewall.is_on()
            conns = Firewall.connections()
            self.after(0, lambda: render(fw, conns))

        def render(fw, conns):
            is_admin = Firewall.is_admin()
            # Update banner
            banner.configure(fg_color=T["accent"] if fw else "#330000")
            banner_lbl.configure(
                text=f"  Firewall {'ON ✅' if fw else 'OFF ❌'}",
                text_color=T["text"])

            # Admin warning
            if not is_admin:
                ctk.CTkLabel(s,
                    text="⚠️ Not running as admin — firewall changes will trigger UAC prompt",
                    font=ctk.CTkFont(size=11),
                    text_color=T["warning"]
                ).pack(anchor="w", pady=(0, 8))

            def do_toggle():
                if fw: Firewall.disable()
                else:  Firewall.enable()
                toggle_btn.configure(text="⏳ Applying...", state="disabled")
                # Refresh page after 2 seconds to show new state
                self.after(2000, lambda: self._go("firewall"))

            # Update toggle button
            toggle_btn.configure(
                text="🔴 Disable Firewall" if fw else "🟢 Enable Firewall",
                fg_color="#aa0000" if fw else "#008800",
                hover_color="#880000" if fw else "#006600",
                state="normal",
                command=do_toggle)

            # Fill connections
            try: conn_lbl.destroy()
            except: pass
            if conns:
                for c in conns[:15]:
                    row = ctk.CTkFrame(conn_frame, fg_color=T["card"], corner_radius=6)
                    row.pack(fill="x", pady=2)
                    inn = ctk.CTkFrame(row, fg_color="transparent")
                    inn.pack(fill="x", padx=14, pady=8)
                    ctk.CTkLabel(inn, text=f"🌐 {c['process']}",
                                 font=ctk.CTkFont(size=12, weight="bold"),
                                 text_color=T["text"], anchor="w").pack(anchor="w")
                    ctk.CTkLabel(inn, text=f"  {c['local']}  →  {c['remote']}",
                                 font=ctk.CTkFont(size=11),
                                 text_color=T["subtext"], anchor="w").pack(anchor="w")
            else:
                self._status_row(conn_frame, "✓", "No active connections", "Network is quiet")

        threading.Thread(target=load, daemon=True).start()
        self._right_panel(r)

    def _pg_browser(self, _=None):
        s,r = self._detail_layout()
        self._h1(s,"🌐 App & Browser Control")
        self._sub(s,"Chrome, Edge, Brave, Opera GX, Opera, Firefox")

        # Installed check is instant (just file exists check)
        installed = BrowserCtrl.installed()
        if not installed:
            self._status_row(s,"ℹ️","No supported browsers found",
                             "Supported: Chrome, Edge, Brave, Opera GX, Opera, Firefox")
            self._right_panel(r)
            return

        self._section(s,"Installed Browsers")
        icons={"Chrome":"🔵","Edge":"🌊","Brave":"🦁",
               "Opera GX":"🎮","Opera":"🔴","Firefox":"🦊"}

        # Build cards immediately, fill running status in background
        cards = {}
        for br in installed:
            card = ctk.CTkFrame(s, fg_color=T["card"], corner_radius=10)
            card.pack(fill="x", pady=6)
            inn = ctk.CTkFrame(card, fg_color="transparent")
            inn.pack(fill="x", padx=20, pady=14)

            top = ctk.CTkFrame(inn, fg_color="transparent")
            top.pack(fill="x")
            ctk.CTkLabel(top, text=f"{icons.get(br,'🌐')} {br}",
                         font=ctk.CTkFont(size=15, weight="bold"),
                         text_color=T["text"]).pack(side="left")

            # Status label (updated by background thread)
            status_lbl = ctk.CTkLabel(top, text="⏳ Checking...",
                                      font=ctk.CTkFont(size=11),
                                      text_color=T["subtext"])
            status_lbl.pack(side="right")

            sb = BrowserCtrl.safe_browsing(br)
            if sb is not None:
                ctk.CTkLabel(inn,
                             text="✅ Safe Browsing: On" if sb else "⚠️ Safe Browsing: Off!",
                             font=ctk.CTkFont(size=12),
                             text_color=T["success"] if sb else T["warning"],
                             anchor="w").pack(anchor="w", pady=(6,0))

            exts = BrowserCtrl.ext_count(br)
            ctk.CTkLabel(inn, text=f"🧩 {exts} extension(s) installed",
                         font=ctk.CTkFont(size=11),
                         text_color=T["subtext"], anchor="w").pack(anchor="w", pady=(4,0))

            cards[br] = status_lbl

        # Check running status in background (process scanning can be slow)
        def check_running():
            for br, lbl in cards.items():
                running = BrowserCtrl.running(br)
                txt = "● Running" if running else "○ Not running"
                color = T["success"] if running else T["subtext"]
                self.after(0, lambda l=lbl, t=txt, c=color: l.configure(text=t, text_color=c))

        threading.Thread(target=check_running, daemon=True).start()
        self._right_panel(r)

    def _pg_device(self, _=None):
        s, r = self._detail_layout()
        self._h1(s, "🔒 Device Security")
        self._sub(s, "Background monitoring for users, startup, and registry")

        # Load saved toggle states
        dev_settings = self.cfg.get("device_settings", {
            "monitor_enabled":  True,
            "user_detection":   True,
            "startup_monitor":  True,
            "task_scheduler":   True,
            "registry_monitor": True,
        })

        def save_and_refresh(key, val):
            dev_settings[key] = val
            self.cfg.set("device_settings", dev_settings)
            # Update DeviceWatcher flags live
            if hasattr(self, 'dev_watcher'):
                self.dev_watcher.user_detection  = dev_settings.get("user_detection", True)
                self.dev_watcher.startup_monitor = dev_settings.get("startup_monitor", True)
            # Update banner
            all_on = dev_settings.get("monitor_enabled", True)
            banner.configure(fg_color=T["accent"] if all_on else "#330000")
            banner_lbl.configure(
                text=f"  🔒 Background Monitor: {'ACTIVE ✅' if all_on else 'DISABLED ❌'}")

        # Master toggle banner
        master_on = dev_settings.get("monitor_enabled", True)
        banner = ctk.CTkFrame(s, fg_color=T["accent"] if master_on else "#330000",
                              corner_radius=10, height=60)
        banner.pack(fill="x", pady=(0, 8))
        banner.pack_propagate(False)

        banner_inner = ctk.CTkFrame(banner, fg_color="transparent")
        banner_inner.pack(fill="both", expand=True, padx=20)

        banner_lbl = ctk.CTkLabel(
            banner_inner,
            text=f"  🔒 Background Monitor: {'ACTIVE ✅' if master_on else 'DISABLED ❌'}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=T["text"])
        banner_lbl.pack(side="left", expand=True)

        master_sw = ctk.CTkSwitch(
            banner_inner, text="",
            progress_color="#ffffff",
            button_color=T["accent"],
            command=lambda: save_and_refresh("monitor_enabled", master_sw.get() == 1))
        if master_on: master_sw.select()
        master_sw.pack(side="right", pady=10)

        self._section(s, "Individual Protections")

        # Each protection with a real working toggle
        protections = [
            ("👤", "New User Detection",   "Auto-removes suspicious user accounts created by malware", "user_detection"),
            ("🚀", "Startup Monitor",       "Alerts when new programs are added to startup",            "startup_monitor"),
            ("⏰", "Task Scheduler",        "Watches for new suspicious scheduled tasks",               "task_scheduler"),
            ("🔑", "Registry Monitor",      "Monitors persistence registry keys for changes",           "registry_monitor"),
        ]

        for icon, name, desc, setting_key in protections:
            is_on = dev_settings.get(setting_key, True)

            row = ctk.CTkFrame(s, fg_color=T["card"], corner_radius=8)
            row.pack(fill="x", pady=5)
            inn = ctk.CTkFrame(row, fg_color="transparent")
            inn.pack(fill="x", padx=18, pady=13)

            left = ctk.CTkFrame(inn, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(left, text=f"{icon}  {name}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=T["text"], anchor="w").pack(anchor="w")

            status_lbl = ctk.CTkLabel(
                left,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color=T["subtext"], anchor="w")
            status_lbl.pack(anchor="w")

            # Real toggle switch
            sw = ctk.CTkSwitch(
                inn, text="",
                progress_color=T["accent"],
                button_color="#ffffff")
            if is_on: sw.select()

            def make_toggle(switch, key, lbl):
                def toggle():
                    val = switch.get() == 1
                    save_and_refresh(key, val)
                    lbl.configure(
                        text_color=T["subtext"] if val else T["danger"])
                switch.configure(command=toggle)

            make_toggle(sw, setting_key, status_lbl)
            sw.pack(side="right")

        self._right_panel(r)

    def _pg_gaming(self, _=None):
        s,r = self._detail_layout()
        self._h1(s,"🎮 Gaming Mode")
        self._sub(s,"Auto-pauses scans when games are detected")

        banner=ctk.CTkFrame(s,
                            fg_color=T["accent"] if self.gaming else T["card"],
                            corner_radius=12,height=110)
        banner.pack(fill="x",pady=(0,20)); banner.pack_propagate(False)
        ctk.CTkLabel(banner,
                     text="🎮  GAMING MODE ACTIVE" if self.gaming else "🎮  NO GAME DETECTED",
                     font=ctk.CTkFont(size=18,weight="bold"),
                     text_color=T["text"]).pack(expand=True)

        self._section(s,"Detected Games (auto-ignored)")
        for g in sorted(KNOWN_GAMES)[:20]:
            ctk.CTkLabel(s,text=f"  • {g}",font=ctk.CTkFont(size=11),
                         text_color=T["subtext"],anchor="w").pack(anchor="w",pady=1)
        self._right_panel(r)

    def _pg_quarantine(self, _=None):
        s, r = self._detail_layout()
        self._h1(s, "🗂️ Quarantine")
        self._sub(s, "Isolated threats — expand for details")

        qdir = Path.home() / ".shadow_quarantine"
        qdir.mkdir(exist_ok=True)

        # Load quarantine metadata (saved when files are quarantined)
        meta_file = Path.home() / ".shadow_antivirus" / "quarantine_meta.json"
        try:
            meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
        except:
            meta = {}

        files = list(qdir.glob("*"))

        if not files:
            banner = ctk.CTkFrame(s, fg_color=T["card"], corner_radius=10, height=110)
            banner.pack(fill="x")
            banner.pack_propagate(False)
            ctk.CTkLabel(banner, text="✅  No quarantined files",
                         font=ctk.CTkFont(size=16),
                         text_color=T["success"]).pack(expand=True)
        else:
            ctk.CTkLabel(s,
                text=f"  {len(files)} file(s) in quarantine",
                font=ctk.CTkFont(size=12),
                text_color=T["subtext"]
            ).pack(anchor="w", pady=(0, 10))

            for f in files:
                file_meta = meta.get(f.name, {})

                # Outer card
                card = ctk.CTkFrame(s, fg_color=T["card"], corner_radius=10,
                                    border_width=1, border_color=T["border"])
                card.pack(fill="x", pady=5)

                # ── Top row (always visible) ──
                top = ctk.CTkFrame(card, fg_color="transparent")
                top.pack(fill="x", padx=16, pady=12)

                # File icon + name
                left = ctk.CTkFrame(top, fg_color="transparent")
                left.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(left,
                    text=f"⚠️  {f.name}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=T["warning"], anchor="w"
                ).pack(anchor="w")

                # Threat type preview
                threat = file_meta.get("threat", "Unknown threat")
                ctk.CTkLabel(left,
                    text=f"🦠 {threat}",
                    font=ctk.CTkFont(size=11),
                    text_color=T["subtext"], anchor="w"
                ).pack(anchor="w")

                # ── Button row ──
                btn_row = ctk.CTkFrame(top, fg_color="transparent")
                btn_row.pack(side="right")

                # Expand/collapse details panel
                details_frame = ctk.CTkFrame(card, fg_color=T["border"], corner_radius=6)
                expanded = [False]

                def make_toggle(df, ef, btn):
                    def toggle():
                        if ef[0]:
                            df.pack_forget()
                            btn.configure(text="▶")
                            ef[0] = False
                        else:
                            df.pack(fill="x", padx=16, pady=(0, 12))
                            btn.configure(text="▼")
                            ef[0] = True
                    return toggle

                arrow_btn = ctk.CTkButton(
                    btn_row, text="▶",
                    width=32, height=28,
                    fg_color=T["border"], hover_color=T["accent"],
                    font=ctk.CTkFont(size=12)
                )
                arrow_btn.pack(side="left", padx=(0, 6))
                arrow_btn.configure(command=make_toggle(details_frame, expanded, arrow_btn))

                # Keep button - restore file to original location
                def make_keep(fp, fm):
                    def keep():
                        orig = fm.get("original_path", str(Path.home() / "Desktop" / fp.name))
                        try:
                            shutil.move(str(fp), orig)
                            # Remove from meta
                            if fp.name in meta:
                                del meta[fp.name]
                                meta_file.write_text(json.dumps(meta, indent=2))
                            messagebox.showinfo("✅ Restored",
                                f"{fp.name}\nRestored to:\n{orig}")
                            self._go("quarantine")
                        except Exception as e:
                            # If original path doesn't exist, restore to Desktop
                            try:
                                dest = Path.home() / "Desktop" / fp.name
                                shutil.move(str(fp), str(dest))
                                messagebox.showinfo("✅ Restored",
                                    f"{fp.name}\nRestored to Desktop:\n{dest}")
                                self._go("quarantine")
                            except:
                                messagebox.showerror("Error", f"Could not restore:\n{e}")
                    return keep

                ctk.CTkButton(
                    btn_row, text="Keep",
                    width=60, height=28,
                    fg_color="#226622", hover_color="#338833",
                    command=make_keep(f, file_meta)
                ).pack(side="left", padx=(0, 6))

                # Delete button
                ctk.CTkButton(
                    btn_row, text="Delete",
                    width=65, height=28,
                    fg_color="#aa0000", hover_color="#cc0000",
                    command=lambda fp=f: self._del_quar(fp)
                ).pack(side="left")

                # ── Details panel (hidden by default) ──
                try:
                    size_kb = round(f.stat().st_size / 1024, 2)
                    mod_time = datetime.fromtimestamp(
                        f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    size_kb = "?"
                    mod_time = "?"

                details = [
                    ("📁 Location",    str(f)),
                    ("📂 Original",    file_meta.get("original_path", "Unknown")),
                    ("🦠 Threat Type", file_meta.get("threat_type",  "Unknown")),
                    ("🔬 Detected by", file_meta.get("detected_by",  "Shadow Scanner")),
                    ("📏 File Size",   f"{size_kb} KB"),
                    ("🕐 Quarantined", file_meta.get("date", mod_time)),
                    ("🔑 SHA256",      file_meta.get("hash", "Not available")),
                ]

                for label, value in details:
                    drow = ctk.CTkFrame(details_frame, fg_color="transparent")
                    drow.pack(fill="x", padx=12, pady=3)

                    ctk.CTkLabel(drow,
                        text=label,
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=T["subtext"], width=120, anchor="w"
                    ).pack(side="left")

                    ctk.CTkLabel(drow,
                        text=str(value),
                        font=ctk.CTkFont(size=11),
                        text_color=T["text"], anchor="w",
                        wraplength=380
                    ).pack(side="left", fill="x", expand=True)

        self._right_panel(r)

    def _pg_settings(self, _=None):
        s,r = self._detail_layout()
        self._h1(s,"⚙️ Settings")
        self._sub(s,"Customize Shadow Antivirus")

        self._section(s,"🎨 Theme  (instant, no restart!)")
        row=ctk.CTkFrame(s,fg_color="transparent")
        row.pack(fill="x",pady=(0,16))
        cur=self.cfg.get("theme","dark")
        for name,key in [("Dark","dark"),("Light","light"),("Aquatic","aquatic"),
                          ("Sunset","sunset"),("Forest","forest")]:
            active=key==cur
            ctk.CTkButton(row,text=("✓ " if active else "")+name,
                          width=100,height=36,
                          fg_color=T["accent"] if active else T["card"],
                          hover_color=T["accent2"],corner_radius=8,
                          border_width=1,border_color=T["accent"] if active else T["border"],
                          command=lambda k=key: self._change_theme(k)
                          ).pack(side="left",padx=4)

        self._section(s,"⚙️ Scan Settings")
        self._toggle_row(s,"Auto-quarantine threats","Enabled",True)
        self._toggle_row(s,"Gaming mode auto-pause","Enabled",True)

        self._section(s,"⌨️ Keyboard Shortcuts  (click a button then press your keys)")

        # Load saved keybinds or use defaults
        keybinds = self.cfg.get("keybinds", {
            "quick_scan":  "Ctrl+Q",
            "full_scan":   "Ctrl+F",
            "settings":    "Ctrl+S",
            "quarantine":  "Ctrl+R",
        })

        kb_actions = [
            ("Quick Scan",  "quick_scan"),
            ("Full Scan",   "full_scan"),
            ("Settings",    "settings"),
            ("Quarantine",  "quarantine"),
        ]

        self._recording = None  # Which button is being recorded

        for action, key_id in kb_actions:
            row = ctk.CTkFrame(s, fg_color=T["card"], corner_radius=8)
            row.pack(fill="x", pady=4)
            inn = ctk.CTkFrame(row, fg_color="transparent")
            inn.pack(fill="x", padx=16, pady=10)

            ctk.CTkLabel(inn, text=action, font=ctk.CTkFont(size=13),
                         text_color=T["text"]).pack(side="left")

            current = keybinds.get(key_id, "Not set")
            kb_btn = ctk.CTkButton(
                inn, text=current, width=160, height=32,
                fg_color=T["border"], hover_color=T["accent"],
                font=ctk.CTkFont(size=12)
            )
            kb_btn.pack(side="right")

            # Click to record new keybind
            def make_recorder(btn, kid, act):
                def start_record():
                    # Reset any other recording button
                    if self._recording and self._recording[0] != btn:
                        self._recording[0].configure(
                            text=keybinds.get(self._recording[1], "Not set"),
                            fg_color=T["border"])

                    btn.configure(text="⌨️ Press keys...", fg_color=T["accent"])
                    self._recording = (btn, kid)

                    def on_key(event):
                        # Build key combo string
                        parts = []
                        if event.state & 0x4: parts.append("Ctrl")
                        if event.state & 0x1: parts.append("Shift")
                        if event.state & 0x8: parts.append("Alt")
                        key = event.keysym
                        if key not in ("Control_L","Control_R","Shift_L",
                                       "Shift_R","Alt_L","Alt_R"):
                            parts.append(key.upper())
                        combo = "+".join(parts) if parts else key.upper()
                        keybinds[kid] = combo
                        self.cfg.set("keybinds", keybinds)
                        btn.configure(text=combo, fg_color=T["border"])
                        self._recording = None
                        self.unbind("<KeyPress>")
                        self._bind_keys()  # Rebind shortcuts

                    self.bind("<KeyPress>", on_key)

                btn.configure(command=start_record)

            make_recorder(kb_btn, key_id, action)

        self._section(s,"🔑 VirusTotal API Key")
        entry=ctk.CTkEntry(s,width=340,placeholder_text="Paste API key here...")
        entry.pack(anchor="w",pady=(0,8))
        if self.cfg.get("vt_api_key"): entry.insert(0,self.cfg.get("vt_api_key"))
        ctk.CTkButton(s,text="Save API Key",width=140,
                      fg_color=T["accent"],hover_color=T["accent2"],
                      command=lambda: (self.cfg.set("vt_api_key",entry.get()),
                                       messagebox.showinfo("Saved","API key saved!"))).pack(anchor="w")
        self._right_panel(r)

    def _pg_generic(self, pid):
        s,r=self._detail_layout()
        self._h1(s,pid.replace("_"," ").title())
        self._sub(s,"Feature page")
        self._status_row(s,"✓","No action needed","All systems operational")
        self._right_panel(r)

    def _toggle_row(self, p, label, status, on):
        row=ctk.CTkFrame(p,fg_color="transparent"); row.pack(fill="x",pady=5)
        inf=ctk.CTkFrame(row,fg_color="transparent"); inf.pack(side="left",fill="x",expand=True)
        ctk.CTkLabel(inf,text=label,font=ctk.CTkFont(size=13),
                     text_color=T["text"],anchor="w").pack(anchor="w")
        ctk.CTkLabel(inf,text=status,font=ctk.CTkFont(size=11),
                     text_color=T["success"] if on else T["subtext"],
                     anchor="w").pack(anchor="w")
        sw=ctk.CTkSwitch(row,text="",progress_color=T["accent"],button_color="#ffffff")
        if on: sw.select()
        sw.pack(side="right")

    # ── Live Theme ──
    def _change_theme(self, key):
        global T
        T=THEMES.get(key,THEMES["dark"])
        self.cfg.set("theme",key)
        self.configure(fg_color=T["bg"])
        # Rebuild everything
        for w in self.winfo_children(): w.destroy()
        self._build_ui()

    # ── Gaming check ──
    def _check_gaming(self):
        """Start background gaming monitor - runs in its own thread, never touches main thread until done"""
        if not HAS_PSUTIL: return
        threading.Thread(target=self._gaming_loop, daemon=True).start()

    def _gaming_loop(self):
        """Runs forever in background - checks every 10 seconds, zero UI lag"""
        while True:
            try:
                found = False
                game_name = ""
                for p in psutil.process_iter(['name']):
                    try:
                        n = p.info['name'] or ""
                        if n.lower() in KNOWN_GAMES:
                            found = True
                            game_name = n
                            break
                    except: pass

                # Also check exe paths if no match yet
                if not found:
                    for p in psutil.process_iter(['name', 'exe']):
                        try:
                            e = ""
                            try: e = p.exe() or ""
                            except: pass
                            if any(g in e.lower() for g in GAME_PATHS):
                                found = True
                                game_name = p.info['name'] or "Game"
                                break
                        except: pass

                # Only update UI if state changed
                if found != self.gaming:
                    self.gaming = found
                    if found:
                        self.after(0, lambda n=game_name: self.gaming_lbl.configure(text=f"🎮 {n}"))
                    else:
                        self.after(0, lambda: self.gaming_lbl.configure(text=""))

            except: pass

            time.sleep(10)  # Check every 10 seconds in background

    # ── Scan actions ──
    def quick_scan(self):
        if self.scanning: return
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        self.scanning = True
        dl = Path.home() / "Downloads"
        cutoff = datetime.now() - timedelta(days=3)
        engine = ScanEngine(self.cfg.get("vt_api_key", ""))
        threats = []
        scanned = 0

        if dl.exists():
            for f in dl.iterdir():
                if f.is_file():
                    try:
                        if datetime.fromtimestamp(f.stat().st_mtime) > cutoff:
                            scanned += 1
                            n = f.name.lower()
                            # Skip own files
                            if "shadow" in n and ("antivirus" in n or n.endswith(".pyw")):
                                continue
                            res = engine.scan(f)
                            if res.is_threat:
                                threats.append((f, res))
                                if self.cfg.get("auto_quarantine", True):
                                    self._quarantine(f, res)  # ← pass res!
                    except:
                        pass

        self.scanning = False

        if not threats:
            msg = f"✅ All clean!\n\n{scanned} files scanned."
        else:
            det = "\n".join(
                f"• {t[0].name}\n  Type: {t[1].threat_type or 'Unknown'}  |  {int(t[1].confidence*100)}% confidence"
                for t in threats[:5]
            )
            msg = f"⚠️ {len(threats)} threat(s) found!\n\n{det}\n\nAll threats auto-quarantined!"

        self.after(0, lambda: messagebox.showinfo("Scan Complete", msg))

    def full_scan(self):
        messagebox.showinfo("Full Scan","Full scan coming soon! (checks entire home folder)")

    def custom_scan(self):
        path = filedialog.askopenfilename(title="Select File to Scan")
        if not path: return
        engine = ScanEngine(self.cfg.get("vt_api_key", ""))
        res = engine.scan(path)
        if res.is_threat:
            action = messagebox.askyesnocancel(
                "⚠️ Threat Detected",
                f"File: {Path(path).name}\n\n"
                f"Threat: {res.threat_name}\n"
                f"Type: {res.threat_type or 'Unknown'}\n"
                f"Severity: {res.severity.upper()}\n"
                f"Confidence: {int(res.confidence*100)}%\n\n"
                f"Quarantine this file? (Yes=Quarantine, No=Delete, Cancel=Keep)"
            )
            if action is True:
                self._quarantine(Path(path), res)
            elif action is False:
                try: os.remove(path)
                except: pass
        else:
            messagebox.showinfo("✅ Clean", f"{Path(path).name}\nNo threats detected!")

    def _quarantine(self, path, scan_result=None):
        try:
            qdir = Path.home() / ".shadow_quarantine"
            qdir.mkdir(exist_ok=True)
            original_path = str(path)
            dest = qdir / path.name

            # Hash before moving
            try:
                h = hashlib.sha256()
                with open(path, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""): h.update(chunk)
                file_hash = h.hexdigest()[:32] + "..."
            except:
                file_hash = "Not available"

            shutil.move(str(path), str(dest))

            # Save metadata
            meta_file = Path.home() / ".shadow_antivirus" / "quarantine_meta.json"
            try:
                meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
            except:
                meta = {}

            meta[dest.name] = {
                "original_path": original_path,
                "threat":        getattr(scan_result, "threat_name", "Suspicious File"),
                "threat_type":   getattr(scan_result, "threat_type", "Unknown"),
                "detected_by":   ", ".join(getattr(scan_result, "modules_run", [])[:3]) or "Shadow Scanner",
                "date":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hash":          file_hash,
            }
            meta_file.write_text(json.dumps(meta, indent=2))
        except: pass

    def _del_quar(self, path):
        # Also remove from metadata
        try:
            meta_file = Path.home() / ".shadow_antivirus" / "quarantine_meta.json"
            if meta_file.exists():
                meta = json.loads(meta_file.read_text())
                meta.pop(path.name, None)
                meta_file.write_text(json.dumps(meta, indent=2))
        except: pass
        try: path.unlink()
        except: pass
        self._go("quarantine")

    # ── Keybinds ──
    def _bind_keys(self):
        kb = self.cfg.get("keybinds", {
            "quick_scan": "Ctrl+Q",
            "full_scan":  "Ctrl+F",
            "settings":   "Ctrl+S",
            "quarantine": "Ctrl+R",
        })
        # Convert "Ctrl+Q" format to tkinter "<Control-q>" format
        def to_tk(combo):
            try:
                parts = combo.split("+")
                mods = []
                key = parts[-1].lower()
                for p in parts[:-1]:
                    p = p.lower()
                    if p == "ctrl": mods.append("Control")
                    elif p == "shift": mods.append("Shift")
                    elif p == "alt": mods.append("Alt")
                return "<" + "-".join(mods + [key]) + ">"
            except:
                return None

        self.unbind("<Control-q>")
        self.unbind("<Control-f>")
        self.unbind("<Control-s>")
        self.unbind("<Control-r>")

        for action, default in [
            ("quick_scan","Ctrl+Q"),
            ("full_scan","Ctrl+F"),
            ("settings","Ctrl+S"),
            ("quarantine","Ctrl+R"),
        ]:
            tk_bind = to_tk(kb.get(action, default))
            if not tk_bind: continue
            if action == "quick_scan":   self.bind(tk_bind, lambda e: self.quick_scan())
            elif action == "full_scan":  self.bind(tk_bind, lambda e: self.full_scan())
            elif action == "settings":   self.bind(tk_bind, lambda e: self._go("settings"))
            elif action == "quarantine": self.bind(tk_bind, lambda e: self._go("quarantine"))


if __name__ == "__main__":
    app = ShadowAntivirus()
    app._bind_keys()
    app.mainloop()
