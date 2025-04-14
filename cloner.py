import os
import subprocess
import argparse
import time
import re

def parse_github_url(url):
    """Parse GitHub URL to extract owner and repository name."""
    if url.startswith("https://github.com/"):
        parts = url.strip('/').split('/')
        if len(parts) < 5:
            raise ValueError("Invalid GitHub URL format")
        owner = parts[3]
        repo = parts[4].replace('.git', '')
    elif url.startswith("git@github.com:"):
        parts = url.split(':')[1].split('/')
        if len(parts) < 2:
            raise ValueError("Invalid GitHub URL format")
        owner = parts[0]
        repo = parts[1].replace('.git', '')
    else:
        raise ValueError("Unsupported GitHub URL format")
    return owner, repo

def sanitize_branch_name(branch):
    """Sanitize branch name to create valid directory name."""
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', branch)
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip().strip('.')
    # Truncate long names (Windows path limit is 260 chars)
    return sanitized[:100]

def main():
    parser = argparse.ArgumentParser(
        description='Clone a GitHub repository and all its branches into separate directories.'
    )
    parser.add_argument('url', type=str, help='GitHub repository URL')
    parser.add_argument('--retries', type=int, default=3,
                       help='Number of retries for network operations')
    args = parser.parse_args()

    try:
        owner, repo = parse_github_url(args.url)
    except ValueError as e:
        print(f"Error: {e}")
        return

    base_dir = os.path.abspath(repo)
    bare_repo_dir = os.path.join(base_dir, f"{repo}.git")
    branches_dir = os.path.join(base_dir, "branches")

    print(f"Creating directory structure at {base_dir}")
    os.makedirs(bare_repo_dir, exist_ok=True)
    os.makedirs(branches_dir, exist_ok=True)

    # Clone bare repository with retries
    print(f"Cloning bare repository from {args.url}")
    for attempt in range(args.retries + 1):
        try:
            subprocess.run(
                ['git', 'clone', '--bare', args.url, bare_repo_dir],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            break
        except subprocess.CalledProcessError:
            if attempt == args.retries:
                print("Failed to clone repository after multiple attempts")
                return
            print(f"Clone failed, retrying... ({attempt + 1}/{args.retries})")
            time.sleep(2)

    # Get list of branches
    try:
        result = subprocess.run(
            ['git', 'branch', '--list'],
            cwd=bare_repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error getting branches: {e.stderr}")
        return

    branches = [b.strip('* ').strip() for b in result.stdout.splitlines() if b.strip()]
    print(f"Found {len(branches)} branches to process")

    # Process each branch
    for branch in branches:
        if not branch:
            continue

        sanitized = sanitize_branch_name(branch)
        branch_path = os.path.join(branches_dir, sanitized)

        if os.path.exists(branch_path):
            print(f"Skipping existing branch: {branch} ({sanitized})")
            continue

        print(f"Creating worktree for branch: {branch}")
        print(f"  Target directory: {branch_path}")

        for attempt in range(args.retries + 1):
            try:
                subprocess.run(
                    [
                        'git',
                        f'--git-dir={bare_repo_dir}',
                        'worktree',
                        'add',
                        '--force',
                        branch_path,
                        branch
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )
                break
            except subprocess.CalledProcessError as e:
                if attempt == args.retries:
                    print(f"  Failed to create worktree for {branch}")
                    print(f"  Error: {e.stderr.decode().strip()}")
                    break
                print(f"  Attempt {attempt + 1} failed, retrying...")
                time.sleep(1)

    print("\nProcess completed!")
    print(f"Main repository: {bare_repo_dir}")
    print(f"All branches cloned to: {branches_dir}")

if __name__ == "__main__":
    main()
