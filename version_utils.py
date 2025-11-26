# version_utils.py
"""
Utility-Modul für Versionsverwaltung und Update-Funktionen.
"""
import os
import subprocess
import requests
from functools import lru_cache
from datetime import datetime, timedelta
import time

# Pfad zur VERSION-Datei
VERSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION')
GITHUB_REPO = "Sinthos/WB-Intranet-2"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"

# Cache für API-Anfragen (verhindert Rate-Limiting)
_update_cache = {
    "data": None,
    "timestamp": None,
    "cache_duration": 300  # 5 Minuten Cache
}

_changelog_cache = {
    "data": None,
    "timestamp": None,
    "cache_duration": 600  # 10 Minuten Cache
}


# Datei für persistente Build-Informationen (wird beim Update erstellt)
BUILD_INFO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.build_info')


def get_version() -> str:
    """Liest die Version aus der VERSION-Datei."""
    try:
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"


def _save_build_info(commit: str, commit_full: str, commit_date: str):
    """Speichert Build-Informationen in eine Datei."""
    try:
        with open(BUILD_INFO_FILE, 'w') as f:
            f.write(f"{commit}\n{commit_full}\n{commit_date}")
    except Exception:
        pass


def _load_build_info() -> tuple:
    """Lädt Build-Informationen aus der Datei."""
    try:
        with open(BUILD_INFO_FILE, 'r') as f:
            lines = f.read().strip().split('\n')
            if len(lines) >= 3:
                return lines[0], lines[1], lines[2]
    except Exception:
        pass
    return None, None, None


def get_git_commit_hash(short: bool = True) -> str:
    """Gibt den aktuellen Git-Commit-Hash zurück."""
    # Zuerst versuchen aus Build-Info-Datei zu laden (schneller und zuverlässiger)
    commit_short, commit_full, _ = _load_build_info()
    if short and commit_short:
        return commit_short
    elif not short and commit_full:
        return commit_full
    
    # Fallback: Git-Befehl versuchen
    try:
        cmd = ['git', 'rev-parse', '--short', 'HEAD'] if short else ['git', 'rev-parse', 'HEAD']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        # Git ist nicht installiert
        pass
    except Exception:
        pass
    
    return "lokal"


def get_git_commit_date() -> str:
    """Gibt das Datum des letzten Commits zurück."""
    # Zuerst versuchen aus Build-Info-Datei zu laden
    _, _, commit_date = _load_build_info()
    if commit_date:
        return commit_date
    
    # Fallback: Git-Befehl versuchen
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ci'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            date_str = result.stdout.strip()
            # Parse und formatiere das Datum
            dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d.%m.%Y %H:%M')
    except FileNotFoundError:
        # Git ist nicht installiert
        pass
    except Exception:
        pass
    
    # Letzter Fallback: Datei-Änderungsdatum der VERSION-Datei
    try:
        mtime = os.path.getmtime(VERSION_FILE)
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime('%d.%m.%Y %H:%M')
    except Exception:
        pass
    
    return "-"


def get_full_version_info() -> dict:
    """Gibt vollständige Versionsinformationen zurück."""
    version = get_version()
    commit = get_git_commit_hash(short=True)
    commit_full = get_git_commit_hash(short=False)
    commit_date = get_git_commit_date()
    
    # Speichere Build-Info für zukünftige Verwendung (falls Git verfügbar)
    if commit != "lokal" and commit_full != "lokal":
        _save_build_info(commit, commit_full, commit_date)
    
    return {
        "version": version,
        "commit": commit,
        "commit_full": commit_full,
        "commit_date": commit_date,
        "display": f"v{version}" + (f" ({commit})" if commit != "lokal" else "")
    }


def _is_cache_valid(cache: dict) -> bool:
    """Prüft, ob der Cache noch gültig ist."""
    if cache["data"] is None or cache["timestamp"] is None:
        return False
    elapsed = time.time() - cache["timestamp"]
    return elapsed < cache["cache_duration"]


