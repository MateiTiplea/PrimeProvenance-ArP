import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';

// Placeholder search results
const placeholderResults = [
  {
    id: '1',
    title: 'The Starry Night',
    artist: 'Vincent van Gogh',
    dateCreated: '1889',
    medium: 'Oil on canvas',
    imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/200px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg',
  },
  {
    id: '2',
    title: 'Sunflowers',
    artist: 'Vincent van Gogh',
    dateCreated: '1888',
    medium: 'Oil on canvas',
    imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Vincent_Willem_van_Gogh_127.jpg/200px-Vincent_Willem_van_Gogh_127.jpg',
  },
];

const SearchPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<typeof placeholderResults | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    // Clear any pending timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    setIsSearching(true);
    // Simulate API call
    timeoutRef.current = setTimeout(() => {
      setResults(placeholderResults);
      setIsSearching(false);
    }, 500);
  };

  return (
    <div className="min-h-screen bg-parchment">
      {/* Search Header */}
      <div className="bg-gradient-to-br from-charcoal via-charcoal to-burgundy-dark">
        <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
          <h1 className="text-center font-heading text-3xl font-bold text-ivory sm:text-4xl">
            Search Artworks
          </h1>
          <p className="mt-4 text-center text-lg text-parchment/70">
            Find artworks by title, artist, period, or medium
          </p>

          {/* Search Form */}
          <form onSubmit={handleSearch} className="mt-8">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for artworks..."
                className="w-full rounded-xl border-0 bg-ivory/95 px-6 py-4 pl-14 text-lg text-charcoal shadow-lg placeholder:text-charcoal-light focus:outline-none focus:ring-2 focus:ring-gold"
              />
              <svg
                className="absolute left-5 top-1/2 h-6 w-6 -translate-y-1/2 text-charcoal-light"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <button
                type="submit"
                disabled={isSearching}
                className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg bg-gradient-to-r from-gold to-gold-dark px-6 py-2 font-medium text-charcoal shadow-md hover:shadow-lg transition-shadow disabled:opacity-50"
              >
                {isSearching ? 'Searching...' : 'Search'}
              </button>
            </div>
          </form>

          {/* Quick Filters */}
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            <button className="rounded-full border border-parchment/30 px-4 py-1 text-sm text-parchment/70 hover:border-gold hover:text-gold transition-colors">
              Renaissance
            </button>
            <button className="rounded-full border border-parchment/30 px-4 py-1 text-sm text-parchment/70 hover:border-gold hover:text-gold transition-colors">
              Impressionism
            </button>
            <button className="rounded-full border border-parchment/30 px-4 py-1 text-sm text-parchment/70 hover:border-gold hover:text-gold transition-colors">
              Modern
            </button>
            <button className="rounded-full border border-parchment/30 px-4 py-1 text-sm text-parchment/70 hover:border-gold hover:text-gold transition-colors">
              Oil Painting
            </button>
            <button className="rounded-full border border-parchment/30 px-4 py-1 text-sm text-parchment/70 hover:border-gold hover:text-gold transition-colors">
              Sculpture
            </button>
          </div>
        </div>
      </div>

      {/* Results Section */}
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        {results === null ? (
          // No search yet
          <div className="text-center py-16">
            <svg
              className="mx-auto h-16 w-16 text-bronze/50"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <h2 className="mt-6 font-heading text-xl font-semibold text-charcoal">
              Start Searching
            </h2>
            <p className="mt-2 text-charcoal-light">
              Enter a search term to find artworks in our collection
            </p>
          </div>
        ) : results.length === 0 ? (
          // No results
          <div className="text-center py-16">
            <svg
              className="mx-auto h-16 w-16 text-bronze/50"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h2 className="mt-6 font-heading text-xl font-semibold text-charcoal">
              No Results Found
            </h2>
            <p className="mt-2 text-charcoal-light">
              Try adjusting your search terms or filters
            </p>
          </div>
        ) : (
          // Show results
          <>
            <div className="mb-8 flex items-center justify-between">
              <p className="text-charcoal-light">
                Found <span className="font-medium text-charcoal">{results.length}</span> artworks
              </p>
              <select className="rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal focus:border-gold focus:outline-none">
                <option value="relevance">Sort by Relevance</option>
                <option value="date-desc">Date (Newest)</option>
                <option value="date-asc">Date (Oldest)</option>
                <option value="title">Title A-Z</option>
              </select>
            </div>

            <div className="space-y-4">
              {results.map((artwork) => (
                <Link
                  key={artwork.id}
                  to={`/artworks/${artwork.id}`}
                  className="group flex gap-6 rounded-2xl border border-bronze/20 bg-ivory p-4 shadow-sm transition-all hover:border-gold/40 hover:shadow-md"
                >
                  {/* Thumbnail */}
                  <div className="h-24 w-24 flex-shrink-0 overflow-hidden rounded-lg bg-parchment-dark">
                    <img
                      src={artwork.imageUrl}
                      alt={artwork.title}
                      className="h-full w-full object-cover transition-transform group-hover:scale-105"
                    />
                  </div>

                  {/* Info */}
                  <div className="flex-1">
                    <h3 className="font-heading text-lg font-semibold text-charcoal group-hover:text-gold transition-colors">
                      {artwork.title}
                    </h3>
                    <p className="mt-1 text-charcoal-light">{artwork.artist}</p>
                    <div className="mt-2 flex gap-4 text-sm text-bronze">
                      <span>{artwork.dateCreated}</span>
                      <span>•</span>
                      <span>{artwork.medium}</span>
                    </div>
                  </div>

                  {/* Arrow */}
                  <div className="flex items-center">
                    <svg
                      className="h-5 w-5 text-charcoal-light group-hover:text-gold transition-colors"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SearchPage;

