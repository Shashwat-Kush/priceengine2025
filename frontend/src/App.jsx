import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";
import { ThemeProvider } from "./theme/ThemeContext";

function App() {
	return (
		<ThemeProvider>
			<BrowserRouter>
				<Layout>
					<Routes>
						<Route index element={<Dashboard />} />
						<Route path="analytics" element={<Analytics />} />
						<Route path="settings" element={<Settings />} />
					</Routes>
				</Layout>
			</BrowserRouter>
		</ThemeProvider>
	);
}

export default App;
