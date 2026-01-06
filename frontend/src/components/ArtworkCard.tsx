import { memo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import type { Artwork } from '../services/api';
import OptimizedImage, { preloadImage } from './OptimizedImage';

interface ArtworkCardProps {
  artwork: Artwork;
  className?: string;
}

const ArtworkCard = memo(({ artwork, className = '' }: ArtworkCardProps) => {
  // Preload the higher resolution image on hover for faster detail page load
  const handleMouseEnter = useCallback(() => {
    if (artwork.imageUrl) {
      preloadImage(artwork.imageUrl, 800);
    }
  }, [artwork.imageUrl]);

  return (
    <Link
      to={`/artworks/${artwork.id}`}
      className={`group overflow-hidden rounded-2xl border border-bronze/20 bg-ivory shadow-sm transition-all hover:border-gold/40 hover:shadow-lg ${className}`}
      onMouseEnter={handleMouseEnter}
    >
      {/* Image */}
      <div className="aspect-[4/3] overflow-hidden bg-parchment-dark">
        <OptimizedImage
          src={artwork.imageUrl}
          alt={artwork.title}
          width={400}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          placeholderClassName="h-full w-full"
        />
      </div>
      
      {/* Content */}
      <div className="p-6">
        <h2 className="font-heading text-xl font-semibold text-charcoal group-hover:text-gold transition-colors line-clamp-2">
          {artwork.title}
        </h2>
        {artwork.artist && (
          <p className="mt-2 text-charcoal-light">
            {artwork.artist}
          </p>
        )}
        <div className="mt-4 flex items-center justify-between text-sm text-bronze">
          <span>{artwork.dateCreated || 'Unknown date'}</span>
          <span className="truncate ml-2">{artwork.medium || artwork.period}</span>
        </div>
        <div className="mt-4 flex items-center gap-2 text-sm text-gold opacity-0 transition-opacity group-hover:opacity-100">
          <span>View Provenance</span>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </div>
      </div>
    </Link>
  );
});

ArtworkCard.displayName = 'ArtworkCard';

export default ArtworkCard;

