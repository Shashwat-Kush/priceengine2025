"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Eye, EyeOff, TrendingUp } from "lucide-react";

import { registerUser } from "@/lib/services";

export default function RegisterPage() {
	const router = useRouter();
	const [organizationName, setOrganizationName] = useState("");
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");
	const [showPassword, setShowPassword] = useState(false);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");

	const handleRegister = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!organizationName || !email || !password || !confirmPassword) {
			setError("Please fill in all fields.");
			return;
		}

		if (password.length < 6) {
			setError("Password must be at least 6 characters.");
			return;
		}

		if (password !== confirmPassword) {
			setError("Passwords do not match.");
			return;
		}

		setError("");
		setLoading(true);
		try {
			await registerUser(email, password, organizationName);
			router.push("/dashboard");
		} catch (err) {
			if (err instanceof Error && err.message.includes("409")) {
				setError("An account with this email already exists.");
			} else {
				setError("Unable to create account. Please try again.");
			}
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-blue-950 flex items-center justify-center p-4">
			<div className="w-full max-w-md">
				<div className="flex flex-col items-center mb-8">
					<div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center mb-3 shadow-lg">
						<TrendingUp size={24} className="text-white" />
					</div>
					<h1 className="text-2xl font-bold text-white">PriceIQ</h1>
					<p className="text-slate-400 text-sm mt-1">
						Create your organization workspace
					</p>
				</div>

				<div className="bg-white rounded-2xl shadow-xl p-8">
					<h2 className="text-xl font-bold text-slate-800 mb-1">
						Create account
					</h2>
					<p className="text-sm text-slate-500 mb-6">
						Start managing pricing and inventory intelligence
					</p>

					{error && (
						<div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-4 border border-red-200">
							{error}
						</div>
					)}

					<form onSubmit={handleRegister} className="space-y-4">
						<div>
							<label className="block text-sm font-medium text-slate-700 mb-1.5">
								Organization Name
							</label>
							<input
								type="text"
								value={organizationName}
								onChange={(e) =>
									setOrganizationName(e.target.value)
								}
								placeholder="Your Brand Pvt Ltd"
								className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
							/>
						</div>

						<div>
							<label className="block text-sm font-medium text-slate-700 mb-1.5">
								Email address
							</label>
							<input
								type="email"
								value={email}
								onChange={(e) => setEmail(e.target.value)}
								placeholder="you@yourshop.in"
								className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
							/>
						</div>

						<div>
							<label className="block text-sm font-medium text-slate-700 mb-1.5">
								Password
							</label>
							<div className="relative">
								<input
									type={showPassword ? "text" : "password"}
									value={password}
									onChange={(e) =>
										setPassword(e.target.value)
									}
									placeholder="At least 6 characters"
									className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors pr-10"
								/>
								<button
									type="button"
									onClick={() => setShowPassword((v) => !v)}
									className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
								>
									{showPassword ? (
										<EyeOff size={16} />
									) : (
										<Eye size={16} />
									)}
								</button>
							</div>
						</div>

						<div>
							<label className="block text-sm font-medium text-slate-700 mb-1.5">
								Confirm Password
							</label>
							<input
								type={showPassword ? "text" : "password"}
								value={confirmPassword}
								onChange={(e) =>
									setConfirmPassword(e.target.value)
								}
								placeholder="Re-enter your password"
								className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
							/>
						</div>

						<button
							type="submit"
							disabled={loading}
							className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-2.5 rounded-lg transition-colors text-sm mt-2"
						>
							{loading ? "Creating account..." : "Create Account"}
						</button>
					</form>

					<p className="text-center text-sm text-slate-500 mt-6">
						Already have an account?{" "}
						<Link
							href="/login"
							className="text-blue-600 font-medium hover:underline"
						>
							Sign in
						</Link>
					</p>
				</div>
			</div>
		</div>
	);
}
