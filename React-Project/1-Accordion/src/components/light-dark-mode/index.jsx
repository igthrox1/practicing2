import useLocalStorage from "./useLocalStorage";
import './theme.css';

function LightDarkMode() {
  const [theme, settheme] = useLocalStorage("theme", "dark");
  function handleToggleTheme() {
    settheme(theme === "light" ? "dark" : "light");
  }

  console.log(theme);

  return (
    <div className="light-dark-mode" data-theme={theme}>
      <div className="container">
        <p>hello world</p>
        <button className="hi"onClick={handleToggleTheme}>Change Theme</button>
      </div>
    </div>
  );
}

export default LightDarkMode;
