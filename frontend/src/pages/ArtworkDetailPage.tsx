import { useState, useEffect, useCallback } from 'react';
import { Link, useParams } from 'react-router-dom';
import { artworkApi, type Artwork, type ProvenanceRecord, type ArtworkEnrichment } from '../services/api';
import { ArtworkDetailSkeleton, ErrorMessage, NotFound, OptimizedImage, JsonLdScript } from '../components';

// Helper to extract a numeric year from various date formats
const extractYear = (dateStr: string): number | null => {
  // Try ISO format first (YYYY-MM-DD or YYYY)
  const isoMatch = dateStr.match(/^(\d{4})/);
  if (isoMatch) return parseInt(isoMatch[1], 10);

  // Try "c. YYYY" or "circa YYYY" format
  const circaMatch = dateStr.match(/c\.?\s*(\d{4})/i);
  if (circaMatch) return parseInt(circaMatch[1], 10);

  // Try extracting any 4-digit year
  const yearMatch = dateStr.match(/\b(\d{4})\b/);
  if (yearMatch) return parseInt(yearMatch[1], 10);

  return null;
};

// Helper to format ISO dates to full readable dates (e.g., "May 15, 1838")
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '';

  // Extract date part if it includes time
  let datePart = dateStr;
  if (dateStr.includes('T')) {
    datePart = dateStr.split('T')[0];
  }

  // Handle YYYY-MM-DD format
  const isoMatch = datePart.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (isoMatch) {
    const [, year, month, day] = isoMatch;
    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  // Handle YYYY-MM format
  const yearMonthMatch = datePart.match(/^(\d{4})-(\d{2})$/);
  if (yearMonthMatch) {
    const [, year, month] = yearMonthMatch;
    const date = new Date(parseInt(year), parseInt(month) - 1, 1);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long'
    });
  }

  // Handle just YYYY
  if (datePart.match(/^\d{4}$/)) {
    return datePart;
  }

  // Return as-is for other formats
  return dateStr;
};

