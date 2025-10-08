import { BrowserRouter, Routes, Route } from "react-router-dom";
// import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
// import Analytics from "./pages/Analytics";
// import Settings from "./pages/Settings";

function App() {
	return (
		<BrowserRouter>
			{/* <Layout> */}
			<Routes>
				<Route index element={<Dashboard />} />
				{/* <Route path="analytics" element={<Analytics />} /> */}
				{/* <Route path="settings" element={<Settings />} /> */}
			</Routes>
			{/* </Layout> */}
		</BrowserRouter>
	);
}

export default App;