def _check_for_updates_via_git() -> dict:
    """
    Prüft auf Updates über lokale Git-Befehle (kein API-Limit).
    """
    result = {
        "update_available": False,
        "current_version": get_version(),
        "current_commit": get_git_commit_hash(short=False),
        "latest_commit": None,
        "latest_commit_date": None,
        "latest_commit_message": None,
        "error": None,
        "source": "git"
    }
    
    cwd = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Fetch updates from remote (ohne zu mergen)
        fetch_result = subprocess.run(
            ['git', 'fetch', 'origin'],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        
        if fetch_result.returncode != 0:
            result["error"] = "Git fetch fehlgeschlagen"
            return result
        
        # Hole den neuesten Remote-Commit
        remote_result = subprocess.run(
            ['git', 'rev-parse', 'origin/main'],
            capture_output=True,
            text=True,
            cwd=cwd
        )
        
        if remote_result.returncode != 0:
            # Versuche origin/master
            remote_result = subprocess.run(
                ['git', 'rev-parse', 'origin/master'],
                capture_output=True,
                text=True,
                cwd=cwd
            )
        
        if remote_result.returncode == 0:
            latest_commit = remote_result.stdout.strip()
            result["latest_commit"] = latest_commit[:7]
            result["latest_commit_full"] = latest_commit
            
            # Hole Commit-Nachricht
            msg_result = subprocess.run(
                ['git', 'log', '-1', '--format=%s', latest_commit],
                capture_output=True,
                text=True,
                cwd=cwd
            )
            if msg_result.returncode == 0:
                result["latest_commit_message"] = msg_result.stdout.strip()
            
            # Hole Commit-Datum
            date_result = subprocess.run(
                ['git', 'log', '-1', '--format=%ci', latest_commit],
                capture_output=True,
                text=True,
                cwd=cwd
            )
            if date_result.returncode == 0:
                date_str = date_result.stdout.strip()
                dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
                result["latest_commit_date"] = dt.strftime('%d.%m.%Y %H:%M')
            
            # Vergleiche Commits
            if latest_commit and result["current_commit"] != "unknown":
                result["update_available"] = latest_commit != result["current_commit"]
        else:
            result["error"] = "Konnte Remote-Branch nicht finden"
            
    except FileNotFoundError:
        result["error"] = "Git ist nicht installiert. Bitte Update manuell durchführen."
    except subprocess.TimeoutExpired:
        result["error"] = "Git-Befehl Zeitüberschreitung"
    except Exception as e:
        result["error"] = f"Git-Fehler: {str(e)}"
    
    return result


def check_for_updates() -> dict:
    """
    Prüft auf GitHub, ob eine neuere Version verfügbar ist.
    Verwendet Caching um Rate-Limits zu vermeiden.
    Gibt ein Dictionary mit Update-Informationen zurück.
    """
    global _update_cache
    
    # Prüfe Cache
    if _is_cache_valid(_update_cache):
        return _update_cache["data"]
    
    result = {
        "update_available": False,
        "current_version": get_version(),
        "current_commit": get_git_commit_hash(short=False),
        "latest_commit": None,
        "latest_commit_date": None,
        "latest_commit_message": None,
        "error": None,
        "source": "github"
    }
    
    try:
        # Hole den neuesten Commit vom main/master Branch
        response = requests.get(
            f"{GITHUB_API_URL}/commits/main",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "WB-Intranet-2"
            },
            timeout=10
        )
        
        if response.status_code == 404:
            # Versuche master Branch
            response = requests.get(
                f"{GITHUB_API_URL}/commits/master",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "WB-Intranet-2"
                },
                timeout=10
            )
        
        if response.status_code == 200:
            data = response.json()
            latest_commit = data.get("sha", "")
            
            result["latest_commit"] = latest_commit[:7] if latest_commit else None
            result["latest_commit_full"] = latest_commit
            
            commit_info = data.get("commit", {})
            result["latest_commit_message"] = commit_info.get("message", "").split("\n")[0]
            
            commit_date = commit_info.get("committer", {}).get("date", "")
            if commit_date:
                dt = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
                result["latest_commit_date"] = dt.strftime('%d.%m.%Y %H:%M')
            
            # Vergleiche Commits
            if latest_commit and result["current_commit"] != "unknown":
                result["update_available"] = latest_commit != result["current_commit"]
                
            # Cache das Ergebnis
            _update_cache["data"] = result
            _update_cache["timestamp"] = time.time()
            
        elif response.status_code == 403:
            # Rate-Limit erreicht - versuche Git-Fallback
            result = _check_for_updates_via_git()
            if not result.get("error"):
                _update_cache["data"] = result
                _update_cache["timestamp"] = time.time()
        else:
            result["error"] = f"GitHub API Fehler: {response.status_code}"
            
    except requests.exceptions.Timeout:
        # Timeout - versuche Git-Fallback
        result = _check_for_updates_via_git()
    except requests.exceptions.RequestException as e:
        # Verbindungsfehler - versuche Git-Fallback
        result = _check_for_updates_via_git()
        if result.get("error"):
            result["error"] = f"Verbindungsfehler: {str(e)}"
    except Exception as e:
        result["error"] = f"Unbekannter Fehler: {str(e)}"
    
    return result


