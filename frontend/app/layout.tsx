import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Parcelcare | Delivery support",
  description: "Order support grounded in verified delivery data and policy.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}