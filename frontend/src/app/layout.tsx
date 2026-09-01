import type { Metadata } from"next";
import { Plus_Jakarta_Sans } from"next/font/google";
import"./globals.css";

const plusJakartaSans = Plus_Jakarta_Sans({
 subsets: ["latin"],
 weight: ["300","400","500","600","700"],
 variable:"--font-plus-jakarta-sans",
 display:"swap",
});

export const metadata: Metadata = {
 title:"SalesOS",
 description:"AI-assisted outbound, with human approval.",
};

export default function RootLayout({
 children,
}: Readonly<{ children: React.ReactNode }>) {
 return (
 <html lang="en"className={plusJakartaSans.variable}>
 <body className="antialiased">{children}</body>
 </html>
 );
}
