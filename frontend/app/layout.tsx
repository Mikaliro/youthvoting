import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CA Youth Voter Outreach",
  description: "California voting precinct analysis for youth voter outreach",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="h-full bg-gray-50">{children}</body>
    </html>
  );
}
