import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner" // 引入新的通知组件

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "密心 · 专家监修系统",
  description: "AI驱动的专家隐性知识逆向工程工具",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        {children}
        <Toaster /> {/* 这里放置通知容器 */}
      </body>
    </html>
  );
}