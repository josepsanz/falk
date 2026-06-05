import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import { SettingsProvider } from "./settings";
import "./index.css";

const REFRESH_MS = 60_000;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      retry: 1,
      // Refresh the whole dashboard automatically every minute.
      refetchInterval: REFRESH_MS,
      refetchOnWindowFocus: true,
    },
  },
});

const container = document.getElementById("root");
if (!container) {
  throw new Error("missing #root element");
}

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <SettingsProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </SettingsProvider>
    </QueryClientProvider>
  </StrictMode>,
);
