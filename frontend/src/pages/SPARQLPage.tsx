import { useState, useRef, useEffect } from 'react';

const exampleQueries = [
  {
    name: 'List all artworks',
    query: `PREFIX schema: <https://schema.org/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT ?artwork ?title ?artist
WHERE {
  ?artwork a schema:VisualArtwork ;
           dc:title ?title ;
           dc:creator ?artist .
}
LIMIT 20`,
  },
  {
    name: 'Artworks by artist',
    query: `PREFIX schema: <https://schema.org/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT ?artwork ?title ?dateCreated
WHERE {
  ?artwork a schema:VisualArtwork ;
           dc:title ?title ;
           dc:creator "Vincent van Gogh" ;
           dc:date ?dateCreated .
}
ORDER BY ?dateCreated`,
  },
  {
    name: 'Provenance events',
    query: `PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX schema: <https://schema.org/>

SELECT ?artwork ?event ?date ?owner
WHERE {
  ?artwork a schema:VisualArtwork .
  ?event prov:used ?artwork ;
         prov:atTime ?date ;
         prov:wasAssociatedWith ?owner .
}
ORDER BY ?date`,
  },
  {
    name: 'Artworks from DBpedia',
    query: `PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?artwork ?title ?artist ?museum
WHERE {
  SERVICE <http://dbpedia.org/sparql> {
    ?artwork a dbo:Artwork ;
             rdfs:label ?title ;
             dbo:author ?artistUri ;
             dbo:museum ?museumUri .
    ?artistUri rdfs:label ?artist .
    ?museumUri rdfs:label ?museum .
    FILTER(LANG(?title) = "en")
    FILTER(LANG(?artist) = "en")
    FILTER(LANG(?museum) = "en")
  }
}
LIMIT 10`,
  },
];

