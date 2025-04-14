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
        return None

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
    if not branches_output:
        print("No branches found or error fetching branches.")
        return
    
    branches = [b.strip().replace('origin/', '') for b in branches_output.splitlines() if "HEAD" not in b]
    print(f"Found branches: {branches}")
    
    # Create a folder for each branch
    for branch in branches:
        branch_dir = os.path.join(base_dir, branch)
        
        # Skip if branch folder already exists
        if os.path.exists(branch_dir):
            print(f"Branch folder {branch_dir} already exists, skipping...")
            continue
        
        print(f"Creating folder for branch {branch} at {branch_dir}...")
        # Clone the repo to the new branch folder
        clone_result = run_command(f"git clone {repo_dir} {branch_dir}", cwd=base_dir)
        if not clone_result:
            print(f"Failed to clone for branch {branch}, skipping...")
            continue
        
        # Verify branch exists before checkout
        branch_check = run_command(f"git rev-parse --verify origin/{branch}")
        if not branch_check:
            print(f"Branch {branch} does not exist or is invalid, skipping checkout...")
            shutil.rmtree(branch_dir)  # Clean up failed clone
            continue
        
        # Checkout the branch
        checkout_result = run_command(f"git checkout {branch}", cwd=branch_dir)
        if checkout_result is None:
            print(f"Failed to checkout branch {branch}, cleaning up...")
            shutil.rmtree(branch_dir)
            continue
        
        # List files to verify content
        files = run_command("dir", cwd=branch_dir)
        print(f"Files in {branch_dir}:\n{files}")
    
    print("Done! All branches have been cloned to separate folders.")

if __name__ == "__main__":
    # Configuration
    repo_url = "https://github.com/speethambaran/envitusIndoor.git"
    base_dir = os.path.join(os.getcwd(), "envitusIndoor_branches")  # Folder to store all branch folders
    
    try:
        clone_branches(repo_url, base_dir)
    except Exception as e:
        print(f"An error occurred: {e}")