def _get_changelog_via_git(limit: int = 10) -> list:
    """
    Holt die letzten Commits über lokale Git-Befehle.
    """
    changelog = []
    
    try:
        cwd = os.path.dirname(os.path.abspath(__file__))
        
        # Hole die letzten Commits
        result = subprocess.run(
            ['git', 'log', f'-{limit}', '--format=%H|%s|%ci|%an'],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        sha, message, date_str, author = parts
                        try:
                            dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
                            formatted_date = dt.strftime('%d.%m.%Y')
                        except:
                            formatted_date = "unbekannt"
                        
                        changelog.append({
                            "sha": sha[:7],
                            "message": message,
                            "date": formatted_date,
                            "author": author
                        })
    except FileNotFoundError:
        # Git ist nicht installiert
        pass
    except Exception:
        pass
    
    return changelog


def get_changelog(limit: int = 10) -> list:
    """
    Holt die letzten Commits von GitHub als Changelog.
    Verwendet Caching um Rate-Limits zu vermeiden.
    """
    global _changelog_cache
    
    # Prüfe Cache
    if _is_cache_valid(_changelog_cache) and _changelog_cache.get("limit") == limit:
        return _changelog_cache["data"]
    
    changelog = []
    
    try:
        response = requests.get(
            f"{GITHUB_API_URL}/commits",
            params={"per_page": limit},
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "WB-Intranet-2"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            commits = response.json()
            for commit in commits:
                commit_info = commit.get("commit", {})
                commit_date = commit_info.get("committer", {}).get("date", "")
                
                if commit_date:
                    dt = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
                    formatted_date = dt.strftime('%d.%m.%Y')
                else:
                    formatted_date = "unbekannt"
                
                changelog.append({
                    "sha": commit.get("sha", "")[:7],
                    "message": commit_info.get("message", "").split("\n")[0],
                    "date": formatted_date,
                    "author": commit_info.get("author", {}).get("name", "unbekannt")
                })
            
            # Cache das Ergebnis
            _changelog_cache["data"] = changelog
            _changelog_cache["timestamp"] = time.time()
            _changelog_cache["limit"] = limit
            
        elif response.status_code == 403:
            # Rate-Limit erreicht - versuche Git-Fallback
            changelog = _get_changelog_via_git(limit)
            if changelog:
                _changelog_cache["data"] = changelog
                _changelog_cache["timestamp"] = time.time()
                _changelog_cache["limit"] = limit
        else:
            # Andere Fehler - versuche Git-Fallback
            changelog = _get_changelog_via_git(limit)
                
    except Exception:
        # Bei Fehlern versuche Git-Fallback
        changelog = _get_changelog_via_git(limit)
    
    return changelog
