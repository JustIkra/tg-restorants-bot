# Project Documentation: Lunch Order TG Bot

## Business Logic
- [Technical Requirements](busness-logic/technical_requirements.md) - roles, scenarios, functional requirements
- [New Features Design](busness-logic/new_features_design.md) - Telegram notifications for cafes, Gemini recommendations

## Technical Documentation

### Backend
- [Tech Stack](tech-docs/stack.md) - Python 3.13, PostgreSQL 17, Kafka, Redis, Next.js, React
- [API Endpoints](tech-docs/api.md) - REST API for users and managers
- [Roles](tech-docs/roles.md) - user, manager
- [Architecture](tech-docs/image.png) - system diagram

### Frontend (Telegram Mini App)
- [Frontend Components](tech-docs/frontend-components.md) - React components documentation
- Location: `frontend_mini_app/`
- Stack: Next.js 16, React 19, Tailwind CSS 4, TypeScript

### Rules
- [Code Style](tech-docs/rules/code-style.md) - Python 3.13, Next.js/React/Tailwind conventions
- [Git Workflow](tech-docs/rules/git-workflow.md) - branches, commits, PRs
- [Testing](tech-docs/rules/testing.md) - pytest, fixtures, coverage

## Plans
- [AI Agents Workflow Design](plans/2025-12-05-ai-agents-workflow-design.md) - Supervisor + agents architecture

## Workflow
- [Config](workflow/config.yaml) - agents, pipelines, settings, **parallel execution**
- [Base Prompt](workflow/prompts/base.md) - common agent instructions, parallel mode
- Agent Roles:
  - [Task Creator](workflow/prompts/roles/task-creator.md) - creates tasks with codebase analysis
  - [Architect](workflow/prompts/roles/architect.md)
  - [Coder](workflow/prompts/roles/coder.md)
  - [Reviewer](workflow/prompts/roles/reviewer.md)
  - [Tester](workflow/prompts/roles/tester.md)
  - [Debugger](workflow/prompts/roles/debugger.md)
  - [DocWriter](workflow/prompts/roles/docwriter.md)
- Tasks: `workflow/tasks/active/`, `completed/`, `failed/`

## Commands
- [/task](.claude/commands/task.md) - create task with codebase analysis