const ArtworkDetailPage = () => {
  const { id } = useParams<{ id: string }>();

  // State
  const [artwork, setArtwork] = useState<Artwork | null>(null);
  const [provenance, setProvenance] = useState<ProvenanceRecord[]>([]);
  const [enrichment, setEnrichment] = useState<ArtworkEnrichment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  // Fetch artwork data
  const fetchArtwork = useCallback(async () => {
    if (!id) return;

    setLoading(true);
    setError(null);
    setNotFound(false);

    try {
      // Fetch artwork details
      const artworkResponse = await artworkApi.getById(id);
      setArtwork(artworkResponse.data);

      // Fetch provenance in parallel
      const [provenanceResponse, enrichmentResponse] = await Promise.allSettled([
        artworkApi.getProvenance(id),
        artworkApi.getEnrichment(id)
      ]);

      if (provenanceResponse.status === 'fulfilled') {
        // Sort by order if available, fallback to date, push undefined to end
        const sortedProvenance = [...provenanceResponse.value.data].sort((a, b) => {
          // Both have order - sort by order
          if (a.order !== undefined && b.order !== undefined) {
            return a.order - b.order;
          }
          // Only a has order - a comes first
          if (a.order !== undefined) {
            return -1;
          }
          // Only b has order - b comes first
          if (b.order !== undefined) {
            return 1;
          }
          // Neither has order - try sorting by date using year extraction
          if (a.date && b.date) {
            const yearA = extractYear(a.date);
            const yearB = extractYear(b.date);
            if (yearA !== null && yearB !== null) {
              return yearA - yearB;
            }
            // If only one has a parseable year, prioritize it
            if (yearA !== null) return -1;
            if (yearB !== null) return 1;
            // Fallback to lexicographic comparison for unparseable dates
            return a.date.localeCompare(b.date);
          }
          // Push records without date to end
          if (a.date) return -1;
          if (b.date) return 1;
          return 0;
        });
        setProvenance(sortedProvenance);
      } else {
        console.warn('Failed to fetch provenance:', provenanceResponse.reason);
      }

      if (enrichmentResponse.status === 'fulfilled') {
        setEnrichment(enrichmentResponse.value.data);
      } else {
        console.warn('Failed to fetch enrichment:', enrichmentResponse.reason);
      }
    } catch (err: unknown) {
      console.error('Failed to fetch artwork:', err);
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          setNotFound(true);
        } else {
          setError('Failed to load artwork details. Please try again.');
        }
      } else {
        setError('Failed to load artwork details. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchArtwork();
  }, [fetchArtwork]);

  // Generate external links from enrichment or artwork data
  // Merge both sources: prefer enrichment data, fallback to artwork.externalLinks per link type
  const getExternalLinks = () => {
    const links: { name: string; url: string }[] = [];

    // DBpedia: try enrichment first, fallback to artwork.externalLinks
    if (enrichment?.dbpedia?.uri) {
      links.push({ name: 'DBpedia', url: enrichment.dbpedia.uri });
    } else if (artwork?.externalLinks?.dbpedia) {
      links.push({ name: 'DBpedia', url: artwork.externalLinks.dbpedia });
    }

    // Wikidata: try enrichment first, fallback to artwork.externalLinks
    if (enrichment?.wikidata?.uri) {
      // Convert entity URI to wiki page URL
      const wikidataId = enrichment.wikidata.uri.split('/').pop();
      // Only add if we got a valid Wikidata ID (e.g., Q12345)
      if (wikidataId && /^Q\d+$/.test(wikidataId)) {
        links.push({ name: 'Wikidata', url: `https://www.wikidata.org/wiki/${wikidataId}` });
      } else if (enrichment.wikidata.uri.startsWith('http')) {
        // Fallback: use the original URI if it's already a valid URL
        links.push({ name: 'Wikidata', url: enrichment.wikidata.uri });
      }
    } else if (artwork?.externalLinks?.wikidata) {
      links.push({ name: 'Wikidata', url: artwork.externalLinks.wikidata });
    }

    // Getty: try enrichment first, fallback to artwork.externalLinks
    if (enrichment?.getty && enrichment.getty.length > 0) {
      links.push({ name: 'Getty AAT', url: enrichment.getty[0].uri });
    } else if (artwork?.externalLinks?.getty) {
      links.push({ name: 'Getty AAT', url: artwork.externalLinks.getty });
    }

    return links;
  };


  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-parchment">
        {/* Breadcrumb skeleton */}
        <div className="border-b border-bronze/20 bg-ivory">
          <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
            <div className="h-4 w-48 animate-pulse rounded bg-parchment-dark" />
          </div>
        </div>
        <ArtworkDetailSkeleton />
      </div>
    );
  }

  // Not found state
  if (notFound) {
    return (
      <div className="min-h-screen bg-parchment">
        <NotFound
          itemType="artwork"
          backLink="/artworks"
          backLinkText="Back to collection"
        />
      </div>
    );
  }

  // Error state
  if (error || !artwork) {
    return (
      <div className="min-h-screen bg-parchment">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <ErrorMessage
            message={error || 'Unable to load artwork'}
            onRetry={fetchArtwork}
            showHomeLink
          />
        </div>
      </div>
    );
  }

  const externalLinks = getExternalLinks();

  return (
    <div
      className="min-h-screen bg-parchment"
      vocab="https://schema.org/"
      typeof="VisualArtwork"
      resource={`#artwork-${artwork.id}`}
    >
      {/* JSON-LD Structured Data */}
      <JsonLdScript artwork={artwork} provenance={provenance} />

      {/* Breadcrumb */}
      <div className="border-b border-bronze/20 bg-ivory">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <nav className="flex items-center gap-2 text-sm" aria-label="Breadcrumb">
            <Link to="/" className="text-charcoal-light hover:text-gold transition-colors">
              Home
            </Link>
            <span className="text-bronze" aria-hidden="true">/</span>
            <Link to="/artworks" className="text-charcoal-light hover:text-gold transition-colors">
              Collection
            </Link>
            <span className="text-bronze" aria-hidden="true">/</span>
            <span className="text-charcoal truncate max-w-xs" property="name" aria-current="page">{artwork.title}</span>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-2">
          {/* Image */}
          <div className="overflow-hidden rounded-2xl border border-bronze/20 bg-ivory shadow-lg self-start">
            <OptimizedImage
              src={artwork.imageUrl}
              alt={artwork.title}
              property="image"
              width={800}
              className="w-full h-auto block"
              placeholderClassName="w-full aspect-[4/3]"
              shrinkOnLoad={true}
            />
          </div>

          {/* Details */}
          <div>
            <h1 className="font-heading text-3xl font-bold text-charcoal sm:text-4xl" property="name">
              {artwork.title}
            </h1>

            {artwork.artist && (
              <p className="mt-2 text-xl text-charcoal-light">
                by <span property="creator" typeof="Person"><span property="name">{artwork.artist}</span></span>
              </p>
            )}

            <div className="mt-8 space-y-4">
              {artwork.dateCreated && (
                <div className="flex border-b border-bronze/10 pb-4">
                  <span className="w-32 font-medium text-charcoal-light">Date:</span>
                  <span className="text-charcoal" property="dateCreated">{artwork.dateCreated}</span>
                </div>
              )}
              {artwork.medium && (
                <div className="flex border-b border-bronze/10 pb-4">
                  <span className="w-32 font-medium text-charcoal-light">Medium:</span>
                  <span className="text-charcoal" property="artMedium">{artwork.medium}</span>
                </div>
              )}
              {artwork.dimensions && (
                <div className="flex border-b border-bronze/10 pb-4">
                  <span className="w-32 font-medium text-charcoal-light">Dimensions:</span>
                  <span className="text-charcoal">{artwork.dimensions}</span>
                </div>
              )}
              {artwork.period && (
                <div className="flex border-b border-bronze/10 pb-4">
                  <span className="w-32 font-medium text-charcoal-light">Period:</span>
                  <span className="text-charcoal">{artwork.period}</span>
                </div>
              )}
              {artwork.style && (
                <div className="flex border-b border-bronze/10 pb-4">
                  <span className="w-32 font-medium text-charcoal-light">Style:</span>
                  <span className="text-charcoal">{artwork.style}</span>
                </div>
              )}
              {artwork.currentLocation && (
                <div className="flex border-b border-bronze/10 pb-4">
                  <span className="w-32 font-medium text-charcoal-light">Location:</span>
                  <span className="text-charcoal" property="contentLocation">{artwork.currentLocation}</span>
                </div>
              )}
            </div>

            {artwork.description && (
              <div className="mt-8">
                <h2 className="font-heading text-lg font-semibold text-charcoal">Description</h2>
                <p className="mt-3 leading-relaxed text-charcoal-light" property="description">
                  {artwork.description}
                </p>
              </div>
            )}

            {/* Artist Info from Enrichment (external or local) */}
            {(enrichment?.artist_dbpedia || enrichment?.artist_wikidata || enrichment?.artist_local) && (
              <div className="mt-8 rounded-xl border border-bronze/20 bg-ivory p-6">
                <h2 className="font-heading text-lg font-semibold text-charcoal">About the Artist</h2>
                {/* Artist description - prefer external, fallback to local */}
                {(enrichment.artist_dbpedia?.abstract || enrichment.artist_wikidata?.description || enrichment.artist_local?.description) && (
                  <p className="mt-3 text-sm leading-relaxed text-charcoal-light">
                    {enrichment.artist_dbpedia?.abstract || enrichment.artist_wikidata?.description || enrichment.artist_local?.description}
                  </p>
                )}
                {/* Birth and death dates - prefer external, fallback to local */}
                {(() => {
                  const birthDate = enrichment.artist_dbpedia?.birthDate || enrichment.artist_wikidata?.birthDate || enrichment.artist_local?.birthDate;
                  const deathDate = enrichment.artist_dbpedia?.deathDate || enrichment.artist_wikidata?.deathDate || enrichment.artist_local?.deathDate;
                  const nationality = enrichment.artist_local?.nationality;

                  if (birthDate || deathDate || nationality) {
                    return (
                      <p className="mt-2 text-sm text-bronze">
                        {nationality && <span>{nationality} • </span>}
                        {birthDate && <span>Born: {formatDate(birthDate)}</span>}
                        {birthDate && deathDate && ' • '}
                        {deathDate && <span>Died: {formatDate(deathDate)}</span>}
                      </p>
                    );
                  }
                  return null;
                })()}
              </div>
            )}

            {/* External Links */}
            {externalLinks.length > 0 && (
              <div className="mt-8">
                <h2 className="font-heading text-lg font-semibold text-charcoal">Linked Data</h2>
                <div className="mt-3 flex flex-wrap gap-3">
                  {externalLinks.map((link) => (
                    <a
                      key={link.name}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      property="sameAs"
                      className="inline-flex items-center gap-2 rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal hover:border-gold hover:text-gold transition-colors"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      {link.name}
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* QR Code Button */}
            <div className="mt-8">
              <button
                onClick={() => {
                  // Future: Implement QR code modal
                  alert('QR Code feature coming soon!');
                }}
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-gold to-gold-dark px-6 py-3 font-medium text-charcoal shadow-md hover:shadow-lg transition-shadow"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                </svg>
                Generate QR Code
              </button>
            </div>
          </div>
        </div>

        {/* Provenance Timeline with RDFa */}
        {provenance.length > 0 && (
          <section className="mt-16" aria-labelledby="provenance-heading">
            <h2 id="provenance-heading" className="font-heading text-2xl font-bold text-charcoal">Provenance History</h2>
            <p className="mt-2 text-charcoal-light">
              Trace the ownership and location history of this artwork.
            </p>

            <div className="mt-8" property="subjectOf" typeof="ItemList">
              <div className="relative border-l-2 border-gold/30 pl-8">
                {provenance.map((record, index) => (
                  <div
                    key={record.id || index}
                    className="relative mb-8 last:mb-0"
                    property="itemListElement"
                    typeof="ListItem"
                  >
                    <meta property="position" content={String(index + 1)} />
                    {/* Timeline dot */}
                    <div className="absolute -left-[41px] flex h-6 w-6 items-center justify-center rounded-full border-2 border-gold bg-ivory" aria-hidden="true">
                      <div className="h-2 w-2 rounded-full bg-gold" />
                    </div>

                    <div className="rounded-xl border border-bronze/20 bg-ivory p-6 shadow-sm" property="item" typeof="TransferAction">
                      <div className="flex flex-wrap items-center gap-4">
                        {record.date && (
                          <span className="rounded-full bg-gold/10 px-3 py-1 text-sm font-medium text-gold" property="startTime">
                            {extractYear(record.date) ?? record.date}
                          </span>
                        )}
                        <span className="text-sm font-medium uppercase tracking-wider text-burgundy" property="name">
                          {record.event}
                        </span>
                      </div>
                      <div className="mt-3 space-y-1">
                        {record.owner && (
                          <p className="font-medium text-charcoal" property="agent" typeof="Person">
                            <span property="name">{record.owner}</span>
                          </p>
                        )}
                        {record.location && (
                          <p className="text-sm text-charcoal-light" property="location" typeof="Place">
                            <span property="name">{record.location}</span>
                          </p>
                        )}
                        {record.description && (
                          <p className="mt-2 text-sm text-charcoal-light" property="description">{record.description}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default ArtworkDetailPage;
