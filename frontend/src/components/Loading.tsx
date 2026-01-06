interface LoadingProps {
  className?: string;
}

// Skeleton loader for artwork cards
export const ArtworkCardSkeleton = ({ className = '' }: LoadingProps) => {
  return (
    <div className={`overflow-hidden rounded-2xl border border-bronze/20 bg-ivory shadow-sm ${className}`}>
      {/* Image skeleton */}
      <div className="aspect-[4/3] animate-pulse bg-parchment-dark" />
      
      {/* Content skeleton */}
      <div className="p-6">
        <div className="h-6 w-3/4 animate-pulse rounded bg-parchment-dark" />
        <div className="mt-2 h-4 w-1/2 animate-pulse rounded bg-parchment-dark" />
        <div className="mt-4 flex items-center justify-between">
          <div className="h-4 w-16 animate-pulse rounded bg-parchment-dark" />
          <div className="h-4 w-20 animate-pulse rounded bg-parchment-dark" />
        </div>
      </div>
    </div>
  );
};

// Grid of skeleton cards
export const ArtworkGridSkeleton = ({ count = 6 }: { count?: number }) => {
  return (
    <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, index) => (
        <ArtworkCardSkeleton key={index} />
      ))}
    </div>
  );
};

// Skeleton for artwork detail page
export const ArtworkDetailSkeleton = () => {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="grid gap-12 lg:grid-cols-2">
        {/* Image skeleton */}
        <div className="aspect-square animate-pulse rounded-2xl bg-parchment-dark" />
        
        {/* Details skeleton */}
        <div>
          <div className="h-10 w-3/4 animate-pulse rounded bg-parchment-dark" />
          <div className="mt-4 h-6 w-1/3 animate-pulse rounded bg-parchment-dark" />
          
          <div className="mt-8 space-y-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="flex border-b border-bronze/10 pb-4">
                <div className="h-4 w-24 animate-pulse rounded bg-parchment-dark" />
                <div className="ml-8 h-4 w-48 animate-pulse rounded bg-parchment-dark" />
              </div>
            ))}
          </div>
          
          <div className="mt-8">
            <div className="h-6 w-32 animate-pulse rounded bg-parchment-dark" />
            <div className="mt-3 space-y-2">
              <div className="h-4 w-full animate-pulse rounded bg-parchment-dark" />
              <div className="h-4 w-5/6 animate-pulse rounded bg-parchment-dark" />
              <div className="h-4 w-4/6 animate-pulse rounded bg-parchment-dark" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Simple spinner
export const Spinner = ({ className = '' }: LoadingProps) => {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-bronze/30 border-t-gold" />
    </div>
  );
};

// Full page loading
export const PageLoading = () => {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="text-center">
        <Spinner className="mb-4" />
        <p className="text-charcoal-light">Loading...</p>
      </div>
    </div>
  );
};

export default Spinner;

