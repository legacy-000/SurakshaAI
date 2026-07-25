import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider, ThemeProvider, LangProvider } from "./context";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <LangProvider>
        <AuthProvider>
          {/* Catalyst client hosting has no SPA fallback — a deep link to
              /app/cases 404s. Hash routing keeps refresh and direct links
              working on static hosting. */}
          <HashRouter>
            <App />
          </HashRouter>
        </AuthProvider>
      </LangProvider>
    </ThemeProvider>
  </React.StrictMode>
);
