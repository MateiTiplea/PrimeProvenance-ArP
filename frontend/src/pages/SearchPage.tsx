import { useState, useEffect, useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  searchApi,
  type SearchResponse,
  type SearchFilters,
} from "../services/api";

const SearchPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // State
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "");
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(
    null
  );
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"title" | "date">(
    (searchParams.get("sort") as "title" | "date") || "title"
  );

  // Pagination
  const limit = 12;
  const parsedPage = parseInt(searchParams.get("page") || "1", 10);
  const page = Number.isNaN(parsedPage) || parsedPage < 1 ? 1 : parsedPage;

  // Filter state
  const [filters, setFilters] = useState<SearchFilters>({
    artist: searchParams.get("artist") || undefined,
    period: searchParams.get("period") || undefined,
    medium: searchParams.get("medium") || undefined,
    location: searchParams.get("location") || undefined,
    style: searchParams.get("style") || undefined,
  });

  // Perform search
  const performSearch = useCallback(
    async (
      query: string,
      currentFilters: SearchFilters,
      currentPage: number = 1,
      currentSort: "title" | "date" = "title"
    ) => {
      setIsSearching(true);
      setError(null);

      try {
        const response = await searchApi.search(
          query,
          currentFilters,
          currentPage,
          limit,
          currentSort
        );
        setSearchResponse(response.data);
      } catch (err) {
        console.error("Search error:", err);
        setError("Failed to search artworks. Please try again.");
        setSearchResponse(null);
      } finally {
        setIsSearching(false);
      }
    },
    [limit]
  );

  // Search on initial load if query param exists or filters are present
  useEffect(() => {
    const q = searchParams.get("q") || "";
    setSearchQuery(q);

    // Perform initial search (defaults to "browse all")
    performSearch(q, filters, page, sortBy);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Update URL when filters change
  const updateUrlParams = (
    query: string,
    newFilters: SearchFilters,
    newPage: number = 1
  ) => {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (newFilters.artist) params.set("artist", newFilters.artist);
    if (newFilters.period) params.set("period", newFilters.period);
    if (newFilters.medium) params.set("medium", newFilters.medium);
    if (newFilters.location) params.set("location", newFilters.location);
    if (newFilters.style) params.set("style", newFilters.style);
    if (newPage > 1) params.set("page", String(newPage));
    setSearchParams(params);
  };

  // Handle pagination
  const goToPage = (newPage: number) => {
    updateUrlParams(searchQuery, filters, newPage);
    performSearch(searchQuery, filters, newPage, sortBy);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const totalPages = searchResponse
    ? Math.ceil(searchResponse.total / limit)
    : 0;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const hasFilters = Object.values(filters).some((v) => v !== undefined);
    if (!searchQuery.trim() && !hasFilters) return;
    updateUrlParams(searchQuery, filters);
    performSearch(searchQuery, filters, 1, sortBy);
  };

  const handleFilterChange = (
    filterType: keyof SearchFilters,
    value: string | undefined
  ) => {
    const newFilters = { ...filters, [filterType]: value };
    setFilters(newFilters);
    updateUrlParams(searchQuery, newFilters);
    performSearch(searchQuery, newFilters, 1, sortBy);
  };

  const clearFilters = () => {
    const clearedFilters: SearchFilters = {};
    setFilters(clearedFilters);
    // Always update URL and perform search, even if query is empty (Browse All behavior)
    updateUrlParams(searchQuery, clearedFilters);
    performSearch(searchQuery, clearedFilters, 1, sortBy);
  };

  const hasActiveFilters =
    filters.artist ||
    filters.period ||
    filters.medium ||
    filters.location ||
    filters.style;

  // Handle sort change
  const handleSortChange = (newSort: "title" | "date") => {
    setSortBy(newSort);
    // Update URL with sort param
    const params = new URLSearchParams(searchParams);
    if (newSort === "date") {
      params.set("sort", "date");
    } else {
      params.delete("sort");
    }
    setSearchParams(params);
    // Re-fetch with new sort order
    performSearch(searchQuery, filters, 1, newSort);
  };

  // Results are now sorted server-side
  const sortedResults = searchResponse?.results || [];

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
                {isSearching ? "Searching..." : "Search"}
              </button>
            </div>
          </form>

          {/* Quick Filters - Dynamic from facets (artwork styles) */}
          {searchResponse?.facets?.styles &&
            searchResponse.facets.styles.length > 0 && (
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {searchResponse.facets.styles.slice(0, 5).map((facet) => (
                  <button
                    key={facet.name}
                    onClick={() =>
                      handleFilterChange(
                        "style",
                        filters.style === facet.name ? undefined : facet.name
                      )
                    }
                    className={`cursor-pointer rounded-full border px-4 py-1 text-sm transition-colors ${
                      filters.style === facet.name
                        ? "border-gold bg-gold/20 text-gold"
                        : "border-parchment/30 text-parchment/70 hover:border-gold hover:text-gold"
                    }`}
                  >
                    {facet.name}
                  </button>
                ))}
              </div>
            )}
        </div>
      </div>

      {/* Main Content */}
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-8 rounded-lg bg-burgundy/10 p-4 text-burgundy">
            {error}
          </div>
        )}

        {searchResponse === null && !isSearching ? (
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
        ) : (
          <div className="grid gap-8 lg:grid-cols-4">
            {/* Filter Sidebar */}
            <div className="lg:col-span-1">
              <div className="sticky top-4 rounded-xl border border-bronze/20 bg-ivory p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-heading text-lg font-semibold text-charcoal">
                    Filters
                  </h3>
                  {hasActiveFilters && (
                    <button
                      onClick={clearFilters}
                      className="text-sm text-burgundy hover:text-burgundy-dark"
                    >
                      Clear all
                    </button>
                  )}
                </div>

                {/* Artist Filter */}
                {searchResponse?.facets?.artists &&
                  searchResponse.facets.artists.length > 0 && (
                    <div className="mb-6">
                      <h4 className="mb-2 font-medium text-charcoal">Artist</h4>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {searchResponse.facets.artists.map((facet) => (
                          <label
                            key={facet.name}
                            className="flex items-center gap-2 cursor-pointer"
                          >
                            <input
                              type="radio"
                              name="artist"
                              checked={filters.artist === facet.name}
                              onChange={() =>
                                handleFilterChange(
                                  "artist",
                                  filters.artist === facet.name
                                    ? undefined
                                    : facet.name
                                )
                              }
                              className="text-gold focus:ring-gold"
                            />
                            <span className="text-sm text-charcoal-light flex-1 truncate">
                              {facet.name}
                            </span>
                            <span className="text-xs text-bronze">
                              ({facet.count})
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                {/* Period Filter */}
                {searchResponse?.facets?.periods &&
                  searchResponse.facets.periods.length > 0 && (
                    <div className="mb-6">
                      <h4 className="mb-2 font-medium text-charcoal">Period</h4>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {searchResponse.facets.periods.map((facet) => (
                          <label
                            key={facet.name}
                            className="flex items-center gap-2 cursor-pointer"
                          >
                            <input
                              type="radio"
                              name="period"
                              checked={filters.period === facet.name}
                              onChange={() =>
                                handleFilterChange(
                                  "period",
                                  filters.period === facet.name
                                    ? undefined
                                    : facet.name
                                )
                              }
                              className="text-gold focus:ring-gold"
                            />
                            <span className="text-sm text-charcoal-light flex-1 truncate">
                              {facet.name}
                            </span>
                            <span className="text-xs text-bronze">
                              ({facet.count})
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                {/* Medium Filter */}
                {searchResponse?.facets?.media &&
                  searchResponse.facets.media.length > 0 && (
                    <div className="mb-6">
                      <h4 className="mb-2 font-medium text-charcoal">Medium</h4>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {searchResponse.facets.media.map((facet) => (
                          <label
                            key={facet.name}
                            className="flex items-center gap-2 cursor-pointer"
                          >
                            <input
                              type="radio"
                              name="medium"
                              checked={filters.medium === facet.name}
                              onChange={() =>
                                handleFilterChange(
                                  "medium",
                                  filters.medium === facet.name
                                    ? undefined
                                    : facet.name
                                )
                              }
                              className="text-gold focus:ring-gold"
                            />
                            <span className="text-sm text-charcoal-light flex-1 truncate">
                              {facet.name}
                            </span>
                            <span className="text-xs text-bronze">
                              ({facet.count})
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                {/* Location Filter */}
                {searchResponse?.facets?.locations &&
                  searchResponse.facets.locations.length > 0 && (
                    <div className="mb-6">
                      <h4 className="mb-2 font-medium text-charcoal">
                        Location
                      </h4>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {searchResponse.facets.locations.map((facet) => (
                          <label
                            key={facet.name}
                            className="flex items-center gap-2 cursor-pointer"
                          >
                            <input
                              type="radio"
                              name="location"
                              checked={filters.location === facet.name}
                              onChange={() =>
                                handleFilterChange(
                                  "location",
                                  filters.location === facet.name
                                    ? undefined
                                    : facet.name
                                )
                              }
                              className="text-gold focus:ring-gold"
                            />
                            <span className="text-sm text-charcoal-light flex-1 truncate">
                              {facet.name}
                            </span>
                            <span className="text-xs text-bronze">
                              ({facet.count})
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            </div>

            {/* Results */}
            <div className="lg:col-span-3">
              {isSearching ? (
                <div className="text-center py-16">
                  <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gold border-r-transparent" />
                  <p className="mt-4 text-charcoal-light">Searching...</p>
                </div>
              ) : searchResponse?.results.length === 0 ? (
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
                <>
                  <div className="mb-8 flex items-center justify-between">
                    <p className="text-charcoal-light">
                      Found{" "}
                      <span className="font-medium text-charcoal">
                        {searchResponse?.total}
                      </span>{" "}
                      artworks
                    </p>
                    <select
                      value={sortBy}
                      onChange={(e) =>
                        handleSortChange(e.target.value as "title" | "date")
                      }
                      className="cursor-pointer rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal focus:border-gold focus:outline-none"
                    >
                      <option value="title">Title A-Z</option>
                      <option value="date">Date (Newest)</option>
                    </select>
                  </div>

                  <div className="space-y-4">
                    {sortedResults.map((artwork) => (
                      <Link
                        key={artwork.id}
                        to={`/artworks/${artwork.id}`}
                        className="group flex gap-6 rounded-2xl border border-bronze/20 bg-ivory p-4 shadow-sm transition-all hover:border-gold/40 hover:shadow-md"
                      >
                        {/* Thumbnail */}
                        <div className="h-24 w-24 flex-shrink-0 overflow-hidden rounded-lg bg-parchment-dark">
                          {artwork.imageUrl ? (
                            <img
                              src={artwork.imageUrl}
                              alt={artwork.title}
                              className="h-full w-full object-cover transition-transform group-hover:scale-105"
                            />
                          ) : (
                            <div className="h-full w-full flex items-center justify-center text-bronze/50">
                              <svg
                                className="h-8 w-8"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={1}
                                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                                />
                              </svg>
                            </div>
                          )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <h3 className="font-heading text-lg font-semibold text-charcoal group-hover:text-gold transition-colors truncate">
                            {artwork.title}
                          </h3>
                          {artwork.artist && (
                            <p className="mt-1 text-charcoal-light">
                              {artwork.artist}
                            </p>
                          )}
                          <div className="mt-2 flex flex-wrap gap-4 text-sm text-bronze">
                            {artwork.dateCreated && (
                              <span>{artwork.dateCreated}</span>
                            )}
                            {artwork.dateCreated && artwork.medium && (
                              <span>•</span>
                            )}
                            {artwork.medium && <span>{artwork.medium}</span>}
                          </div>
                          {artwork.period && (
                            <span className="mt-2 inline-block rounded-full bg-parchment-dark px-2 py-0.5 text-xs text-charcoal-light">
                              {artwork.period}
                            </span>
                          )}
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

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="mt-12 flex justify-center">
                      <nav className="flex items-center gap-2">
                        <button
                          onClick={() => goToPage(page - 1)}
                          disabled={page <= 1}
                          className="cursor-pointer rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal-light hover:border-gold hover:text-charcoal transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Previous
                        </button>

                        <div className="flex items-center gap-1">
                          {/* First page */}
                          {page > 2 && (
                            <>
                              <button
                                onClick={() => goToPage(1)}
                                className="cursor-pointer rounded-lg px-3 py-2 text-sm text-charcoal-light hover:text-charcoal transition-colors"
                              >
                                1
                              </button>
                              {page > 3 && (
                                <span className="px-2 text-bronze">...</span>
                              )}
                            </>
                          )}

                          {/* Previous page */}
                          {page > 1 && (
                            <button
                              onClick={() => goToPage(page - 1)}
                              className="cursor-pointer rounded-lg px-3 py-2 text-sm text-charcoal-light hover:text-charcoal transition-colors"
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
                              className="cursor-pointer rounded-lg px-3 py-2 text-sm text-charcoal-light hover:text-charcoal transition-colors"
                            >
                              {page + 1}
                            </button>
                          )}

                          {/* Last page */}
                          {page < totalPages - 1 && (
                            <>
                              {page < totalPages - 2 && (
                                <span className="px-2 text-bronze">...</span>
                              )}
                              <button
                                onClick={() => goToPage(totalPages)}
                                className="cursor-pointer rounded-lg px-3 py-2 text-sm text-charcoal-light hover:text-charcoal transition-colors"
                              >
                                {totalPages}
                              </button>
                            </>
                          )}
                        </div>

                        <button
                          onClick={() => goToPage(page + 1)}
                          disabled={page >= totalPages}
                          className="cursor-pointer rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal-light hover:border-gold hover:text-charcoal transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
        )}
      </div>
    </div>
  );
};

export default SearchPage;
