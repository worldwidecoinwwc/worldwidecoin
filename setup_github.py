#!/usr/bin/env python3
"""
GitHub Repository Setup Script for WorldWideCoin
Helps create and push to GitHub repository
"""

import subprocess
import webbrowser
import os


def run_command(command, description):
    """Run a command and show result"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("✅ SUCCESS!")
            if result.stdout:
                print(f"Output:\n{result.stdout}")
        else:
            print("✅ SUCCESS! (No output)")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def setup_github_repo():
    """Setup GitHub repository"""
    print("WorldWideCoin GitHub Repository Setup")
    print("="*50)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not a Git repository. Please run 'git init' first.")
        return False
    
    # Get GitHub repository URL
    github_url = input("Enter your GitHub repository URL (or press Enter for worldwidecoinwwc/worldwidecoin): ").strip()
    if not github_url:
        github_url = "https://github.com/worldwidecoinwwc/worldwidecoin.git"
    
    # Get branch name
    branch = input("Enter branch name (or press Enter for main): ").strip()
    if not branch:
        branch = "main"
    
    print(f"\nRepository URL: {github_url}")
    print(f"Branch: {branch}")
    
    # Commands to run
    commands = [
        (f'git remote add origin {github_url}', 'Add remote origin'),
        ('git branch -M main', 'Rename branch to main'),
        (f'git push -u origin {branch}', 'Push to GitHub'),
    ]
    
    # Run commands
    for command, description in commands:
        if not run_command(command, description):
            print(f"\n❌ Failed to run: {description}")
            print("Please check the error above and try again.")
            return False
    
    print("\n" + "="*50)
    print("🎉 GitHub Repository Setup Complete!")
    print("="*50)
    
    # Open repository in browser
    try:
        repo_url = github_url.replace('.git', '')
        webbrowser.open(repo_url)
        print(f"🌐 Opened repository in browser: {repo_url}")
    except:
        print(f"🌐 Repository URL: {repo_url}")
    
    # Next steps
    print("\n📋 Next Steps:")
    print("1. Your code is now on GitHub!")
    print("2. You can enable GitHub Pages for the dashboard")
    print("3. Share the repository with others")
    print("4. Collaborators can now contribute")
    
    print(f"\n🔗 Repository: {github_url}")
    print("📊 Dashboard: https://worldwidecoinwwc.github.io/ (if GitHub Pages enabled)")
    
    return True


def show_repository_info():
    """Show current repository information"""
    print("\nCurrent Repository Information:")
    print("-"*30)
    
    # Check git status
    run_command('git status', 'Check git status')
    
    # Check remotes
    run_command('git remote -v', 'Check remotes')
    
    # Check current branch
    run_command('git branch', 'Check current branch')
    
    # Check last commit
    run_command('git log --oneline -1', 'Show last commit')


def main():
    """Main function"""
    print("WorldWideCoin GitHub Setup Tool")
    print("="*40)
    
    while True:
        print("\nOptions:")
        print("1. Setup GitHub repository")
        print("2. Show repository info")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            setup_github_repo()
        elif choice == '2':
            show_repository_info()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
