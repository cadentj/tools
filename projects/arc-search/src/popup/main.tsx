import { render } from "preact";
import { StrictMode } from "preact/compat";
import "./popup.css";
import { App } from "./App";

const root = document.getElementById("root");
if (!root) throw new Error("Missing #root");

render(
  <StrictMode>
    <App />
  </StrictMode>,
  root,
);
