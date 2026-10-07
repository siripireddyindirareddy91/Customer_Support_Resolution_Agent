import type { NextConfig } from "next";

const backendOrigin = process.env.BACKEND_API_ORIGIN ?? (process.env.VERCEL ? undefined : "http://localhost:8000");

if (!backendOrigin) {
	throw new Error("Set BACKEND_API_ORIGIN to the deployed FastAPI origin before building on Vercel.");
}

if (process.env.VERCEL && !backendOrigin.startsWith("https://")) {
	throw new Error("BACKEND_API_ORIGIN must use HTTPS on Vercel.");
}

const nextConfig: NextConfig = {
	async rewrites() {
		return [{ source: "/api/:path*", destination: `${backendOrigin}/api/:path*` }];
	},
};

export default nextConfig;