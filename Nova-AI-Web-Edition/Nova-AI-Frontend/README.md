# Nova-AI-Frontend

Nova-AI-Frontend is a modern, responsive web interface designed for interacting with AI-powered chat assistants. It features a clean, customizable user experience with real-time streaming, markdown support, and authentication capabilities.

---

## 🚀 Features

*   **Real-time Interaction:** Smooth AI text streaming using custom hooks.
*   **Rich Content Support:** Markdown rendering with syntax highlighting for code blocks.
*   **Multimodal Input:** Support for image uploads and base64 processing.
*   **Theme Customization:** Seamless light and dark mode switching via CSS variables.
*   **Secure Routing:** Protected routes and authentication state management.
*   **State Management:** Efficient global state handling using `zustand`.

---

## 🛠️ Technology Stack

*   **Framework:** React 18
*   **Language:** TypeScript
*   **Styling:** Tailwind CSS (with PostCSS)
*   **State Management:** Zustand
*   **Routing:** React Router DOM
*   **API Client:** Axios
*   **UI/Animation:** Framer Motion, Radix UI, Lucide React
*   **Markdown/Code:** React Markdown, React Syntax Highlighter
*   **Build Tool:** Vite

---

## 📦 Project Structure

```text
src/
├── components/   # Reusable UI components
├── hooks/        # Custom React hooks (e.g., useStreamedText)
├── lib/          # API services and auth handlers
├── pages/        # Application views (Chat, Login, Register, etc.)
├── store/        # Zustand state stores
└── types/        # TypeScript interfaces
```

---

## ⚙️ Configuration

The project relies on environment variables for API integration. Ensure the following variable is defined in your `.env` file:

| Variable | Description |
| :--- | :--- |
| `VITE_API_BASE_URL` | The base URL of the backend API service |

---

## 🏗️ Getting Started

### Prerequisites
- Node.js (v18+)
- npm

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Nova-AI-Frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables (create a `.env` file):
   ```text
   VITE_API_BASE_URL=your_backend_api_url
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

5. Build for production:
   ```bash
   npm run build
   ```

---

## ☁️ Deployment
This project is configured for deployment on **Render**. The `render.yaml` file defines the build process and static path requirements (`./dist`).

---

## 📄 License
This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.