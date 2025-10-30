import { createContext, useContext, useEffect, useMemo, useState } from "react";

const ThemeContext = createContext({ theme: "dark", setTheme: () => {} });

export function ThemeProvider({ children }) {
	const [theme, setThemeState] = useState(() => {
		const saved =
			typeof window !== "undefined"
				? localStorage.getItem("theme")
				: null;
		if (saved === "light" || saved === "dark") return saved;
		const prefersDark =
			typeof window !== "undefined" &&
			window.matchMedia &&
			window.matchMedia("(prefers-color-scheme: dark)").matches;
		return prefersDark ? "dark" : "light";
	});

	const setTheme = (t) => {
		setThemeState(t);
		try {
			localStorage.setItem("theme", t);
		} catch {}
	};

	useEffect(() => {
		document.documentElement.setAttribute("data-theme", theme);
	}, [theme]);

	const value = useMemo(() => ({ theme, setTheme }), [theme]);
	return (
		<ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
	);
}

export function useTheme() {
	return useContext(ThemeContext);
}

export function ThemeToggle() {
	const { theme, setTheme } = useTheme();
	const isDark = theme === "dark";
	return (
		<button
			type="button"
			onClick={() => setTheme(isDark ? "light" : "dark")}
			className="theme-toggle"
			aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
			title={isDark ? "Switch to light mode" : "Switch to dark mode"}
			style={{
				background: "transparent",
				border: "1px solid var(--border-strong)",
				color: "var(--text-muted)",
				padding: "8px 12px",
				borderRadius: 8,
				cursor: "pointer",
				display: "inline-flex",
				alignItems: "center",
				gap: 8,
			}}
		>
			<span style={{ fontSize: 16 }}>{isDark ? "🌙" : "☀️"}</span>
			<span style={{ fontWeight: 600 }}>{isDark ? "Dark" : "Light"}</span>
		</button>
	);
}
