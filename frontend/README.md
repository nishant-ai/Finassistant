# Financial Assistant UI

A modern, ChatGPT/Gemini-style React interface for the Financial Assistant API.

## Features

- **Dual Mode Interface**: Switch seamlessly between Chat and Report modes
- **Chat Mode**: Quick, conversational financial queries with fast responses
- **Report Mode**: Comprehensive financial analysis with detailed reports and export functionality
- **Modern UI**: Dark theme with gradient accents, inspired by ChatGPT and Google Gemini
- **Markdown Support**: Rich text formatting for financial data, tables, and code
- **Real-time API Status**: Visual indicators for API connectivity
- **Responsive Design**: Works great on desktop and mobile devices

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create environment file (optional):
```bash
cp .env.example .env
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/         # React components
│   │   ├── Header.jsx      # App header with mode switcher
│   │   ├── ChatMode.jsx    # Chat mode container
│   │   ├── ReportMode.jsx  # Report mode with export
│   │   ├── MessageList.jsx # Message display container
│   │   ├── Message.jsx     # Individual message component
│   │   └── InputBox.jsx    # Message input field
│   ├── services/           # API integration
│   │   └── api.js          # API client and methods
│   ├── styles/             # Global styles
│   │   └── index.css       # Tailwind and custom CSS
│   ├── App.jsx             # Main app component
│   └── main.jsx            # App entry point
├── index.html              # HTML template
├── package.json            # Dependencies and scripts
├── vite.config.js          # Vite configuration
└── tailwind.config.js      # Tailwind CSS configuration
```

## Usage

### Chat Mode

1. Click the "Chat" button in the header
2. Type your financial question in the input box
3. Press Enter or click Send
4. Get quick, conversational responses

Example queries:
- "What is Apple's P/E ratio?"
- "What's Tesla's current stock price?"
- "Compare Microsoft and Google"

### Report Mode

1. Click the "Report" button in the header
2. Type your analysis request
3. Press Enter or click Send
4. Get detailed, comprehensive financial reports
5. Click "Export Report" to download as Markdown

Example queries:
- "Analyze Tesla's financial health"
- "Provide a comprehensive analysis of Apple's Q4 performance"
- "Compare the financial metrics of top 5 tech companies"

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000` by default.

Endpoints used:
- `GET /api/health` - Health check
- `POST /api/chat` - Quick chat queries
- `POST /api/report` - Detailed report generation

## Customization

### Changing Colors

Edit [tailwind.config.js](tailwind.config.js) to customize the color scheme:

```javascript
theme: {
  extend: {
    colors: {
      'chat-bg': '#212121',
      'accent-blue': '#8ab4f8',
      // ... add your colors
    }
  }
}
```

### API URL

Set the API URL in `.env`:
```
VITE_API_URL=http://your-api-url:8000
```

## Technologies Used

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client
- **React Markdown** - Markdown rendering
- **Lucide React** - Icon library

## License

Part of the Financial Assistant project.
