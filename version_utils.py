# version_utils.py
"""
Utility-Modul für Versionsverwaltung und Update-Funktionen.
"""
import os
import subprocess
import requests
from functools import lru_cache
from datetime import datetime

# Pfad zur VERSION-Datei
VERSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION')
GITHUB_REPO = "Sinthos/WB-Intranet-2"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"


def get_version() -> str:
    """Liest die Version aus der VERSION-Datei."""
    try:
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"


def get_git_commit_hash(short: bool = True) -> str:
    """Gibt den aktuellen Git-Commit-Hash zurück."""
    try:
        cmd = ['git', 'rev-parse', '--short', 'HEAD'] if short else ['git', 'rev-parse', 'HEAD']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def get_git_commit_date() -> str:
    """Gibt das Datum des letzten Commits zurück."""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ci'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            date_str = result.stdout.strip()
            # Parse und formatiere das Datum
            dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d.%m.%Y %H:%M')
    except Exception:
        pass
    return "unbekannt"


def get_full_version_info() -> dict:
    """Gibt vollständige Versionsinformationen zurück."""
    return {
        "version": get_version(),
        "commit": get_git_commit_hash(short=True),
        "commit_full": get_git_commit_hash(short=False),
        "commit_date": get_git_commit_date(),
        "display": f"v{get_version()} ({get_git_commit_hash(short=True)})"
    }


def check_for_updates() -> dict:
    """
    Prüft auf GitHub, ob eine neuere Version verfügbar ist.
    Gibt ein Dictionary mit Update-Informationen zurück.
    """
    result = {
        "update_available": False,
        "current_version": get_version(),
        "current_commit": get_git_commit_hash(short=False),
        "latest_commit": None,
        "latest_commit_date": None,
        "latest_commit_message": None,
        "error": None
    }
    
    try:
        # Hole den neuesten Commit vom main/master Branch
        response = requests.get(
            f"{GITHUB_API_URL}/commits/main",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        
        if response.status_code == 404:
            # Versuche master Branch
            response = requests.get(
                f"{GITHUB_API_URL}/commits/master",
                headers={"Accept": "application/vnd.github.v3+json"},
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
        else:
            result["error"] = f"GitHub API Fehler: {response.status_code}"
            
    except requests.exceptions.Timeout:
        result["error"] = "Zeitüberschreitung bei der Verbindung zu GitHub"
    except requests.exceptions.RequestException as e:
        result["error"] = f"Verbindungsfehler: {str(e)}"
    except Exception as e:
        result["error"] = f"Unbekannter Fehler: {str(e)}"
    
    return result


def get_changelog(limit: int = 10) -> list:
    """
    Holt die letzten Commits von GitHub als Changelog.
    """
    changelog = []
    
    try:
        response = requests.get(
            f"{GITHUB_API_URL}/commits",
            params={"per_page": limit},
            headers={"Accept": "application/vnd.github.v3+json"},
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
                
    except Exception:
        pass
    
    return changelog
