"use client";

import { Sidebar, TopBar } from "@/components/Layout";
import { hasClientSession } from "@/lib/services";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const pageTitles: Record<string, { title: string; subtitle?: string }> = {
	"/dashboard": {
		title: "Dashboard",
		subtitle: "Your pricing command center",
	},
	"/skus": { title: "SKU Manager", subtitle: "Manage all your products" },
	"/portfolio": {
		title: "Portfolio Analytics",
		subtitle: "Visual overview of your catalog",
	},
	"/inventory": {
		title: "Inventory Planner",
		subtitle: "Stock levels & reorder suggestions",
	},
	"/festivals": {
		title: "Festival Planner",
		subtitle: "Capitalize on upcoming sales events",
	},
	"/competitors": {
		title: "Competitor Intelligence",
		subtitle: "Track and respond to market moves",
	},
	"/settings": { title: "Settings", subtitle: "Configure your preferences" },
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
	const router = useRouter();
	const pathname = usePathname();
	const [isCheckingAuth, setIsCheckingAuth] = useState(true);

	useEffect(() => {
		if (!hasClientSession()) {
			router.replace("/login");
			return;
		}
		setIsCheckingAuth(false);
	}, [router]);

	if (isCheckingAuth) {
		return null;
	}

	const base = "/" + pathname.split("/")[1];
	const meta = pageTitles[base] ?? { title: "PriceIQ" };

	return (
		<div className="flex min-h-screen bg-slate-50">
			<Sidebar />
			<div className="flex-1 flex flex-col min-w-0">
				<TopBar title={meta.title} subtitle={meta.subtitle} />
				<main className="flex-1 p-6 overflow-auto">{children}</main>
			</div>
		</div>
	);
}
