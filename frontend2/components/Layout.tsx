"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import clsx from "clsx";
import {
	LayoutDashboard,
	Package,
	BarChart3,
	Warehouse,
	CalendarDays,
	Users,
	Settings,
	TrendingUp,
	LogOut,
	ChevronDown,
	Bell,
} from "lucide-react";
import { useState } from "react";

const navItems = [
	{ href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
	{ href: "/skus", label: "SKU Manager", icon: Package },
	{ href: "/portfolio", label: "Portfolio", icon: BarChart3 },
	{ href: "/inventory", label: "Inventory", icon: Warehouse },
	{ href: "/festivals", label: "Festival Planner", icon: CalendarDays },
	{ href: "/competitors", label: "Competitors", icon: Users },
	{ href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
	const pathname = usePathname();
	return (
		<aside className="w-60 shrink-0 bg-slate-900 text-white flex flex-col min-h-screen">
			<div className="px-6 py-5 border-b border-slate-700">
				<div className="flex items-center gap-2.5">
					<div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
						<TrendingUp size={16} />
					</div>
					<div>
						<p className="font-bold text-sm leading-tight">
							PriceIQ
						</p>
						<p className="text-xs text-slate-400">
							AI Pricing Engine
						</p>
					</div>
				</div>
			</div>

			<nav className="flex-1 px-3 py-4 space-y-0.5">
				{navItems.map(({ href, label, icon: Icon }) => {
					const active =
						pathname === href ||
						(href !== "/dashboard" && pathname.startsWith(href));
					return (
						<Link
							key={href}
							href={href}
							className={clsx(
								"flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
								active
									? "bg-blue-600 text-white"
									: "text-slate-400 hover:bg-slate-800 hover:text-white",
							)}
						>
							<Icon size={16} />
							{label}
						</Link>
					);
				})}
			</nav>

			<div className="px-3 py-4 border-t border-slate-700">
				<div className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-400 hover:bg-slate-800 cursor-pointer text-sm">
					<div className="w-7 h-7 rounded-full bg-blue-500 flex items-center justify-center text-white text-xs font-bold">
						RS
					</div>
					<div className="flex-1 min-w-0">
						<p className="text-white text-xs font-medium truncate">
							Ravi Sharma
						</p>
						<p className="text-slate-500 text-xs truncate">
							ravi@shop.in
						</p>
					</div>
				</div>
				<Link
					href="/login"
					className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white cursor-pointer text-sm mt-1 transition-colors"
				>
					<LogOut size={14} />
					Sign Out
				</Link>
			</div>
		</aside>
	);
}

export function TopBar({
	title,
	subtitle,
}: {
	title: string;
	subtitle?: string;
}) {
	const [showDropdown, setShowDropdown] = useState(false);
	return (
		<header className="h-16 bg-white border-b border-slate-200 flex items-center px-6 gap-4 shrink-0">
			<div className="flex-1">
				<h1 className="font-bold text-slate-800 text-base leading-tight">
					{title}
				</h1>
				{subtitle && (
					<p className="text-xs text-slate-500">{subtitle}</p>
				)}
			</div>
			<div className="flex items-center gap-3">
				<button className="relative p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors">
					<Bell size={18} />
					<span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
				</button>
				<div className="relative">
					<button
						onClick={() => setShowDropdown((v) => !v)}
						className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors"
					>
						<div className="w-7 h-7 rounded-full bg-blue-500 flex items-center justify-center text-white text-xs font-bold">
							RS
						</div>
						<span className="text-sm text-slate-700 font-medium">
							Ravi Sharma
						</span>
						<ChevronDown size={14} className="text-slate-400" />
					</button>
					{showDropdown && (
						<div className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border border-slate-200 py-1 w-40 z-50">
							<Link
								href="/settings"
								className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
							>
								Settings
							</Link>
							<hr className="my-1 border-slate-100" />
							<Link
								href="/login"
								className="block px-4 py-2 text-sm text-red-600 hover:bg-slate-50"
							>
								Sign Out
							</Link>
						</div>
					)}
				</div>
			</div>
		</header>
	);
}
