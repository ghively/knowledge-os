# GitHub Setup Guide

This document describes the GitHub repository setup for Knowledge OS and what remains to be configured.

## ✅ Completed Setup

### Repository Creation
- [x] Created private repository: `ghively/knowledge-os`
- [x] Added description: "A Capacities/Anytype-inspired knowledge management system with OpenClaw agent integration, built on Qdrant"
- [x] Enabled Issues, Projects, and Wiki features

### Issue Templates
Located in `.github/ISSUE_TEMPLATE/`:
- [x] **Bug Report** (`bug_report.md`) - Template for reporting bugs
- [x] **Feature Request** (`feature_request.md`) - Template for new features
- [x] **Development Task** (`task.md`) - Template for technical tasks

### Pull Request Template
Located in `.github/pull_request_template.md`:
- [x] Description section
- [x] Related issue linking
- [x] Change type selection (bug fix, feature, breaking change, etc.)
- [x] Changes made checklist
- [x] Testing requirements
- [x] Full PR checklist

### CI/CD Workflows
Located in `.github/workflows/`:

#### ci.yml
- [x] Frontend checks (linting, type checking, build)
- [x] Backend checks (flake8, black, isort, pytest)
- [x] Docker build tests
- [x] Security scanning with Trivy
- [x] Runs on push to main/develop and all PRs

#### release.yml
- [x] Creates GitHub releases on version tags
- [x] Builds and pushes Docker images to GitHub Container Registry (GHCR)
- [x] Generates SBOMs for security auditing
- [x] Multi-architecture support

### Dependency Management
Located in `.github/dependabot.yml`:
- [x] Weekly npm updates (frontend)
- [x] Weekly pip updates (backend)
- [x] Weekly Docker updates
- [x] Weekly GitHub Actions updates
- [x] Auto-creates PRs for security patches
- [x] Ignores major version updates (manual review required)

### Labels Created
- [x] `priority-high` (red) - High priority items
- [x] `priority-medium` (orange) - Medium priority items
- [x] `priority-low` (gray) - Low priority items
- [x] `frontend` (blue) - Frontend related
- [x] `backend` (dark blue) - Backend related
- [x] `qdrant` (red) - Qdrant/Vector DB related
- [x] `docker` (blue) - Docker/Deployment related
- [x] Default labels (bug, enhancement, etc.)

### Documentation Files
- [x] `CONTRIBUTING.md` - Contribution guidelines with:
  - Code of conduct
  - Development setup instructions
  - Branch naming conventions
  - PR process
  - Coding standards (TypeScript/React and Python/FastAPI)
  - Commit message format (conventional commits)

- [x] `CHANGELOG.md` - Version history following Keep a Changelog format

- [x] `ROADMAP.md` - Development roadmap with:
  - v0.1.0 (current MVP)
  - v0.2.0 (production readiness)
  - v0.3.0 (collaboration & mobile)
  - v0.4.0 (AI enhancements)
  - v1.0.0 (stable release)

- [x] `SECURITY.md` - Security policy with:
  - Supported versions
  - Vulnerability reporting process
  - Response timeline
  - Disclosure policy
  - Security best practices

- [x] `LICENSE` - MIT License

- [x] `CODEOWNERS` - Code review assignments (all files → @ghively)

- [x] `FUNDING.yml` - Funding/sponsorship template (commented out)

### Initial Issues Created
- [x] **#7** - [TASK] Set up authentication system
- [x] **#8** - [TASK] Add comprehensive test suite
- [x] **#12** - [FEATURE] Add collaborative editing support
- [x] **#14** - [FEATURE] Mobile app / PWA support

---

## ⏳ Remaining Setup (Manual)

The following items require manual configuration through the GitHub web interface:

### 1. Branch Protection Rules
**Location:** Settings → Branches → Add rule

Configure for `main` branch:
- [ ] **Require a pull request before merging**
  - Require approvals: 1
  - Dismiss stale PR approvals when new commits are pushed
  - Require review from Code Owners

- [ ] **Require status checks to pass**
  - Require branches to be up to date before merging
  - Status checks:
    - `Frontend Checks`
    - `Backend Checks`
    - `Docker Build Test`

- [ ] **Require conversation resolution before merging**

