import { useState, useEffect, memo, useCallback } from 'react';

// Global cache to track loaded images across components
const imageCache = new Set<string>();

// Transform Wikimedia Commons URLs to use thumbnails
const getOptimizedUrl = (url: string, width: number = 400): string => {
  if (!url) return '';

  // Handle Wikimedia Commons Special:FilePath URLs
  if (url.includes('commons.wikimedia.org/wiki/Special:FilePath/')) {
    const filename = url.split('Special:FilePath/')[1];
    if (filename) {
      // Use Wikimedia thumbnail API
      return `https://commons.wikimedia.org/wiki/Special:FilePath/${filename}?width=${width}`;
    }
  }

  // Handle direct Wikimedia Commons URLs
  if (url.includes('upload.wikimedia.org/wikipedia/commons/') && !url.includes('/thumb/')) {
    // Convert to thumbnail URL
    const match = url.match(/\/wikipedia\/commons\/([a-f0-9])\/([a-f0-9]{2})\/(.+)$/);
    if (match) {
      const [, a, ab, filename] = match;
      return `https://upload.wikimedia.org/wikipedia/commons/thumb/${a}/${ab}/${filename}/${width}px-${filename}`;
    }
  }

  return url;
};

interface OptimizedImageProps {
  src: string | undefined;
  alt: string;
  className?: string;
  placeholderClassName?: string;
  width?: number;
  property?: string;
  /** If true, wrapper shrinks to fit image after loading. If false, keeps placeholder dimensions. */
  shrinkOnLoad?: boolean;
  loading?: 'lazy' | 'eager';
}

const OptimizedImage = memo(({
  src,
  alt,
  className = '',
  placeholderClassName = '',
  width = 400,
  property,
  shrinkOnLoad = false,
  loading = 'lazy'
}: OptimizedImageProps) => {
  const optimizedSrc = src ? getOptimizedUrl(src, width) : '';
  const [isLoaded, setIsLoaded] = useState(() => imageCache.has(optimizedSrc));
  const [hasError, setHasError] = useState(false);
  const [imageSrc, setImageSrc] = useState(optimizedSrc);

  // Placeholder SVG
  const placeholderImage = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"%3E%3Crect fill="%23e8e0d0" width="400" height="300"/%3E%3Ctext fill="%238b7355" font-family="sans-serif" font-size="24" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';

  // Reset state when src changes
  useEffect(() => {
    const newOptimizedSrc = src ? getOptimizedUrl(src, width) : '';
    setImageSrc(newOptimizedSrc);
    setHasError(false);
    setIsLoaded(imageCache.has(newOptimizedSrc));
  }, [src, width]);

  const handleLoad = useCallback(() => {
    if (imageSrc) {
      imageCache.add(imageSrc);
    }
    setIsLoaded(true);
  }, [imageSrc]);

  const handleError = useCallback(() => {
    setHasError(true);
    setIsLoaded(true);
  }, []);

  // If no src or has error, show placeholder
  if (!imageSrc || hasError) {
    return (
      <img
        src={placeholderImage}
        alt={alt}
        className={className}
        {...(property && { property })}
      />
    );
  }

  // If shrinkOnLoad is true, remove placeholder sizing after image loads
  // Otherwise, keep the placeholder class to maintain container sizing (for grid cards)
  const wrapperClass = (shrinkOnLoad && isLoaded)
    ? 'relative'
    : `relative ${placeholderClassName}`;

  return (
    <div className={wrapperClass}>
      {/* Loading skeleton */}
      {!isLoaded && (
        <div className="absolute inset-0 animate-pulse bg-parchment-dark flex items-center justify-center">
          <svg className="h-12 w-12 text-bronze/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      )}
      <img
        src={imageSrc}
        alt={alt}
        loading={loading}
        decoding="async"
        className={`${className} ${isLoaded ? 'opacity-100' : 'opacity-0'} transition-opacity duration-300`}
        onLoad={handleLoad}
        onError={handleError}
        {...(property && { property })}
      />
    </div>
  );
});

OptimizedImage.displayName = 'OptimizedImage';

export default OptimizedImage;

// Export utility for preloading images
export const preloadImage = (url: string, width: number = 400): void => {
  const optimizedUrl = getOptimizedUrl(url, width);
  if (!imageCache.has(optimizedUrl)) {
    const img = new Image();
    img.onload = () => imageCache.add(optimizedUrl);
    img.src = optimizedUrl;
  }
};

