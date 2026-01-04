import { Link, useParams } from 'react-router-dom';

// Placeholder data (to be replaced with API call)
const placeholderArtwork = {
  id: '1',
  title: 'The Starry Night',
  artist: 'Vincent van Gogh',
  dateCreated: 'June 1889',
  medium: 'Oil on canvas',
  dimensions: '73.7 cm × 92.1 cm (29 in × 36.25 in)',
  currentLocation: 'Museum of Modern Art, New York City',
  description: 'The Starry Night is an oil-on-canvas painting by the Dutch Post-Impressionist painter Vincent van Gogh. Painted in June 1889, it depicts the view from the east-facing window of his asylum room at Saint-Rémy-de-Provence, just before sunrise, with the addition of an imaginary village.',
  imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/600px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg',
  provenance: [
    {
      date: 'June 1889',
      event: 'Created',
      owner: 'Vincent van Gogh',
      location: 'Saint-Rémy-de-Provence, France',
    },
    {
      date: 'July 1890',
      event: 'Inherited',
      owner: 'Theo van Gogh',
      location: 'Paris, France',
    },
    {
      date: '1891',
      event: 'Inherited',
      owner: 'Johanna van Gogh-Bonger',
      location: 'Netherlands',
    },
    {
      date: '1900',
      event: 'Sold',
      owner: 'Julien Leclercq',
      location: 'Paris, France',
    },
    {
      date: '1901',
      event: 'Sold',
      owner: 'Émile Schuffenecker',
      location: 'Paris, France',
    },
    {
      date: '1941',
      event: 'Acquired',
      owner: 'Museum of Modern Art',
      location: 'New York City, USA',
    },
  ],
  externalLinks: {
    dbpedia: 'http://dbpedia.org/resource/The_Starry_Night',
    wikidata: 'https://www.wikidata.org/wiki/Q45585',
    getty: 'http://vocab.getty.edu/aat/300177435',
  },
};

const ArtworkDetailPage = () => {
  const { id } = useParams<{ id: string }>();

  // In real implementation, fetch artwork by id
  const artwork = placeholderArtwork;

  return (
    <div 
      className="min-h-screen bg-parchment"
      vocab="https://schema.org/"
      typeof="VisualArtwork"
    >
      {/* Breadcrumb */}
      <div className="border-b border-bronze/20 bg-ivory">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <nav className="flex items-center gap-2 text-sm">
            <Link to="/" className="text-charcoal-light hover:text-gold transition-colors">
              Home
            </Link>
            <span className="text-bronze">/</span>
            <Link to="/artworks" className="text-charcoal-light hover:text-gold transition-colors">
              Collection
            </Link>
            <span className="text-bronze">/</span>
            <span className="text-charcoal" property="name">{artwork.title}</span>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-2">
          {/* Image */}
          <div className="overflow-hidden rounded-2xl border border-bronze/20 bg-ivory shadow-lg">
            <img
              src={artwork.imageUrl}
              alt={artwork.title}
              property="image"
              className="w-full object-cover"
            />
          </div>

          {/* Details */}
          <div>
            <h1 className="font-heading text-3xl font-bold text-charcoal sm:text-4xl" property="name">
              {artwork.title}
            </h1>
            
            <p className="mt-2 text-xl text-charcoal-light">
              by <span property="creator" typeof="Person"><span property="name">{artwork.artist}</span></span>
            </p>

            <div className="mt-8 space-y-4">
              <div className="flex border-b border-bronze/10 pb-4">
                <span className="w-32 font-medium text-charcoal-light">Date:</span>
                <span className="text-charcoal" property="dateCreated">{artwork.dateCreated}</span>
              </div>
              <div className="flex border-b border-bronze/10 pb-4">
                <span className="w-32 font-medium text-charcoal-light">Medium:</span>
                <span className="text-charcoal" property="artMedium">{artwork.medium}</span>
              </div>
              <div className="flex border-b border-bronze/10 pb-4">
                <span className="w-32 font-medium text-charcoal-light">Dimensions:</span>
                <span className="text-charcoal">{artwork.dimensions}</span>
              </div>
              <div className="flex border-b border-bronze/10 pb-4">
                <span className="w-32 font-medium text-charcoal-light">Location:</span>
                <span className="text-charcoal" property="contentLocation">{artwork.currentLocation}</span>
              </div>
            </div>

            <div className="mt-8">
              <h2 className="font-heading text-lg font-semibold text-charcoal">Description</h2>
              <p className="mt-3 leading-relaxed text-charcoal-light" property="description">
                {artwork.description}
              </p>
            </div>

            {/* External Links */}
            {artwork.externalLinks && (
              <div className="mt-8">
                <h2 className="font-heading text-lg font-semibold text-charcoal">Linked Data</h2>
                <div className="mt-3 flex flex-wrap gap-3">
                  {artwork.externalLinks.dbpedia && (
                    <a
                      href={artwork.externalLinks.dbpedia}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal hover:border-gold hover:text-gold transition-colors"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      DBpedia
                    </a>
                  )}
                  {artwork.externalLinks.wikidata && (
                    <a
                      href={artwork.externalLinks.wikidata}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal hover:border-gold hover:text-gold transition-colors"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      Wikidata
                    </a>
                  )}
                  {artwork.externalLinks.getty && (
                    <a
                      href={artwork.externalLinks.getty}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal hover:border-gold hover:text-gold transition-colors"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      Getty AAT
                    </a>
                  )}
                </div>
              </div>
            )}

            {/* QR Code Button */}
            <div className="mt-8">
              <button className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-gold to-gold-dark px-6 py-3 font-medium text-charcoal shadow-md hover:shadow-lg transition-shadow">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                </svg>
                Generate QR Code
              </button>
            </div>
          </div>
        </div>

        {/* Provenance Timeline */}
        <div className="mt-16">
          <h2 className="font-heading text-2xl font-bold text-charcoal">Provenance History</h2>
          <p className="mt-2 text-charcoal-light">
            Trace the ownership and location history of this artwork.
          </p>

          <div className="mt-8">
            <div className="relative border-l-2 border-gold/30 pl-8">
              {artwork.provenance.map((record, index) => (
                <div 
                  key={index}
                  className="relative mb-8 last:mb-0"
                >
                  {/* Timeline dot */}
                  <div className="absolute -left-[41px] flex h-6 w-6 items-center justify-center rounded-full border-2 border-gold bg-ivory">
                    <div className="h-2 w-2 rounded-full bg-gold" />
                  </div>

                  <div className="rounded-xl border border-bronze/20 bg-ivory p-6 shadow-sm">
                    <div className="flex flex-wrap items-center gap-4">
                      <span className="rounded-full bg-gold/10 px-3 py-1 text-sm font-medium text-gold">
                        {record.date}
                      </span>
                      <span className="text-sm font-medium uppercase tracking-wider text-burgundy">
                        {record.event}
                      </span>
                    </div>
                    <div className="mt-3 space-y-1">
                      <p className="font-medium text-charcoal">{record.owner}</p>
                      <p className="text-sm text-charcoal-light">{record.location}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Debug: show artwork ID */}
      <div className="hidden">Artwork ID: {id}</div>
    </div>
  );
};

export default ArtworkDetailPage;

