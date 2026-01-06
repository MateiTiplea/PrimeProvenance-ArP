import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { artworkApi, type Artwork } from '../services/api';
import { ArtworkCard, ArtworkCardSkeleton } from '../components';

const HomePage = () => {
  const [featuredArtworks, setFeaturedArtworks] = useState<Artwork[]>([]);
  const [loadingFeatured, setLoadingFeatured] = useState(true);

  useEffect(() => {
    const fetchFeaturedArtworks = async () => {
      try {
        const response = await artworkApi.getAll({ limit: 6 });
        // Backend now properly deduplicates by preferring English titles
        setFeaturedArtworks(response.data.items);
      } catch (err) {
        console.error('Failed to fetch featured artworks:', err);
      } finally {
        setLoadingFeatured(false);
      }
    };

    fetchFeaturedArtworks();
  }, []);

  return (
    <div className="relative">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-charcoal via-charcoal to-burgundy-dark">
        {/* Decorative pattern overlay */}
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23c9a227' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
        
        <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8 lg:py-40">
          <div className="max-w-3xl">
            <h1 className="font-heading text-4xl font-bold tracking-tight text-ivory sm:text-5xl lg:text-6xl">
              Discover the{' '}
              <span className="bg-gradient-to-r from-gold to-gold-light bg-clip-text text-transparent">
                Provenance
              </span>{' '}
              of Art
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-parchment/80 sm:text-xl">
              Explore the rich histories behind masterpieces. ArP brings together 
              semantic web technologies to trace artwork ownership, authenticity, 
              and cultural significance through linked data.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <Link
                to="/artworks"
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-gold to-gold-dark px-6 py-3 font-medium text-charcoal shadow-lg shadow-gold/25 transition-all hover:shadow-xl hover:shadow-gold/30 hover:scale-[1.02]"
              >
                Browse Collection
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </Link>
              <Link
                to="/sparql"
                className="inline-flex items-center gap-2 rounded-lg border border-parchment/30 px-6 py-3 font-medium text-parchment transition-all hover:border-gold hover:text-gold"
              >
                SPARQL Explorer
              </Link>
            </div>
          </div>
        </div>

        {/* Decorative gradient fade */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-parchment to-transparent" />
      </section>

      {/* Featured Artworks Section */}
      <section className="bg-parchment py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-heading text-3xl font-bold text-charcoal">
                Featured Artworks
              </h2>
              <p className="mt-2 text-charcoal-light">
                Discover masterpieces with rich provenance histories
              </p>
            </div>
            <Link
              to="/artworks"
              className="hidden sm:inline-flex items-center gap-2 text-gold hover:text-gold-dark transition-colors"
            >
              View all
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
          </div>

          {/* Featured Grid */}
          <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {loadingFeatured ? (
              <>
                <ArtworkCardSkeleton />
                <ArtworkCardSkeleton />
                <ArtworkCardSkeleton />
                <ArtworkCardSkeleton />
                <ArtworkCardSkeleton />
                <ArtworkCardSkeleton />
              </>
            ) : featuredArtworks.length > 0 ? (
              featuredArtworks.slice(0, 6).map((artwork) => (
                <ArtworkCard key={artwork.id} artwork={artwork} />
              ))
            ) : (
              <div className="col-span-full py-12 text-center">
                <p className="text-charcoal-light">No artworks available yet.</p>
              </div>
            )}
          </div>

          {/* Mobile view all link */}
          <div className="mt-8 text-center sm:hidden">
            <Link
              to="/artworks"
              className="inline-flex items-center gap-2 text-gold hover:text-gold-dark transition-colors"
            >
              View all artworks
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-ivory py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="font-heading text-3xl font-bold text-charcoal sm:text-4xl">
              Powered by Linked Data
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-charcoal-light">
              ArP leverages the semantic web to connect artwork data across multiple knowledge bases.
            </p>
          </div>

          <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="group rounded-2xl border border-bronze/20 bg-parchment p-8 shadow-sm transition-all hover:border-gold/40 hover:shadow-md">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-burgundy to-burgundy-dark text-ivory">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="mt-6 font-heading text-xl font-semibold text-charcoal">
                Provenance Tracking
              </h3>
              <p className="mt-3 text-charcoal-light">
                Follow the complete ownership history of artworks from creation to present day.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="group rounded-2xl border border-bronze/20 bg-parchment p-8 shadow-sm transition-all hover:border-gold/40 hover:shadow-md">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-gold to-gold-dark text-charcoal">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
              <h3 className="mt-6 font-heading text-xl font-semibold text-charcoal">
                Linked Data Integration
              </h3>
              <p className="mt-3 text-charcoal-light">
                Connected to DBpedia, Wikidata, and Getty vocabularies for rich contextual information.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="group rounded-2xl border border-bronze/20 bg-parchment p-8 shadow-sm transition-all hover:border-gold/40 hover:shadow-md">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-bronze to-bronze-light text-ivory">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="mt-6 font-heading text-xl font-semibold text-charcoal">
                SPARQL Queries
              </h3>
              <p className="mt-3 text-charcoal-light">
                Execute custom SPARQL queries to explore artwork data with our interactive interface.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="group rounded-2xl border border-bronze/20 bg-parchment p-8 shadow-sm transition-all hover:border-gold/40 hover:shadow-md">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-charcoal to-charcoal-light text-gold">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                </svg>
              </div>
              <h3 className="mt-6 font-heading text-xl font-semibold text-charcoal">
                QR Code Sharing
              </h3>
              <p className="mt-3 text-charcoal-light">
                Generate QR codes for easy sharing of artwork information and provenance data.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="group rounded-2xl border border-bronze/20 bg-parchment p-8 shadow-sm transition-all hover:border-gold/40 hover:shadow-md">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-burgundy to-burgundy-dark text-ivory">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="mt-6 font-heading text-xl font-semibold text-charcoal">
                RDFa Markup
              </h3>
              <p className="mt-3 text-charcoal-light">
                Semantic HTML with Schema.org and RDFa for enhanced machine-readability.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="group rounded-2xl border border-bronze/20 bg-parchment p-8 shadow-sm transition-all hover:border-gold/40 hover:shadow-md">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-gold to-gold-dark text-charcoal">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="mt-6 font-heading text-xl font-semibold text-charcoal">
                Smart Search
              </h3>
              <p className="mt-3 text-charcoal-light">
                Find artworks by artist, period, medium, or location with intelligent recommendations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Data Sources Section */}
      <section className="border-t border-bronze/20 bg-parchment py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h3 className="text-center font-heading text-lg font-medium text-charcoal-light">
            Integrated Knowledge Sources
          </h3>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-8 opacity-70 grayscale transition-all hover:opacity-100 hover:grayscale-0">
            <a href="https://dbpedia.org" target="_blank" rel="noopener noreferrer" className="text-xl font-heading font-semibold text-charcoal hover:text-gold transition-colors">
              DBpedia
            </a>
            <span className="text-bronze">•</span>
            <a href="https://www.wikidata.org" target="_blank" rel="noopener noreferrer" className="text-xl font-heading font-semibold text-charcoal hover:text-gold transition-colors">
              Wikidata
            </a>
            <span className="text-bronze">•</span>
            <a href="https://vocab.getty.edu" target="_blank" rel="noopener noreferrer" className="text-xl font-heading font-semibold text-charcoal hover:text-gold transition-colors">
              Getty Vocabularies
            </a>
            <span className="text-bronze">•</span>
            <a href="https://www.europeana.eu" target="_blank" rel="noopener noreferrer" className="text-xl font-heading font-semibold text-charcoal hover:text-gold transition-colors">
              Europeana
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
