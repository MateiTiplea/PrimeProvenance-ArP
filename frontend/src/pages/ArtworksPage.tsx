import { Link } from 'react-router-dom';

// Placeholder artwork data (to be replaced with API calls)
const placeholderArtworks = [
  {
    id: '1',
    title: 'The Starry Night',
    artist: 'Vincent van Gogh',
    dateCreated: '1889',
    medium: 'Oil on canvas',
    imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/300px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg',
  },
  {
    id: '2',
    title: 'Mona Lisa',
    artist: 'Leonardo da Vinci',
    dateCreated: 'c. 1503–1519',
    medium: 'Oil on poplar panel',
    imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/300px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg',
  },
  {
    id: '3',
    title: 'The Persistence of Memory',
    artist: 'Salvador Dalí',
    dateCreated: '1931',
    medium: 'Oil on canvas',
    imageUrl: 'https://upload.wikimedia.org/wikipedia/en/d/dd/The_Persistence_of_Memory.jpg',
  },
  {
    id: '4',
    title: 'Girl with a Pearl Earring',
    artist: 'Johannes Vermeer',
    dateCreated: 'c. 1665',
    medium: 'Oil on canvas',
    imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/1665_Girl_with_a_Pearl_Earring.jpg/300px-1665_Girl_with_a_Pearl_Earring.jpg',
  },
  {
    id: '5',
    title: 'The Birth of Venus',
    artist: 'Sandro Botticelli',
    dateCreated: 'c. 1484–1486',
    medium: 'Tempera on canvas',
    imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Sandro_Botticelli_-_La_nascita_di_Venere_-_Google_Art_Project_-_edited.jpg/400px-Sandro_Botticelli_-_La_nascita_di_Venere_-_Google_Art_Project_-_edited.jpg',
  },
  {
    id: '6',
    title: 'The Night Watch',
    artist: 'Rembrandt van Rijn',
    dateCreated: '1642',
    medium: 'Oil on canvas',
    imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/The_Night_Watch_-_HD.jpg/400px-The_Night_Watch_-_HD.jpg',
  },
];

const ArtworksPage = () => {
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
                className="rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal placeholder:text-bronze focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              />
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="period" className="text-sm font-medium text-charcoal-light">
                Period:
              </label>
              <select
                id="period"
                className="rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              >
                <option value="">All Periods</option>
                <option value="renaissance">Renaissance</option>
                <option value="baroque">Baroque</option>
                <option value="impressionism">Impressionism</option>
                <option value="modern">Modern</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="medium" className="text-sm font-medium text-charcoal-light">
                Medium:
              </label>
              <select
                id="medium"
                className="rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              >
                <option value="">All Media</option>
                <option value="oil">Oil</option>
                <option value="watercolor">Watercolor</option>
                <option value="tempera">Tempera</option>
                <option value="sculpture">Sculpture</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Artworks Grid */}
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {placeholderArtworks.map((artwork) => (
            <Link
              key={artwork.id}
              to={`/artworks/${artwork.id}`}
              className="group overflow-hidden rounded-2xl border border-bronze/20 bg-ivory shadow-sm transition-all hover:border-gold/40 hover:shadow-lg"
            >
              {/* Image */}
              <div className="aspect-[4/3] overflow-hidden bg-parchment-dark">
                <img
                  src={artwork.imageUrl}
                  alt={artwork.title}
                  className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
              </div>
              
              {/* Content */}
              <div className="p-6">
                <h2 className="font-heading text-xl font-semibold text-charcoal group-hover:text-gold transition-colors">
                  {artwork.title}
                </h2>
                <p className="mt-2 text-charcoal-light">
                  {artwork.artist}
                </p>
                <div className="mt-4 flex items-center justify-between text-sm text-bronze">
                  <span>{artwork.dateCreated}</span>
                  <span>{artwork.medium}</span>
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm text-gold opacity-0 transition-opacity group-hover:opacity-100">
                  <span>View Provenance</span>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* Pagination */}
        <div className="mt-12 flex justify-center">
          <nav className="flex items-center gap-2">
            <button className="rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal-light hover:border-gold hover:text-charcoal transition-colors">
              Previous
            </button>
            <span className="px-4 py-2 text-sm text-charcoal">
              Page 1 of 1
            </span>
            <button className="rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm text-charcoal-light hover:border-gold hover:text-charcoal transition-colors">
              Next
            </button>
          </nav>
        </div>
      </div>
    </div>
  );
};

export default ArtworksPage;

