/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    domains: ["cdn.dsmcdn.com", "img.hepsiemlak.com", "imgr.emlakjet.com"],
  },
};

module.exports = nextConfig;
