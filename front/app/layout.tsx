import type { Metadata } from "next";
import { Inter, Newsreader } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const newsreader = Newsreader({
  subsets: ["latin"],
  variable: "--font-serif",
  style: ['normal', 'italic'],
});

export const metadata: Metadata = {
  title: "VoiceBook Studio",
  description: "AI Audiobook Creation Studio",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${newsreader.variable} font-sans bg-book-bg text-book-text antialiased`}>
        {children}
      </body>
    </html>
  );
}
