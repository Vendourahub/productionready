import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata = {
  title: "ProductionReady — Evidence-Backed Security & ASVS 5.0 Verification",
  description: "Deployment readiness verification for AI-built web applications.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
          <p>ProductionReady &copy; 2026 &middot; Evidence-Backed Verification Architecture &middot; Based on OWASP ASVS 5.0</p>
        </footer>
      </body>
    </html>
  );
}
