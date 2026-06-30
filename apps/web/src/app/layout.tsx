import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "meizhaiseek",
  description: "电商 AI 智能分析平台"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
