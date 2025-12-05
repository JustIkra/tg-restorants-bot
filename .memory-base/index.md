# Project Documentation: Lunch Order TG Bot

## Business Logic
- [Technical Requirements](busness-logic/technical_requirements.md) - roles, scenarios, functional requirements
- [New Features Design](busness-logic/new_features_design.md) - Telegram notifications for cafes, Gemini recommendations

## Technical Documentation
- [Tech Stack](tech-docs/stack.md) - Python 3.13, PostgreSQL 17, Kafka, Redis, React
- [API Endpoints](tech-docs/api.md) - REST API for users and managers
- [Roles](tech-docs/roles.md) - user, manager
- [Architecture](tech-docs/image.png) - system diagram

### Rules
- [Code Style](tech-docs/rules/code-style.md) - Python 3.13, TypeScript/React conventions
- [Git Workflow](tech-docs/rules/git-workflow.md) - branches, commits, PRs
- [Testing](tech-docs/rules/testing.md) - pytest, fixtures, coverage

## Plans
- [AI Agents Workflow Design](plans/2025-12-05-ai-agents-workflow-design.md) - Supervisor + agents architecture

## Workflow
- [Config](workflow/config.yaml) - agents, pipelines, settings
- [Base Prompt](workflow/prompts/base.md) - common agent instructions
- Agent Roles:
  - [Architect](workflow/prompts/roles/architect.md)
  - [Coder](workflow/prompts/roles/coder.md)
  - [Reviewer](workflow/prompts/roles/reviewer.md)
  - [Tester](workflow/prompts/roles/tester.md)
  - [Debugger](workflow/prompts/roles/debugger.md)
  - [DocWriter](workflow/prompts/roles/docwriter.md)
- Tasks: `workflow/tasks/active/`, `completed/`, `failed/`