const SPARQLPage = () => {
  const [query, setQuery] = useState(exampleQueries[0].query);
  const [results, setResults] = useState<null | { head: { vars: string[] }; results: { bindings: Record<string, { value: string }>[] } }>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleExecuteQuery = async () => {
    // Clear any pending timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    setIsLoading(true);
    setError(null);
    setResults(null);

    // Simulated response for demo purposes
    timeoutRef.current = setTimeout(() => {
      setResults({
        head: { vars: ['artwork', 'title', 'artist'] },
        results: {
          bindings: [
            { artwork: { value: 'http://arp.example.org/artwork/1' }, title: { value: 'The Starry Night' }, artist: { value: 'Vincent van Gogh' } },
            { artwork: { value: 'http://arp.example.org/artwork/2' }, title: { value: 'Mona Lisa' }, artist: { value: 'Leonardo da Vinci' } },
            { artwork: { value: 'http://arp.example.org/artwork/3' }, title: { value: 'The Persistence of Memory' }, artist: { value: 'Salvador Dalí' } },
          ],
        },
      });
      setIsLoading(false);
    }, 1000);
  };

  const handleSelectExample = (exampleQuery: string) => {
    setQuery(exampleQuery);
    setResults(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-parchment">
      {/* Page Header */}
      <div className="border-b border-bronze/20 bg-ivory">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <h1 className="font-heading text-3xl font-bold text-charcoal sm:text-4xl">
            SPARQL Explorer
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-charcoal-light">
            Query the ArP knowledge graph using SPARQL. Execute queries against our 
            triplestore or federate with DBpedia and Wikidata.
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-4">
          {/* Sidebar with example queries */}
          <div className="lg:col-span-1">
            <h2 className="font-heading text-lg font-semibold text-charcoal">
              Example Queries
            </h2>
            <div className="mt-4 space-y-2">
              {exampleQueries.map((example, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectExample(example.query)}
                  className="w-full rounded-lg border border-bronze/20 bg-ivory px-4 py-3 text-left text-sm font-medium text-charcoal transition-colors hover:border-gold hover:bg-gold/5"
                >
                  {example.name}
                </button>
              ))}
            </div>

            <div className="mt-8">
              <h2 className="font-heading text-lg font-semibold text-charcoal">
                Endpoints
              </h2>
              <div className="mt-4 space-y-3 text-sm">
                <div>
                  <p className="font-medium text-charcoal">ArP Endpoint</p>
                  <p className="text-charcoal-light">http://localhost:3030/arp/sparql</p>
                </div>
                <div>
                  <p className="font-medium text-charcoal">DBpedia</p>
                  <p className="text-charcoal-light">http://dbpedia.org/sparql</p>
                </div>
                <div>
                  <p className="font-medium text-charcoal">Wikidata</p>
                  <p className="text-charcoal-light">https://query.wikidata.org/sparql</p>
                </div>
              </div>
            </div>
          </div>

          {/* Main query area */}
          <div className="lg:col-span-3">
            {/* Query Editor */}
            <div className="rounded-2xl border border-bronze/20 bg-ivory shadow-sm">
              <div className="flex items-center justify-between border-b border-bronze/10 px-6 py-4">
                <h2 className="font-heading text-lg font-semibold text-charcoal">
                  Query Editor
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => setQuery('')}
                    className="rounded-lg border border-bronze/30 px-4 py-2 text-sm text-charcoal-light hover:border-burgundy hover:text-burgundy transition-colors"
                  >
                    Clear
                  </button>
                  <button
                    onClick={handleExecuteQuery}
                    disabled={isLoading || !query.trim()}
                    className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-gold to-gold-dark px-6 py-2 font-medium text-charcoal shadow-md hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <>
                        <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Executing...
                      </>
                    ) : (
                      <>
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Execute
                      </>
                    )}
                  </button>
                </div>
              </div>
              <div className="p-4">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full h-64 rounded-lg border border-bronze/20 bg-charcoal p-4 font-mono text-sm text-parchment focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
                  placeholder="Enter your SPARQL query here..."
                  spellCheck={false}
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mt-6 rounded-xl border border-burgundy/30 bg-burgundy/10 p-4">
                <div className="flex items-start gap-3">
                  <svg className="h-5 w-5 text-burgundy flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p className="font-medium text-burgundy">Query Error</p>
                    <p className="mt-1 text-sm text-burgundy-dark">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Results */}
            {results && (
              <div className="mt-6 rounded-2xl border border-bronze/20 bg-ivory shadow-sm">
                <div className="flex items-center justify-between border-b border-bronze/10 px-6 py-4">
                  <h2 className="font-heading text-lg font-semibold text-charcoal">
                    Results ({results.results.bindings.length} rows)
                  </h2>
                  <div className="flex gap-2">
                    <button className="rounded-lg border border-bronze/30 px-4 py-2 text-sm text-charcoal-light hover:border-gold hover:text-charcoal transition-colors">
                      Export CSV
                    </button>
                    <button className="rounded-lg border border-bronze/30 px-4 py-2 text-sm text-charcoal-light hover:border-gold hover:text-charcoal transition-colors">
                      Export JSON
                    </button>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-bronze/10 bg-parchment-dark/30">
                        {results.head.vars.map((varName) => (
                          <th
                            key={varName}
                            className="px-6 py-3 text-left text-sm font-semibold text-charcoal"
                          >
                            ?{varName}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-bronze/10">
                      {results.results.bindings.map((binding, rowIndex) => (
                        <tr key={rowIndex} className="hover:bg-parchment-dark/20">
                          {results.head.vars.map((varName) => (
                            <td
                              key={varName}
                              className="px-6 py-4 text-sm text-charcoal-light"
                            >
                              {binding[varName]?.value?.startsWith('http') ? (
                                <a
                                  href={binding[varName]?.value}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-gold hover:underline"
                                >
                                  {binding[varName]?.value}
                                </a>
                              ) : (
                                binding[varName]?.value || '-'
                              )}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SPARQLPage;

