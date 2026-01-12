import { Link } from 'react-router-dom';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-bronze/20 bg-charcoal text-parchment">
      {/* Main Footer */}
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="lg:col-span-2">
            <Link to="/" className="inline-flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-gold to-gold-dark">
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
              <span className="font-heading text-xl font-bold text-ivory">
                ArP
              </span>
            </Link>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-parchment/70">
              Artwork Provenance (ArP) is a semantic web platform for exploring
              and managing the history and authenticity of artistic works,
              leveraging linked data from DBpedia, Wikidata, and Getty vocabularies.
            </p>
            <div className="mt-6 flex gap-4">
              <a
                href="https://github.com/MateiTiplea/PrimeProvenance-ArP"
                target="_blank"
                rel="noopener noreferrer"
                className="text-parchment/60 transition-colors hover:text-gold"
                aria-label="GitHub"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path
                    fillRule="evenodd"
                    d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                    clipRule="evenodd"
                  />
                </svg>
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-heading text-sm font-semibold uppercase tracking-wider text-gold">
              Explore
            </h3>
            <ul className="mt-4 space-y-2">
              <li>
                <Link
                  to="/artworks"
                  className="text-sm text-parchment/70 transition-colors hover:text-ivory"
                >
                  Artwork Collection
                </Link>
              </li>
              <li>
                <Link
                  to="/sparql"
                  className="text-sm text-parchment/70 transition-colors hover:text-ivory"
                >
                  SPARQL Explorer
                </Link>
              </li>
              <li>
                <Link
                  to="/search"
                  className="text-sm text-parchment/70 transition-colors hover:text-ivory"
                >
                  Search
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="font-heading text-sm font-semibold uppercase tracking-wider text-gold">
              Resources
            </h3>
            <ul className="mt-4 space-y-2">
              <li>
                <Link
                  to="/about"
                  className="text-sm text-parchment/70 transition-colors hover:text-ivory"
                >
                  About ArP
                </Link>
              </li>
              <li>
                <a
                  href="/docs/technical-report.html"
                  className="text-sm text-parchment/70 transition-colors hover:text-ivory"
                >
                  Technical Report
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/MateiTiplea/PrimeProvenance-ArP/tree/main?tab=readme-ov-file#toolbox-getting-started"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-parchment/70 transition-colors hover:text-ivory"
                >
                  User Guide
                </a>
              </li>
              <li>
                <a
                  href="http://localhost:8000/api/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-parchment/70 transition-colors hover:text-ivory"
                >
                  API Documentation
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-charcoal-light/30 bg-charcoal">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-2 text-xs text-parchment/50 sm:flex-row">
            <p>© {currentYear} ArP - Artwork Provenance. Open source under MIT License.</p>
            <p>
              Built with semantic web technologies •{' '}
              <a
                href="https://www.w3.org/RDF/"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors hover:text-gold"
              >
                RDF
              </a>
              {' • '}
              <a
                href="https://www.w3.org/TR/sparql11-query/"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors hover:text-gold"
              >
                SPARQL
              </a>
              {' • '}
              <a
                href="https://schema.org/"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors hover:text-gold"
              >
                Schema.org
              </a>
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

