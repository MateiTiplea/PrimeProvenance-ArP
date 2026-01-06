import { Link } from 'react-router-dom';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  showHomeLink?: boolean;
  className?: string;
}

const ErrorMessage = ({ 
  title = 'Something went wrong', 
  message, 
  onRetry, 
  showHomeLink = false,
  className = '' 
}: ErrorMessageProps) => {
  return (
    <div className={`rounded-2xl border border-burgundy/20 bg-burgundy/5 p-8 text-center ${className}`}>
      {/* Error icon */}
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-burgundy/10">
        <svg 
          className="h-8 w-8 text-burgundy" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
          />
        </svg>
      </div>
      
      <h3 className="mt-4 font-heading text-xl font-semibold text-charcoal">
        {title}
      </h3>
      
      <p className="mt-2 text-charcoal-light">
        {message}
      </p>
      
      <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-gold to-gold-dark px-6 py-3 font-medium text-charcoal shadow-md hover:shadow-lg transition-shadow"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Try Again
          </button>
        )}
        
        {showHomeLink && (
          <Link
            to="/"
            className="inline-flex items-center gap-2 rounded-lg border border-bronze/30 px-6 py-3 font-medium text-charcoal hover:border-gold hover:text-gold transition-colors"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Go Home
          </Link>
        )}
      </div>
    </div>
  );
};

// 404 Not Found component
export const NotFound = ({ 
  itemType = 'page',
  backLink = '/',
  backLinkText = 'Go back home'
}: { 
  itemType?: string;
  backLink?: string;
  backLinkText?: string;
}) => {
  return (
    <div className="flex min-h-[50vh] items-center justify-center px-4">
      <div className="text-center">
        <h1 className="font-heading text-6xl font-bold text-gold">404</h1>
        <h2 className="mt-4 font-heading text-2xl font-semibold text-charcoal">
          {itemType.charAt(0).toUpperCase() + itemType.slice(1)} Not Found
        </h2>
        <p className="mt-2 text-charcoal-light">
          The {itemType} you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to={backLink}
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-gold to-gold-dark px-6 py-3 font-medium text-charcoal shadow-md hover:shadow-lg transition-shadow"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          {backLinkText}
        </Link>
      </div>
    </div>
  );
};

export default ErrorMessage;

