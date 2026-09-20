import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Copy Editing Assistant",
  description: "Ask an editorial question and get guidance.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>
        <nav>
          <Link href="/">Ask</Link>
          <Link href="/rules">Draft rules</Link>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
