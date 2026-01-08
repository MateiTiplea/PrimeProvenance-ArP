/**
 * QRCodeModal Component
 * 
 * Modal to display and download QR code for artwork sharing.
 */

import { useState, useEffect, useCallback } from 'react';
import { artworkApi } from '../services/api';

interface QRCodeModalProps {
    artworkId: string;
    artworkTitle: string;
    isOpen: boolean;
    onClose: () => void;
}

const QRCodeModal: React.FC<QRCodeModalProps> = ({
    artworkId,
    artworkTitle,
    isOpen,
    onClose,
}) => {
    const [qrCodeUrl, setQrCodeUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const shareUrl = `${window.location.origin}/artworks/${artworkId}`;

    const fetchQrCode = useCallback(async () => {
        if (!isOpen || !artworkId) return;

        setLoading(true);
        setError(null);

        try {
            const response = await artworkApi.getQRCode(artworkId);
            const blob = new Blob([response.data], { type: 'image/png' });
            const url = URL.createObjectURL(blob);
            setQrCodeUrl(url);
        } catch (err) {
            console.error('Failed to fetch QR code:', err);
            setError('Failed to generate QR code. Please try again.');
        } finally {
            setLoading(false);
        }
    }, [artworkId, isOpen]);

    useEffect(() => {
        if (isOpen) {
            fetchQrCode();
        }

        return () => {
            if (qrCodeUrl) {
                URL.revokeObjectURL(qrCodeUrl);
            }
        };
    }, [isOpen, fetchQrCode]);

    const handleDownload = () => {
        if (!qrCodeUrl) return;

        const link = document.createElement('a');
        link.href = qrCodeUrl;
        link.download = `${artworkId}-qr.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleCopyUrl = async () => {
        try {
            await navigator.clipboard.writeText(shareUrl);
            // Could add a toast notification here
        } catch (err) {
            console.error('Failed to copy URL:', err);
        }
    };

    // Handle escape key
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="qr-modal-title"
        >
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-charcoal/60 backdrop-blur-sm"
                onClick={onClose}
                aria-hidden="true"
            />

            {/* Modal */}
            <div className="relative w-full max-w-md rounded-2xl border border-bronze/20 bg-ivory p-6 shadow-xl">
                {/* Close button */}
                <button
                    onClick={onClose}
                    className="cursor-pointer absolute right-4 top-4 rounded-lg p-2 text-charcoal-light hover:bg-parchment hover:text-charcoal transition-colors"
                    aria-label="Close modal"
                >
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>

                {/* Title */}
                <h2
                    id="qr-modal-title"
                    className="font-heading text-xl font-bold text-charcoal pr-8"
                >
                    Share "{artworkTitle}"
                </h2>

                <p className="mt-2 text-sm text-charcoal-light">
                    Scan this QR code to open the artwork page on any device.
                </p>

                {/* QR Code */}
                <div className="mt-6 flex justify-center">
                    {loading && (
                        <div className="flex h-64 w-64 items-center justify-center rounded-xl border border-bronze/20 bg-parchment">
                            <div className="h-8 w-8 animate-spin rounded-full border-4 border-gold border-t-transparent" />
                        </div>
                    )}

                    {error && (
                        <div className="flex h-64 w-64 flex-col items-center justify-center rounded-xl border border-burgundy/20 bg-burgundy/5 p-4 text-center">
                            <svg className="h-12 w-12 text-burgundy" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <p className="mt-3 text-sm text-burgundy">{error}</p>
                            <button
                                onClick={fetchQrCode}
                                className="cursor-pointer mt-3 text-sm font-medium text-gold hover:text-gold-dark"
                            >
                                Try again
                            </button>
                        </div>
                    )}

                    {qrCodeUrl && !loading && !error && (
                        <div className="rounded-xl border border-bronze/20 bg-white p-4 shadow-sm">
                            <img
                                src={qrCodeUrl}
                                alt={`QR code for ${artworkTitle}`}
                                className="h-56 w-56"
                            />
                        </div>
                    )}
                </div>

                {/* URL display */}
                <div className="mt-6">
                    <label className="text-sm font-medium text-charcoal-light">
                        Shareable URL
                    </label>
                    <div className="mt-1 flex items-center gap-2">
                        <input
                            type="text"
                            value={shareUrl}
                            readOnly
                            className="flex-1 rounded-lg border border-bronze/30 bg-parchment px-3 py-2 text-sm text-charcoal focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
                        />
                        <button
                            onClick={handleCopyUrl}
                            className="cursor-pointer rounded-lg border border-bronze/30 bg-ivory px-3 py-2 text-charcoal hover:border-gold hover:text-gold transition-colors"
                            title="Copy URL"
                        >
                            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Actions */}
                <div className="mt-6 flex gap-3">
                    <button
                        onClick={handleDownload}
                        disabled={!qrCodeUrl || loading}
                        className="cursor-pointer flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-gold to-gold-dark px-4 py-2.5 font-medium text-charcoal shadow-md hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        Download QR
                    </button>
                    <button
                        onClick={onClose}
                        className="cursor-pointer flex-1 rounded-lg border border-bronze/30 bg-ivory px-4 py-2.5 font-medium text-charcoal hover:border-gold transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default QRCodeModal;
