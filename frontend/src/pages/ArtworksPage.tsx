import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { artworkApi, type Artwork, type ArtworkListResponse } from '../services/api';
import { ArtworkCard, ArtworkGridSkeleton, ErrorMessage } from '../components';

const ArtworksPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State
  const [artworks, setArtworks] = useState<Artwork[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  
  // Get filter values from URL params
  const parsedPage = parseInt(searchParams.get('page') || '1', 10);
  const page = Number.isNaN(parsedPage) || parsedPage < 1 ? 1 : parsedPage;
  const search = searchParams.get('search') || '';
  const period = searchParams.get('period') || '';
  const limit = 12;

  // Fetch artworks
  const fetchArtworks = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params: Record<string, unknown> = { page, limit };
      if (search) params.search = search;
      if (period) params.period = period;
      
      const response = await artworkApi.getAll(params as { page?: number; limit?: number; search?: string; artist?: string; period?: string });
      const data: ArtworkListResponse = response.data;
      
      // Backend now properly deduplicates by preferring English titles
      setArtworks(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to fetch artworks:', err);
      setError('Failed to load artworks. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [page, search, period, limit]);

  useEffect(() => {
    fetchArtworks();
  }, [fetchArtworks]);

  // Handle search input
  const handleSearchChange = (value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set('search', value);
    } else {
      newParams.delete('search');
    }
    newParams.set('page', '1'); // Reset to first page
    setSearchParams(newParams);
  };

  // Handle period filter
  const handlePeriodChange = (value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set('period', value);
    } else {
      newParams.delete('period');
    }
    newParams.set('page', '1'); // Reset to first page
    setSearchParams(newParams);
  };

  // Handle pagination
  const goToPage = (newPage: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', String(newPage));
    setSearchParams(newParams);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-parchment">
      {/* Page Header */}
      <div className="border-b border-bronze/20 bg-ivory">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <h1 className="font-heading text-3xl font-bold text-charcoal sm:text-4xl">
            Artwork Collection
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-charcoal-light">
            Explore our curated collection of artworks with detailed provenance information.
          </p>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="border-b border-bronze/10 bg-parchment-dark/50">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label htmlFor="search" className="text-sm font-medium text-charcoal-light">
                Search:
              </label>
              <input
                type="text"
                id="search"
                placeholder="Title or artist..."
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal placeholder:text-bronze focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              />
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="period" className="text-sm font-medium text-charcoal-light">
                Period:
              </label>
              <select
                id="period"
                value={period}
                onChange={(e) => handlePeriodChange(e.target.value)}
                className="rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              >
                <option value="">All Periods</option>
                <option value="Renaissance">Renaissance</option>
                <option value="Baroque">Baroque</option>
                <option value="Impressionism">Impressionism</option>
                <option value="Post-Impressionism">Post-Impressionism</option>
                <option value="Expressionism">Expressionism</option>
                <option value="Cubism">Cubism</option>
                <option value="Surrealism">Surrealism</option>
                <option value="Art Nouveau">Art Nouveau</option>
                <option value="Dutch Golden Age">Dutch Golden Age</option>
                <option value="Romanian">Romanian</option>
              </select>
            </div>
            {(search || period) && (
              <button
                onClick={() => {
                  setSearchParams(new URLSearchParams());
                }}
                className="text-sm text-burgundy hover:text-burgundy-dark transition-colors"
              >
                Clear filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        {/* Error State */}
        {error && (
          <ErrorMessage
            message={error}
            onRetry={fetchArtworks}
            className="mb-8"
          />
        )}

        {/* Loading State */}
        {loading && <ArtworkGridSkeleton count={limit} />}

        {/* Empty State */}
        {!loading && !error && artworks.length === 0 && (
          <div className="py-16 text-center">
            <svg
              className="mx-auto h-16 w-16 text-bronze"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <h3 className="mt-4 font-heading text-xl font-semibold text-charcoal">
              No artworks found
            </h3>
            <p className="mt-2 text-charcoal-light">
              {search || period
                ? 'Try adjusting your search or filters.'
                : 'Check back later for new additions to the collection.'}
            </p>
          </div>
        )}

        {/* Artworks Grid */}
        {!loading && !error && artworks.length > 0 && (
          <>
            {/* Results count */}
            <p className="mb-6 text-sm text-charcoal-light">
              Showing {(page - 1) * limit + 1}-{(page - 1) * limit + artworks.length} of {total} artworks
            </p>

            <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {artworks.map((artwork) => (
                <ArtworkCard key={artwork.id} artwork={artwork} />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-12 flex justify-center">
                <nav className="flex items-center gap-2">
                  <button
                    onClick={() => goToPage(page - 1)}
                    disabled={page <= 1}
                    className="rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal-light hover:border-gold hover:text-charcoal transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  
                  <div className="flex items-center gap-1">
                    {/* First page */}
                    {page > 2 && (
                      <>
                        <button
                          onClick={() => goToPage(1)}
                          className="rounded-lg px-3 py-2 text-sm text-charcoal-light hover:text-charcoal transition-colors"
                        >
                          1
                        </button>
                        {page > 3 && <span className="px-2 text-bronze">...</span>}
                      </>
                    )}
                    
                    {/* Previous page */}
                    {page > 1 && (
                      <button
                        onClick={() => goToPage(page - 1)}
                        className="rounded-lg px-3 py-2 text-sm text-charcoal-light hover:text-charcoal transition-colors"
                      >
                        {page - 1}
                      </button>
                    )}
                    
                    {/* Current page */}
                    <span className="rounded-lg bg-gold/20 px-3 py-2 text-sm font-medium text-gold">
                      {page}
                    </span>
                    
                    {/* Next page */}
                    {page < totalPages && (
                      <button
                        onClick={() => goToPage(page + 1)}
                        className="rounded-lg px-3 py-2 text-sm text-charcoal-light hover:text-charcoal transition-colors"
                      >
                        {page + 1}
                      </button>
                    )}
                    
                    {/* Last page */}
                    {page < totalPages - 1 && (
                      <>
                        {page < totalPages - 2 && <span className="px-2 text-bronze">...</span>}
                        <button
                          onClick={() => goToPage(totalPages)}
                          className="rounded-lg px-3 py-2 text-sm text-charcoal-light hover:text-charcoal transition-colors"
                        >
                          {totalPages}
                        </button>
                      </>
                    )}
                  </div>
                  
                  <button
                    onClick={() => goToPage(page + 1)}
                    disabled={page >= totalPages}
                    className="rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal-light hover:border-gold hover:text-charcoal transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </nav>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ArtworksPage;
