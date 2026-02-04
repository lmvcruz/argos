# Lens Frontend

Modern React-based CI analytics and visualization dashboard for the Argos project.

## Features

- **CI Health Dashboard**: Real-time monitoring of CI pipeline health
- **Local vs CI Comparison**: Side-by-side comparison of test results
- **Flaky Test Detection**: Identify and analyze intermittent test failures
- **Failure Pattern Analysis**: Platform-specific failure detection and reproduction guides
- **WebSocket Support**: Real-time result streaming from backend

## Technology Stack

- **React 18**: Modern UI framework
- **TypeScript**: Type-safe development
- **Vite**: Lightning-fast build tool
- **Tailwind CSS**: Utility-first CSS
- **Recharts**: Beautiful charts and visualizations
- **Axios**: HTTP client for backend communication

## Getting Started

### Prerequisites

- Node.js >= 16
- npm >= 8

### Installation

```bash
cd lens/frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000` with proxy to backend at `http://localhost:8000`.

### Build

Create a production build:

```bash
npm run build
```

Preview the build:

```bash
npm run preview
```

## Backend Requirements

The Lens Frontend requires the Lens Backend server running:

```bash
# From the project root
python -m lens.backend.server:app
```

The backend will be available at `http://localhost:8000`.

## API Integration

The frontend communicates with the backend via:

- **REST API**: `/api/` endpoints for data queries and action execution
- **WebSocket**: `/ws` for real-time updates

See `src/api/client.ts` for the complete API client.

## Project Structure

```
src/
├── api/
│   └── client.ts           # Backend API integration
├── pages/
│   ├── CIDashboard.tsx     # CI health dashboard
│   ├── Comparison.tsx      # Local vs CI comparison
│   ├── FlakyTests.tsx      # Flaky test analysis
│   └── FailurePatterns.tsx # Platform-specific failures
├── App.tsx                 # Main app component
├── index.css               # Global styles
└── main.tsx                # Entry point

public/
└── lens-icon.svg           # App icon
```

## Code Quality

Format code:

```bash
npm run format
```

Lint code:

```bash
npm run lint
```

Type checking:

```bash
npm run type-check
```

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Open pull request

## License

Part of the Argos project - See LICENSE for details
