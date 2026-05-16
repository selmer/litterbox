# Litterbox Frontend

The frontend is a React/Vite app for the litterbox dashboard. Source files live under `frontend/src/`.

## Commands

- `npm ci`: install dependencies from the lockfile.
- `npm run dev`: start the Vite development server.
- `npm run lint`: run ESLint.
- `npm test`: run Vitest.
- `npm run build`: build production assets into `frontend/dist/`.

## Test Coverage

Current Vitest coverage includes selected page and component behavior:

- `frontend/src/pages/Visits.test.jsx`
- `frontend/src/pages/Cats.test.jsx`
- `frontend/src/components/WeightChart.test.jsx`
- `frontend/src/components/Toast.test.jsx`

Add tests beside the component or page as `*.test.jsx`.
