import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="border-b border-slate-200 bg-slate-900 text-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <Link href="/" className="flex items-center space-x-3">
            <span className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-sky-400 animate-pulse"></span>
              ProductionReady
            </span>
            <span className="text-xs bg-slate-800 text-sky-400 px-2 py-0.5 rounded font-mono border border-slate-700">
              v0.2.0
            </span>
          </Link>
          <div className="hidden md:flex space-x-4 text-sm font-medium text-slate-300">
            <Link href="/" className="hover:text-white transition-colors">
              Projects
            </Link>
            <a
              href="https://asvs.owasp.org/"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white transition-colors"
            >
              OWASP ASVS 5.0
            </a>
          </div>
        </div>
        <div className="flex items-center space-x-3 text-xs">
          <span className="hidden sm:inline-block px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
            Zero Code Retention &middot; Ephemeral Sandboxes
          </span>
        </div>
      </div>
    </nav>
  );
}
