import Link from "next/link";

export const REPO_URL = "https://github.com/ne-he/suara-rakyat";

const LINKS = [
  { href: "/#coba", label: "Coba" },
  { href: "/massal", label: "Massal" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/kuesioner", label: "Kuesioner" },
];

/** Header halaman dalam (dashboard, massal, kuesioner). Halaman depan punya header sendiri di atas cerita scroll. */
export default function SiteHeader({ active }: { active?: string }) {
  return (
    <header className="sticky top-0 z-30 border-b-2 border-aspal bg-aspal px-5 text-putih sm:px-10">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4">
        <Link href="/" className="display flex shrink-0 items-center gap-2 text-2xl">
          <span className="inline-block h-4 w-6 border border-putih/80 bg-[linear-gradient(to_bottom,var(--merah)_50%,#fff_50%)]" aria-hidden />
          <span className="hidden sm:inline">Suara Rakyat</span>
          <span className="sm:hidden">SR</span>
        </Link>
        <nav className="flex items-center gap-3 overflow-x-auto text-sm sm:gap-6">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              aria-current={active === l.href ? "page" : undefined}
              className={`whitespace-nowrap border-b-2 py-1 transition-colors ${
                active === l.href ? "border-merah text-white" : "border-transparent text-putih/75 hover:text-white"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter({ version }: { version?: string }) {
  return (
    <>
      <div className="bendera" />
      <footer className="px-5 py-6 text-xs text-abu sm:px-10">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span>Suara Rakyat {version} · projek AOL Software Engineering</span>
          <nav className="flex flex-wrap gap-x-4 gap-y-1">
            {LINKS.map((l) => (
              <Link key={l.href} href={l.href} className="hover:text-aspal">
                {l.label}
              </Link>
            ))}
            <a href={REPO_URL} target="_blank" rel="noreferrer" className="hover:text-aspal">
              Kode
            </a>
          </nav>
          <span>Hasil model bukan penilaian resmi instansi mana pun.</span>
        </div>
      </footer>
    </>
  );
}
