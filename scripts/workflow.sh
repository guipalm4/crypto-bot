#!/bin/bash
# Workflow automation script for Task Master + Git + GitHub

set -e

command=$1
shift 2>/dev/null || true

case "$command" in
    start)
        echo "🚀 Starting new task workflow..."
        echo ""
        
        # Get next task info
        echo "📋 Fetching next task from Task Master..."
        task_info=$(task-master next 2>&1 || echo "")
        
        if [[ -z "$task_info" ]]; then
            echo "❌ Error: Could not get task from Task Master"
            echo "💡 Make sure Task Master is initialized: task-master init"
            exit 1
        fi
        
        # Extract task ID and title
        task_id=$(echo "$task_info" | grep -i "id:" | head -1 | awk '{print $2}' | tr -d '[:space:]')
        task_title=$(echo "$task_info" | grep -i "title:" | head -1 | sed 's/.*Title://' | xargs | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -d '[:punct:]' | sed 's/--*/-/g')
        
        if [[ -z "$task_id" ]]; then
            echo "❌ Error: Could not extract task ID"
            exit 1
        fi
        
        branch_name="feature/task-${task_id}-${task_title}"
        
        # Check current branch
        current_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
        
        if [[ "$current_branch" != "main" ]] && [[ "$current_branch" != "master" ]]; then
            echo "⚠️  Warning: Currently on branch '$current_branch'"
            read -p "Switch to main first? (y/n): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git checkout main
                git pull origin main
            else
                echo "❌ Aborted"
                exit 1
            fi
        fi
        
        # Create and checkout new branch
        git checkout -b "$branch_name"
        
        echo ""
        echo "✅ Started work on Task #${task_id}"
        echo "📋 Branch: $branch_name"
        echo ""
        echo "📝 Next steps:"
        echo "  1. Develop your changes"
        echo "  2. Commit: git add . && git commit -m 'feat(task-${task_id}): description'"
        echo "  3. Finish: ./scripts/workflow.sh finish"
        echo ""
        ;;
        
    finish)
        echo "🏁 Finishing task workflow..."
        echo ""
        
        # Get current branch
        current_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
        
        if [[ -z "$current_branch" ]]; then
            echo "❌ Error: Could not determine current branch"
            exit 1
        fi
        
        if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
            echo "🚫 ERROR: Cannot finish from main/master branch!"
            echo "💡 Use: ./scripts/workflow.sh start"
            exit 1
        fi
        
        # Extract task ID from branch name
        task_id=$(echo "$current_branch" | grep -oP 'task-\K\d+' || echo "")
        
        if [[ -z "$task_id" ]]; then
            echo "⚠️  Warning: Could not extract task ID from branch name"
            read -p "Enter task ID manually: " task_id
            
            if [[ -z "$task_id" ]]; then
                echo "❌ Error: Task ID is required"
                exit 1
            fi
        fi
        
        # Check for uncommitted changes
        if [[ -n $(git status -s) ]]; then
            echo "⚠️  Warning: You have uncommitted changes"
            read -p "Commit them now? (y/n): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git add .
                read -p "Enter commit message: " commit_msg
                git commit -m "$commit_msg"
            else
                echo "❌ Please commit your changes first"
                exit 1
            fi
        fi
        
        # Push branch
        echo "📤 Pushing branch..."
        git push origin "$current_branch"
        
        # Get task title for PR
        task_title=$(echo "$current_branch" | sed 's/feature\/task-[0-9]*-//' | tr '-' ' ' | sed 's/\b\(.\)/\u\1/g')
        
        # Create PR
        echo "📝 Creating Pull Request..."
        gh pr create \
            --title "[Task #${task_id}] ${task_title}" \
            --body "## 📋 Descrição

Implementação da Task #${task_id}

## ✅ Checklist

- [ ] Código formatado
- [ ] Testes passando
- [ ] Documentação atualizada
- [ ] CI/CD passing

## 🔗 Relacionado

- Task Master AI Task #${task_id}" \
            --base main || {
                echo "⚠️  Warning: Could not create PR automatically"
                echo "💡 Create it manually at: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:\/]//' | sed 's/.git$//')/compare/${current_branch}?expand=1"
            }
        
        echo ""
        echo "✅ Task finished!"
        echo "📋 Next steps:"
        echo "  1. Review the PR on GitHub"
        echo "  2. Wait for CI/CD to pass"
        echo "  3. Merge the PR"
        echo "  4. Update task status: task-master set-status --id=${task_id} --status=done"
        echo ""
        ;;
        
    *)
        echo "Usage: $0 {start|finish}"
        echo ""
        echo "Commands:"
        echo "  start  - Start new task (creates branch from Task Master)"
        echo "  finish - Finish task (push + create PR)"
        echo ""
        echo "Example:"
        echo "  ./scripts/workflow.sh start   # Start new task"
        echo "  # ... develop ..."
        echo "  git add ."
        echo "  git commit -m 'feat(task-X): description'"
        echo "  ./scripts/workflow.sh finish  # Push and create PR"
        echo ""
        exit 1
        ;;
esac

