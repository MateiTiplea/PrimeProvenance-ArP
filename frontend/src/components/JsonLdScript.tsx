/**
 * JsonLdScript Component
 * 
 * Generates and injects Schema.org/VisualArtwork JSON-LD structured data
 * into the document head for SEO and semantic web purposes.
 */

import { useEffect } from 'react';
import type { Artwork, ProvenanceRecord } from '../services/api';

interface JsonLdScriptProps {
    artwork: Artwork;
    provenance?: ProvenanceRecord[];
    baseUrl?: string;
}

interface JsonLdPerson {
    '@type': 'Person';
    name: string;
}

interface JsonLdPlace {
    '@type': 'Place';
    name: string;
}

interface JsonLdTransferAction {
    '@type': 'TransferAction';
    startTime?: string;
    agent?: JsonLdPerson;
    location?: JsonLdPlace;
    description?: string;
}

interface JsonLdVisualArtwork {
    '@context': 'https://schema.org';
    '@type': 'VisualArtwork';
    '@id'?: string;
    name: string;
    description?: string;
    dateCreated?: string;
    creator?: JsonLdPerson;
    artMedium?: string;
    artform?: string;
    width?: string;
    height?: string;
    image?: string;
    contentLocation?: JsonLdPlace;
    temporalCoverage?: string;
    genre?: string;
    sameAs?: string[];
    subjectOf?: JsonLdTransferAction[];
}

/**
 * Parses dimension string and extracts width/height if possible
 * Expected formats: "30 x 40 cm", "30x40cm", "30 × 40 inches"
 */
const parseDimensions = (dimensions: string): { width?: string; height?: string } => {
    if (!dimensions) return {};

    // Match patterns like "30 x 40 cm" or "30x40cm" or "30 × 40"
    const match = dimensions.match(/(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(cm|in|inches|mm|m)?/i);
    if (match) {
        const unit = match[3] || '';
        return {
            width: `${match[1]}${unit}`,
            height: `${match[2]}${unit}`,
        };
    }
    return {};
};

/**
 * Generates JSON-LD structured data for a VisualArtwork
 */
const generateJsonLd = (
    artwork: Artwork,
    provenance?: ProvenanceRecord[],
    baseUrl: string = typeof window !== 'undefined' ? window.location.origin : ''
): JsonLdVisualArtwork => {
    const jsonLd: JsonLdVisualArtwork = {
        '@context': 'https://schema.org',
        '@type': 'VisualArtwork',
        '@id': `${baseUrl}/artworks/${artwork.id}`,
        name: artwork.title,
    };

    // Add optional properties
    if (artwork.description) {
        jsonLd.description = artwork.description;
    }

    if (artwork.dateCreated) {
        jsonLd.dateCreated = artwork.dateCreated;
    }

    if (artwork.artist) {
        jsonLd.creator = {
            '@type': 'Person',
            name: artwork.artist,
        };
    }

    if (artwork.medium) {
        jsonLd.artMedium = artwork.medium;
    }

    if (artwork.dimensions) {
        const { width, height } = parseDimensions(artwork.dimensions);
        if (width) jsonLd.width = width;
        if (height) jsonLd.height = height;
    }

    if (artwork.imageUrl) {
        // Ensure absolute URL for image
        jsonLd.image = artwork.imageUrl.startsWith('http')
            ? artwork.imageUrl
            : `${baseUrl}${artwork.imageUrl}`;
    }

    if (artwork.currentLocation) {
        jsonLd.contentLocation = {
            '@type': 'Place',
            name: artwork.currentLocation,
        };
    }

    if (artwork.period) {
        jsonLd.temporalCoverage = artwork.period;
    }

    if (artwork.style) {
        jsonLd.genre = artwork.style;
    }

    // Add sameAs links for external resources
    const sameAsLinks: string[] = [];
    if (artwork.externalLinks?.dbpedia) {
        sameAsLinks.push(artwork.externalLinks.dbpedia);
    }
    if (artwork.externalLinks?.wikidata) {
        sameAsLinks.push(artwork.externalLinks.wikidata);
    }
    if (artwork.externalLinks?.getty) {
        sameAsLinks.push(artwork.externalLinks.getty);
    }
    if (sameAsLinks.length > 0) {
        jsonLd.sameAs = sameAsLinks;
    }

    // Add provenance as TransferAction events
    if (provenance && provenance.length > 0) {
        jsonLd.subjectOf = provenance.map((record): JsonLdTransferAction => {
            const action: JsonLdTransferAction = {
                '@type': 'TransferAction',
            };

            if (record.date) {
                action.startTime = record.date;
            }

            if (record.owner) {
                action.agent = {
                    '@type': 'Person',
                    name: record.owner,
                };
            }

            if (record.location) {
                action.location = {
                    '@type': 'Place',
                    name: record.location,
                };
            }

            if (record.description) {
                action.description = record.description;
            }

            return action;
        });
    }

    return jsonLd;
};

/**
 * Component that injects JSON-LD structured data into the document head
 */
const JsonLdScript: React.FC<JsonLdScriptProps> = ({ artwork, provenance, baseUrl }) => {
    useEffect(() => {
        // Generate JSON-LD data
        const jsonLd = generateJsonLd(artwork, provenance, baseUrl);

        // Create or update script element
        const scriptId = 'artwork-jsonld';
        let scriptElement = document.getElementById(scriptId) as HTMLScriptElement | null;

        if (!scriptElement) {
            scriptElement = document.createElement('script');
            scriptElement.id = scriptId;
            scriptElement.type = 'application/ld+json';
            document.head.appendChild(scriptElement);
        }

        scriptElement.textContent = JSON.stringify(jsonLd, null, 2);

        // Cleanup on unmount
        return () => {
            const existingScript = document.getElementById(scriptId);
            if (existingScript) {
                existingScript.remove();
            }
        };
    }, [artwork, provenance, baseUrl]);

    // This component doesn't render anything visible
    return null;
};

export default JsonLdScript;
