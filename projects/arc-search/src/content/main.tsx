import { render } from "preact";
import styles from "./palette.css?inline";
import { Palette } from "./Palette";

const host = document.createElement("div");
host.id = "arc-search-root";
host.style.zIndex = "2147483647";
const shadow = host.attachShadow({ mode: "open" });
const style = document.createElement("style");
style.textContent = styles;
shadow.appendChild(style);
const mount = document.createElement("div");
shadow.appendChild(mount);
document.documentElement.appendChild(host);

render(<Palette />, mount);
