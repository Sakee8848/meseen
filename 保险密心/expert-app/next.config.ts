import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone', // Docker 优化：生成独立运行包
};

export default nextConfig;

