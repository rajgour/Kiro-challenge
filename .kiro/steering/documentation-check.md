---
inclusion: always
---

# Documentation Best Practices

When making changes to the codebase:

1. **Check existing documentation**: Before implementing features, review:
   - README.md for project overview
   - DEPLOYMENT.md for deployment details
   - API documentation in `backend/docs/`

2. **Update documentation**: After significant changes:
   - Update README.md if setup steps change
   - Update API docs if endpoints change
   - Add inline code comments for complex logic

3. **Regenerate API docs**: After modifying `backend/main.py`:
   ```bash
   python3 -m pdoc backend/main.py -o backend/docs
   ```

4. **Commit documentation**: Include documentation updates in commits
