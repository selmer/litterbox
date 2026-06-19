# Litterbox Frontend

The frontend is a React/Vite app for the litterbox dashboard. Source files live under `frontend/src/`.

## Commands

- `npm ci`: install dependencies from the lockfile.
- `npm run dev`: start the Vite development server.
- `npm run lint`: run ESLint.
- `npm test`: run Vitest.
- `npm run build`: build production assets into `frontend/dist/`.

## Test Coverage

Vitest tests live beside the page or component they cover as `*.test.jsx`. Keep new frontend tests colocated with the code under test so related behavior stays easy to find.
