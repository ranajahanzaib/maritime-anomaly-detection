import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vessel Behavior Analysis Platform",
  description: "Maritime movement intelligence, route corridor deviation analysis, and contextual anomaly detection.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#06090e] text-slate-100 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