- [ ] **Require signed commits** (optional, recommended)

- [ ] **Include administrators** (optional)

- [ ] **Restrict pushes that create files larger than 100MB**

### 2. GitHub Project Board
**Location:** Projects → New project

- [ ] Create a project board named "Knowledge OS Development"
- [ ] Add columns:
  - Backlog
  - Todo
  - In Progress
  - In Review
  - Done
- [ ] Link existing issues to the board
- [ ] Set up automation:
  - Auto-move PRs to "In Review" when opened
  - Auto-move issues to "Done" when closed

### 3. Repository Secrets
**Location:** Settings → Secrets and variables → Actions

Add the following secrets if needed:
- [ ] `DOCKER_USERNAME` - For Docker Hub pushes (if not using GHCR)
- [ ] `DOCKER_PASSWORD` - Docker Hub password/token
- [ ] `DEPLOY_KEY` - For deployment to servers
- [ ] Any external API keys (OpenAI, etc.)

### 4. GitHub Discussions
**Location:** Settings → Discussions

- [ ] Enable Discussions
- [ ] Create categories:
  - General
  - Q&A
  - Ideas
  - Show and tell

### 5. Wiki (Optional)
**Location:** Settings → Wikis

- [ ] Enable Wikis if you want community documentation
- [ ] Or disable if using external docs

### 6. Repository Topics
**Location:** About section on main page

Add topics to help with discoverability:
- [ ] `knowledge-management`
- [ ] `note-taking`
- [ ] `qdrant`
- [ ] `vector-database`
- [ ] `ai-agents`
- [ ] `openclaw`
- [ ] `semantic-search`
- [ ] `react`
- [ ] `fastapi`
- [ ] `docker`

### 7. Social Preview
**Location:** Settings → Social preview

- [ ] Upload a social preview image (1280×640px)
- [ ] This appears when sharing on social media

### 8. Releases
**Location:** Releases → Create a new release

- [ ] Create initial v0.1.0 release
- [ ] Tag: `v0.1.0`
- [ ] Title: "Knowledge OS v0.1.0 - MVP Release"
- [ ] Description: Link to CHANGELOG.md
- [ ] Attach binaries (optional)

### 9. GitHub Pages (Optional)
**Location:** Settings → Pages

If you want to host documentation:
- [ ] Enable GitHub Pages
- [ ] Source: Deploy from a branch → `gh-pages`
- [ ] Or use GitHub Actions for custom deployment

### 10. Code Scanning
**Location:** Security → Code scanning

- [ ] Enable CodeQL analysis
- [ ] Enable dependency review
- [ ] Configure secret scanning (if available)

### 11. Environment Protection (Optional)
**Location:** Settings → Environments

If deploying to production:
- [ ] Create `production` environment
- [ ] Add protection rules:
  - Required reviewers
  - Wait timer
  - Deployment branches

### 12. Notification Settings
**Location:** Settings → Notifications

- [ ] Configure notification preferences
- [ ] Set up email notifications for:
  - Issues
  - Pull requests
  - Discussions
  - Actions

---

## 🔧 Customization Tips

### Update CODEOWNERS
As the project grows, update `.github/CODEOWNERS`:
```
# Frontend team
/frontend/ @frontend-lead @ghively

# Backend team
/backend/ @backend-lead @ghively

# DevOps
/docker-compose.yml @devops-lead
/.github/workflows/ @devops-lead
```

### Update FUNDING.yml
If you want to accept sponsorships:
```yaml
github: [ghively]
patreon: your-patreon-username
ko_fi: your-kofi-username
```

### Customize Issue Templates
Edit files in `.github/ISSUE_TEMPLATE/` to match your workflow.

### Add More Workflows
Consider adding:
- Nightly builds
- Performance benchmarking
- Dependency vulnerability scanning
- Automated deployment

---

## 📚 Useful Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [About Issue Templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates)
- [Managing Security Alerts](https://docs.github.com/en/code-security/getting-started/managing-security-alerts)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

---

## 🚀 Quick Start for New Contributors

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/knowledge-os.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make changes following [CONTRIBUTING.md](CONTRIBUTING.md)
5. Push and create a PR

The CI will automatically run checks on your PR!
