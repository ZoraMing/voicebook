import type { NextConfig } from "next";

import { networkInterfaces } from "os";

const getLocalIps = () => {
  const ips: string[] = [];
  const nets = networkInterfaces();
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]!) {
      if (net.family === "IPv4" && !net.internal) {
        ips.push(net.address);
      }
    }
  }
  return ips;
};

const localIps = getLocalIps();
const allowedOrigins = ["127.0.0.1:3000", "localhost:3000", ...localIps.map((ip) => `${ip}:3000`)];

const nextConfig: NextConfig = {
  devIndicators: false,
  allowedDevOrigins: allowedOrigins,
};

export default nextConfig;
