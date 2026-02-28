# Git Conventions

## Commits

- Always use atomic commits
- **Author**: spideystreet <dhicham.pro@gmail.com>
- **Co-Author**: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>

Always include in every commit message:
```
Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
```

Commit format:
```
git commit -m "$(cat <<'EOF'
<type>(<scope>): <imperative summary>

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
Scopes: `agent`, `pipeline`, `dbt`, `eval`, `ci`

## Pull Requests

- **Author**: spicode-bot — **Reviewer**: spideystreet (always assign)
- Never develop on `main` — always create a feature branch first
- PR title follows the same `<type>(<scope>): <summary>` convention
