# Contributing to FlowMetrics

Thanks for considering a contribution. Keep changes focused and explain the problem they solve.

## Before opening a pull request
1. Open an issue for significant changes so the scope can be discussed.
2. Keep credentials, local databases, and personal data out of commits.
3. Run the backend smoke test and frontend production build.
4. Include screenshots for visible UI changes and steps to reproduce bug fixes.

## Local checks
- Backend: `python -m unittest discover -s backend/tests -v`
- Frontend: `cd frontend && npm install && npm run build`

## Pull request checklist
- [ ] The change has a clear purpose.
- [ ] Existing role permissions still work.
- [ ] The Team Leader → Employee → Team Leader workflow was checked.
- [ ] No secrets, database files, or generated dependencies are included.
