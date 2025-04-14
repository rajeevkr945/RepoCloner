import os
import subprocess
import shutil

def run_command(command, cwd=None):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True, cwd=cwd)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e.stderr}")
        raise

def clone_branches(repo_url, base_dir):
    """Clone a repository and create separate folders for each branch."""
    # Ensure base_dir exists
    os.makedirs(base_dir, exist_ok=True)
    
    # Extract repo name from URL
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    repo_dir = os.path.join(base_dir, repo_name)
    
    # Clone the repository if it doesn't exist
    if not os.path.exists(repo_dir):
        print(f"Cloning repository to {repo_dir}...")
        run_command(f"git clone {repo_url}", cwd=base_dir)
    else:
        print(f"Repository already exists at {repo_dir}, using it.")
    
    # Change to the repo directory
    os.chdir(repo_dir)
    
    # Fetch all remote branches
    print("Fetching all branches...")
    run_command("git fetch origin")
    
    # Get list of remote branches (excluding HEAD)
    branches_output = run_command("git branch -r")
    branches = [b.strip() for b in branches_output.splitlines() if "HEAD" not in b]
    branches = [b.replace('origin/', '') for b in branches]
    
    # Create a folder for each branch
    for branch in branches:
        branch_dir = os.path.join(base_dir, branch)
        
        # Skip if branch folder already exists
        if os.path.exists(branch_dir):
            print(f"Branch folder {branch_dir} already exists, skipping...")
            continue
        
        print(f"Creating folder for branch {branch} at {branch_dir}...")
        # Clone the repo to the new branch folder
        run_command(f"git clone {repo_dir} {branch_dir}", cwd=base_dir)
        
        # Change to the branch folder and checkout the branch
        run_command(f"git checkout {branch}", cwd=branch_dir)
    
    print("Done! All branches have been cloned to separate folders.")

if __name__ == "__main__":
    # Configuration
    repo_url = "REPO_URL"
    base_dir = os.path.join(os.getcwd(), "REPO_URL_branches")  # Folder to store all branch folders
    
    try:
        clone_branches(repo_url, base_dir)
    except Exception as e:
        print(f"An error occurred: {e}")
