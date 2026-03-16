import os
import subprocess
from pathlib import Path
from datetime import datetime


class SystemHandler:
    """
    Handles all project management tasks through HIL — no raw shell needed.

    SYSTEM subcommands
    ------------------
    File operations:
      move    src:<path> dest:<path>
      rename  src:<path> dest:<path>
      delete  path:<path>
      mkdir   path:<path>
      list    [path:<path>]
      clean

    Git operations:
      status             — git status + disk usage
      diff               — git diff (staged + unstaged)
      log    [n:<int>]   — recent commits (default 10)
      add    [path:<p>]  — git add (default: -A)
      commit message:"…" — git commit only (no push)
      push               — git push origin main
      pull               — git pull
      sync   message:"…" — add + commit + push (full sync)
    """

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)

    # ── Dispatch ──────────────────────────────────────────────────────────────

    def handle(self, envelope: dict) -> dict:
        verb = envelope.get("verb")
        subcommand = envelope.get("subcommand")
        params = envelope.get("params", {})

        if verb == "SYSTEM":
            return self._handle_system(subcommand, params)
        elif verb == "OPERATOR":
            return self._handle_operator(subcommand, params)

        return {"status": "error", "message": f"Unknown system verb: {verb}"}

    # ── SYSTEM ────────────────────────────────────────────────────────────────

    def _handle_system(self, subcommand: str, params: dict) -> dict:
        handlers = {
            "sync":   self._sys_sync,
            "status": self._sys_status,
            "diff":   self._sys_diff,
            "log":    self._sys_log,
            "add":    self._sys_add,
            "commit": self._sys_commit,
            "push":   self._sys_push,
            "pull":   self._sys_pull,
            "clean":  self._sys_clean,
            "move":   self._sys_move,
            "rename": self._sys_move,
            "delete": self._sys_delete,
            "mkdir":  self._sys_mkdir,
            "list":   self._sys_list,
        }
        fn = handlers.get(subcommand)
        if fn is None:
            return {
                "status": "error",
                "message": (
                    f"Unknown SYSTEM subcommand: {subcommand!r}\n"
                    f"Available: {', '.join(sorted(handlers))}"
                ),
            }
        return fn(params)

    # ── Git operations ────────────────────────────────────────────────────────

    def _sys_sync(self, params: dict) -> dict:
        """git add -A + commit + push."""
        message = params.get("message", f"HELIX AUTO-SYNC: {datetime.now().isoformat()}")
        try:
            subprocess.run(["git", "add", "-A"], cwd=self.repo_root, check=True)
            subprocess.run(["git", "commit", "-m", message], cwd=self.repo_root, check=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=self.repo_root, check=True)
            return {"status": "ok", "message": f"Synced: {message}"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Sync failed: {e}"}

    def _sys_status(self, params: dict) -> dict:
        """git status --short + disk usage."""
        try:
            res = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.repo_root, capture_output=True, text=True,
            )
            disk = subprocess.run(
                ["du", "-sh", str(self.repo_root)],
                capture_output=True, text=True,
            )
            return {
                "status":     "ok",
                "git_status": res.stdout or "(clean)",
                "disk_usage": disk.stdout.strip(),
                "repo_root":  str(self.repo_root),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _sys_diff(self, params: dict) -> dict:
        """git diff HEAD (staged + unstaged)."""
        try:
            res = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=self.repo_root, capture_output=True, text=True,
            )
            return {"status": "ok", "diff": res.stdout or "(no changes)"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _sys_log(self, params: dict) -> dict:
        """git log --oneline -n <n>."""
        n = int(params.get("n", 10))
        try:
            res = subprocess.run(
                ["git", "log", "--oneline", f"-{n}"],
                cwd=self.repo_root, capture_output=True, text=True,
            )
            return {"status": "ok", "log": res.stdout or "(no commits)"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _sys_add(self, params: dict) -> dict:
        """git add <path> or git add -A."""
        path = params.get("path")
        args = ["git", "add", path] if path else ["git", "add", "-A"]
        try:
            subprocess.run(args, cwd=self.repo_root, check=True)
            return {"status": "ok", "message": f"Staged: {path or 'all'}"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": str(e)}

    def _sys_commit(self, params: dict) -> dict:
        """git commit -m <message> (no push)."""
        message = params.get("message")
        if not message:
            return {"status": "error", "message": "commit requires message:\"...\""}
        try:
            subprocess.run(["git", "commit", "-m", message], cwd=self.repo_root, check=True)
            return {"status": "ok", "message": f"Committed: {message}"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Commit failed: {e}"}

    def _sys_push(self, params: dict) -> dict:
        """git push origin main."""
        try:
            subprocess.run(["git", "push", "origin", "main"], cwd=self.repo_root, check=True)
            return {"status": "ok", "message": "Pushed to origin/main"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Push failed: {e}"}

    def _sys_pull(self, params: dict) -> dict:
        """git pull."""
        try:
            res = subprocess.run(
                ["git", "pull"],
                cwd=self.repo_root, capture_output=True, text=True,
            )
            return {"status": "ok", "message": res.stdout.strip() or "Already up to date."}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Pull failed: {e}"}

    # ── File operations ───────────────────────────────────────────────────────

    def _sys_clean(self, params: dict) -> dict:
        """Remove __pycache__ trees."""
        try:
            subprocess.run(
                ["find", ".", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", "+"],
                cwd=self.repo_root,
            )
            tmp = self.repo_root / "last_hil_run.json"
            if tmp.exists():
                tmp.unlink()
            return {"status": "ok", "message": "Cleaned __pycache__ and temp files."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _sys_move(self, params: dict) -> dict:
        """Move or rename a file/directory."""
        src  = params.get("src")
        dest = params.get("dest")
        if not src or not dest:
            return {"status": "error", "message": "move/rename requires src:<path> dest:<path>"}

        src_path  = (self.repo_root / src).resolve()
        dest_path = (self.repo_root / dest).resolve()

        if ".git" in str(src_path) or ".git" in str(dest_path):
            return {"status": "error", "message": "Access to .git is restricted."}
        if not str(src_path).startswith(str(self.repo_root)):
            return {"status": "error", "message": "src must be inside repository."}

        try:
            import shutil
            if dest_path.exists() and dest_path.is_dir():
                shutil.move(str(src_path), str(dest_path))
            else:
                src_path.rename(dest_path)
            return {"status": "ok", "message": f"Moved {src} -> {dest}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _sys_delete(self, params: dict) -> dict:
        """Delete a file or directory."""
        path = params.get("path")
        if not path:
            return {"status": "error", "message": "delete requires path:<path>"}

        target = (self.repo_root / path).resolve()
        if ".git" in str(target) or not str(target).startswith(str(self.repo_root)):
            return {"status": "error", "message": "Restricted deletion target."}
        if target == self.repo_root:
            return {"status": "error", "message": "Cannot delete repository root."}

        try:
            if target.is_dir():
                import shutil
                shutil.rmtree(target)
            else:
                target.unlink()
            return {"status": "ok", "message": f"Deleted {path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _sys_mkdir(self, params: dict) -> dict:
        """Create a directory (parents=True)."""
        path = params.get("path")
        if not path:
            return {"status": "error", "message": "mkdir requires path:<path>"}

        target = (self.repo_root / path).resolve()
        if not str(target).startswith(str(self.repo_root)):
            return {"status": "error", "message": "path must be inside repository."}

        try:
            target.mkdir(parents=True, exist_ok=True)
            return {"status": "ok", "message": f"Created {path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _sys_list(self, params: dict) -> dict:
        """List directory contents."""
        path = params.get("path", ".")
        target = (self.repo_root / path).resolve()
        if not str(target).startswith(str(self.repo_root)):
            return {"status": "error", "message": "path must be inside repository."}

        try:
            items = sorted(os.listdir(target))
            return {"status": "ok", "path": path, "items": items}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ── OPERATOR ──────────────────────────────────────────────────────────────

    def _handle_operator(self, subcommand: str, params: dict) -> dict:
        if subcommand == "log":
            message = params.get("message")
            if not message:
                return {"status": "error", "message": "No message provided for logging."}

            operator_file = self.repo_root / "OPERATOR.md"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"\n### [{timestamp}] Operator Observation\n{message}\n"

            try:
                with open(operator_file, "a") as f:
                    f.write(entry)
                return {"status": "ok", "message": "Log entry added to OPERATOR.md"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        elif subcommand == "status":
            operator_file = self.repo_root / "OPERATOR.md"
            try:
                with open(operator_file, "r") as f:
                    content = f.read()
                return {"status": "ok", "last_log": content[-500:]}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        elif subcommand == "profile":
            operator_file = self.repo_root / "OPERATOR.md"
            try:
                with open(operator_file, "r") as f:
                    content = f.read()
                return {"status": "ok", "profile": content[:1000]}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "error", "message": f"Unknown operator subcommand: {subcommand}"}
