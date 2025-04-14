import os
import subprocess
import logging
import shutil
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from functools import partial

class GitCloner:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.total_size_estimate = 0
        
    def parse_github_url(self, url):
        if url.startswith("https://github.com/"):
            parts = url.strip('/').split('/')
            owner, repo = parts[3], parts[4].replace('.git', '')
        elif url.startswith("git@github.com:"):
            parts = url.split(':')[1].split('/')
            owner, repo = parts[0], parts[1].replace('.git', '')
        else:
            raise ValueError("Unsupported GitHub URL format")
        return owner, repo

    def sanitize_branch_name(self, branch):
        sanitized = re.sub(r'[\\/*?:"<>|]', '_', branch).strip().strip('.')
        return sanitized[:100]

    def get_repo_size(self, path):
        return sum(os.path.getsize(f) for f in os.listdir(path) if os.path.isfile(f))

    def check_disk_space(self, path):
        stats = shutil.disk_usage(path)
        return stats.free > self.total_size_estimate * 2

    def clone_branches(self, url, exclude_branches=[], retries=3, max_workers=4, progress_callback=None):
        try:
            owner, repo = self.parse_github_url(url)
            base_dir = os.path.abspath(repo)
            bare_repo_dir = os.path.join(base_dir, f"{repo}.git")
            branches_dir = os.path.join(base_dir, "branches")

            os.makedirs(bare_repo_dir, exist_ok=True)
            os.makedirs(branches_dir, exist_ok=True)

            # Clone bare repo
            self._run_command(['git', 'clone', '--bare', url, bare_repo_dir], retries)

            # Get branches
            branches = self._get_branches(bare_repo_dir)
            branches = [b for b in branches if b not in exclude_branches]
            
            # Estimate size
            self.total_size_estimate = self.get_repo_size(bare_repo_dir) * len(branches)
            if not self.check_disk_space(base_dir):
                raise RuntimeError("Insufficient disk space for cloning")

            # Process branches in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for branch in branches:
                    future = executor.submit(
                        self._process_branch,
                        bare_repo_dir,
                        branches_dir,
                        branch,
                        retries,
                        progress_callback
                    )
                    futures.append(future)

                for future in as_completed(futures):
                    future.result()

            return True, "Cloning completed successfully"
        except Exception as e:
            return False, str(e)

    def _process_branch(self, bare_repo_dir, branches_dir, branch, retries, progress_callback):
        sanitized = self.sanitize_branch_name(branch)
        branch_path = os.path.join(branches_dir, sanitized)

        if os.path.exists(branch_path):
            self.logger.info(f"Skipping existing branch: {branch}")
            return

        for attempt in range(retries + 1):
            try:
                self._run_command([
                    'git',
                    f'--git-dir={bare_repo_dir}',
                    'worktree',
                    'add',
                    '--force',
                    branch_path,
                    branch
                ])
                if progress_callback:
                    progress_callback(f"Cloned {branch}")
                break
            except Exception as e:
                if attempt == retries:
                    self.logger.error(f"Failed to clone {branch}: {str(e)}")
                    if os.path.exists(branch_path):
                        shutil.rmtree(branch_path)
                    raise
                time.sleep(1)

    def _run_command(self, command, retries=3):
        for attempt in range(retries + 1):
            try:
                subprocess.run(
                    command,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )
                return
            except subprocess.CalledProcessError as e:
                if attempt == retries:
                    raise RuntimeError(e.stderr.decode().strip())
                time.sleep(1)

    def _get_branches(self, bare_repo_dir):
        result = subprocess.run(
            ['git', 'branch', '--list'],
            cwd=bare_repo_dir,
            capture_output=True,
            text=True
        )
        return [b.strip('* ').strip() for b in result.stdout.splitlines() if b.strip()]