import { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';

const Header = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchQuery('');
    }
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `relative px-3 py-2 text-sm font-medium transition-colors duration-200 ${isActive
      ? 'text-gold'
      : 'text-charcoal-light hover:text-gold'
    } after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-full after:origin-left after:scale-x-0 after:bg-gold after:transition-transform after:duration-300 hover:after:scale-x-100 ${isActive ? 'after:scale-x-100' : ''
    }`;

  return (
    <header className="sticky top-0 z-50 border-b border-bronze/20 bg-ivory/95 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link
            to="/"
            className="group flex items-center gap-3 transition-transform duration-200 hover:scale-[1.02]"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-gold to-gold-dark shadow-md">
              <svg
                className="h-6 w-6 text-ivory"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418"
                />
              </svg>
            </div>
            <div className="flex flex-col">
              <span className="font-heading text-xl font-bold tracking-wide text-charcoal">
                ArP
              </span>
              <span className="text-[10px] font-medium uppercase tracking-widest text-bronze">
                Artwork Provenance
              </span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:block">
            <ul className="flex items-center gap-1">
              <li>
                <NavLink to="/" className={navLinkClass} end>
                  Home
                </NavLink>
              </li>
              <li>
                <NavLink to="/artworks" className={navLinkClass}>
                  Collection
                </NavLink>
              </li>
              <li>
                <NavLink to="/sparql" className={navLinkClass}>
                  SPARQL Explorer
                </NavLink>
              </li>
              <li>
                <NavLink to="/about" className={navLinkClass}>
                  About
                </NavLink>
              </li>
            </ul>
          </nav>

          {/* Search & Mobile Menu */}
          <div className="flex items-center gap-4">
            {/* Quick Search Bar */}
            <form onSubmit={handleSearch} className="relative hidden sm:block">
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-48 rounded-full border border-bronze/20 bg-ivory/50 px-4 py-1.5 pl-9 text-sm text-charcoal placeholder:text-bronze/50 focus:border-gold focus:bg-ivory focus:outline-none focus:ring-1 focus:ring-gold transition-all"
              />
              <svg
                className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-charcoal-light"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                />
              </svg>
            </form>

            {/* Mobile Search Icon (visible only on small screens) */}
            <Link
              to="/search"
              className="flex h-9 w-9 items-center justify-center rounded-full text-charcoal-light transition-colors hover:bg-parchment-dark hover:text-charcoal sm:hidden"
              aria-label="Search"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                />
              </svg>
            </Link>

            {/* Mobile menu button */}
            <button
              className="flex h-9 w-9 items-center justify-center rounded-lg text-charcoal-light transition-colors hover:bg-parchment-dark hover:text-charcoal md:hidden"
              aria-label="Open menu"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;

