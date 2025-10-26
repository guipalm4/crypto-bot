#!/bin/bash
# Script to install git hooks for workflow enforcement

set -e

echo "🔧 Installing Git Hooks for Workflow Enforcement..."
echo ""

# Install pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Pre-push hook to prevent direct pushes to main/master

protected_branches=("main" "master")
current_branch=$(git symbolic-ref HEAD | sed -e 's,.*/\(.*\),\1,')

for branch in "${protected_branches[@]}"; do
    if [ "$current_branch" = "$branch" ]; then
        echo "🚫 ERROR: Direct push to '$branch' is not allowed!"
        echo ""
        echo "📋 Correct workflow:"
        echo "  1. Create a feature branch: git checkout -b feature/task-X-description"
        echo "  2. Make your changes and commit"
        echo "  3. Push the feature branch: git push origin feature/task-X-description"
        echo "  4. Create a Pull Request on GitHub"
        echo ""
        echo "💡 Quick fix if you already committed:"
        echo "  git branch feature/task-X-description  # Create branch at current commit"
        echo "  git reset --hard origin/main           # Reset main to remote"
        echo "  git checkout feature/task-X-description # Switch to feature branch"
        echo "  git push origin feature/task-X-description # Push feature branch"
        echo ""
        echo "🎯 Or use Task Master workflow:"
        echo "  ./scripts/workflow.sh start  # Start new task"
        echo "  # ... develop ..."
        echo "  ./scripts/workflow.sh finish # Finish and create PR"
        echo ""
        exit 1
    fi
done

# Run quality gates before allowing push
echo "🔍 Running quality checks (pre-push)..."
if command -v pre-commit >/dev/null 2>&1; then
    pre-commit run --all-files || exit 1
else
    echo "⚠️ pre-commit not found. Please install dev deps and run 'pre-commit install'."
    exit 1
fi

exit 0
EOF

chmod +x .git/hooks/pre-push

echo "✅ Pre-push hook installed!"
echo ""
echo "📋 What this does:"
echo "  - Blocks direct pushes to main/master"
echo "  - Forces you to use feature branches"
echo "  - Shows helpful workflow instructions"
echo ""
echo "🧪 Test it:"
echo "  git checkout main"
echo "  git push origin main  # Should fail!"
echo ""
echo "✅ Done!"

