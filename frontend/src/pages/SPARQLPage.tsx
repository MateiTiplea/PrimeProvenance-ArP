import { useState, useRef, useEffect, useCallback } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { sql } from "@codemirror/lang-sql";
import { oneDark } from "@codemirror/theme-one-dark";
import { sparqlApi } from "../services/api";

// Example queries for the SPARQL explorer - matching the ArP ontology
const exampleQueries = [
  {
    name: "List all artworks",
    description: "Retrieve all artworks with their titles and artist names",
    category: "Basic",
    query: `PREFIX arp: <http://example.org/arp#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX schema: <http://schema.org/>

SELECT ?artwork ?title ?artistName
WHERE {
  ?artwork a arp:Artwork ;
           dc:title ?title ;
           dc:creator ?artist .
  ?artist schema:name ?artistName .
}
LIMIT 20`,
  },
  {
    name: "Artworks by Van Gogh",
    description: "Find all artworks created by Vincent van Gogh",
    category: "Basic",
    query: `PREFIX arp: <http://example.org/arp#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX schema: <http://schema.org/>

SELECT ?artwork ?title ?dateCreated ?medium
WHERE {
  ?artwork a arp:Artwork ;
           dc:title ?title ;
           dc:creator ?artist .
  ?artist schema:name "Vincent van Gogh"@en .
  OPTIONAL { ?artwork dcterms:created ?dateCreated }
  OPTIONAL { ?artwork arp:artworkMedium ?medium }
}`,
  },
  {
    name: "All artists",
    description: "List all artists with their birth/death dates",
    category: "Basic",
    query: `PREFIX arp: <http://example.org/arp#>
PREFIX schema: <http://schema.org/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT ?artist ?name ?birthDate ?deathDate ?nationality
WHERE {
  ?artist a arp:Artist ;
          schema:name ?name .
  OPTIONAL { ?artist schema:birthDate ?birthDate }
  OPTIONAL { ?artist schema:deathDate ?deathDate }
  OPTIONAL { ?artist schema:nationality ?nationality }
}
ORDER BY ?name`,
  },
  {
    name: "Provenance events",
    description: "Track provenance events for artworks",
    category: "Provenance",
    query: `PREFIX arp: <http://example.org/arp#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX schema: <http://schema.org/>

SELECT ?title ?eventType ?startDate ?toOwnerName
WHERE {
  ?artwork a arp:Artwork ;
           dc:title ?title ;
           arp:hasProvenanceEvent ?event .
  ?event arp:eventType ?eventType ;
         prov:startedAtTime ?startDate .
  OPTIONAL { 
    ?event arp:toOwner ?toOwner .
    ?toOwner schema:name ?toOwnerName .
  }
}
ORDER BY ?title ?startDate`,
  },
  {
    name: "Ownership chain",
    description: "Get complete ownership history for a specific artwork",
    category: "Provenance",
    query: `PREFIX arp: <http://example.org/arp#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX schema: <http://schema.org/>

SELECT ?eventType ?description ?startDate ?fromOwnerName ?toOwnerName ?locationName
WHERE {
  ?artwork dc:title "Mona Lisa"@en ;
           arp:hasProvenanceEvent ?event .
  ?event arp:eventType ?eventType ;
         dc:description ?description ;
         prov:startedAtTime ?startDate .
  OPTIONAL { 
    ?event arp:fromOwner ?fromOwner .
    ?fromOwner schema:name ?fromOwnerName .
  }
  OPTIONAL { 
    ?event arp:toOwner ?toOwner .
    ?toOwner schema:name ?toOwnerName .
  }
  OPTIONAL { 
    ?event arp:eventLocation ?location .
    ?location schema:name ?locationName .
  }
}
ORDER BY ?startDate`,
  },
  {
    name: "Artworks by period",
    description: "Group artworks by art historical period",
    category: "Analytics",
    query: `PREFIX arp: <http://example.org/arp#>

SELECT ?period (COUNT(?artwork) as ?count)
WHERE {
  ?artwork a arp:Artwork ;
           arp:artworkPeriod ?period .
}
GROUP BY ?period
ORDER BY DESC(?count)`,
  },
  {
    name: "Artworks by current location",
    description: "Find artworks grouped by museum/location",
    category: "Analytics",
    query: `PREFIX arp: <http://example.org/arp#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX schema: <http://schema.org/>

SELECT ?locationName (COUNT(?artwork) as ?artworkCount)
WHERE {
  ?artwork a arp:Artwork ;
           arp:currentLocation ?location .
  ?location schema:name ?locationName .
}
GROUP BY ?locationName
ORDER BY DESC(?artworkCount)`,
  },
  {
    name: "Museums and their artworks",
    description: "List all museums with the artworks they hold",
    category: "Basic",
    query: `PREFIX arp: <http://example.org/arp#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX schema: <http://schema.org/>

SELECT ?museumName ?title ?artistName
WHERE {
  ?artwork a arp:Artwork ;
           dc:title ?title ;
           dc:creator ?artist ;
           arp:currentLocation ?museum .
  ?artist schema:name ?artistName .
  ?museum a schema:Museum ;
          schema:name ?museumName .
}
ORDER BY ?museumName ?title`,
  },
  {
    name: "Artworks with external links",
    description: "Find artworks linked to DBpedia and Wikidata",
    category: "Linked Data",
    query: `PREFIX arp: <http://example.org/arp#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?title ?sameAsLink
WHERE {
  ?artwork a arp:Artwork ;
           dc:title ?title ;
           owl:sameAs ?sameAsLink .
}
ORDER BY ?title`,
  },
  {
    name: "DBpedia federated query",
    description: "Federated query to retrieve artwork data from DBpedia",
    category: "Federated",
    query: `PREFIX dbo: <http://dbpedia.org/ontology/>
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

interface SPARQLResult {
  head: { vars: string[] };
  results: { bindings: Record<string, { type: string; value: string }>[] };
}

interface ConnectionStatus {
  connected: boolean;
  checking: boolean;
}

const SPARQLPage = () => {
  const [query, setQuery] = useState(exampleQueries[0].query);
  const [results, setResults] = useState<SPARQLResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
    checking: true,
  });
  const abortControllerRef = useRef<AbortController | null>(null);

  // Get unique categories
  const categories = [
    "All",
    ...Array.from(new Set(exampleQueries.map((q) => q.category))),
  ];

  // Filter queries by category
  const filteredQueries =
    selectedCategory === "All"
      ? exampleQueries
      : exampleQueries.filter((q) => q.category === selectedCategory);

  // Check Fuseki connection status on mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(
          `${
            import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api"
          }/sparql/status`
        );
        const data = await response.json();
        setConnectionStatus({ connected: data.connected, checking: false });
      } catch {
        setConnectionStatus({ connected: false, checking: false });
      }
    };
    checkConnection();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "Enter") {
        e.preventDefault();
        if (query.trim() && !isLoading) {
          handleExecuteQuery();
        }
      } else if (e.ctrlKey && e.key === "l") {
        e.preventDefault();
        handleClear();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [query, isLoading]);

  const handleExecuteQuery = async () => {
    // Cancel any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setIsLoading(true);
    setError(null);
    setResults(null);
    setExecutionTime(null);

    const startTime = performance.now();

    try {
      const response = await sparqlApi.query(query);
      const endTime = performance.now();
      setExecutionTime(Math.round(endTime - startTime));

      if (response.data.success) {
        setResults(response.data.results as SPARQLResult);
      } else {
        setError(response.data.error || "Query execution failed");
      }
    } catch (err) {
      if (err instanceof Error && err.name !== "AbortError") {
        setError(
          err.message ||
            "Failed to execute query. Please check your query syntax and try again."
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectExample = (exampleQuery: string) => {
    setQuery(exampleQuery);
    setResults(null);
    setError(null);
    setExecutionTime(null);
  };

  const handleClear = () => {
    setQuery("");
    setResults(null);
    setError(null);
    setExecutionTime(null);
  };

  // Export functions
  const exportToCSV = useCallback(() => {
    if (!results) return;

    const headers = results.head.vars;
    const rows = results.results.bindings.map((binding) =>
      headers.map((h) => {
        const value = binding[h]?.value || "";
        // Escape quotes and wrap in quotes if contains comma or quote
        if (
          value.includes(",") ||
          value.includes('"') ||
          value.includes("\n")
        ) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      })
    );

    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `sparql_results_${
      new Date().toISOString().split("T")[0]
    }.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }, [results]);

  const exportToJSON = useCallback(() => {
    if (!results) return;

    // Transform to cleaner format
    const data = results.results.bindings.map((binding) => {
      const row: Record<string, string> = {};
      results.head.vars.forEach((v) => {
        row[v] = binding[v]?.value || "";
      });
      return row;
    });

    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `sparql_results_${
      new Date().toISOString().split("T")[0]
    }.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  }, [results]);

  // Copy query to clipboard
  const copyQuery = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(query);
    } catch {
      console.error("Failed to copy query");
    }
  }, [query]);

  return (
    <div className="min-h-screen bg-parchment">
      {/* Page Header */}
      <div className="border-b border-bronze/20 bg-gradient-to-r from-ivory to-parchment">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-gold to-gold-dark shadow-lg">
              <svg
                className="h-7 w-7 text-charcoal"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                />
              </svg>
            </div>
            <div>
              <h1 className="font-heading text-3xl font-bold text-charcoal sm:text-4xl">
                SPARQL Explorer
              </h1>
              <p className="mt-1 text-lg text-charcoal-light">
                Query the ArP knowledge graph using SPARQL
              </p>
            </div>
          </div>

          {/* Connection Status Badge */}
          <div className="mt-6 flex items-center gap-3">
            <div
              className={`inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium ${
                connectionStatus.checking
                  ? "bg-bronze/10 text-bronze"
                  : connectionStatus.connected
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  connectionStatus.checking
                    ? "bg-bronze animate-pulse"
                    : connectionStatus.connected
                    ? "bg-green-500"
                    : "bg-red-500"
                }`}
              />
              {connectionStatus.checking
                ? "Checking connection..."
                : connectionStatus.connected
                ? "Fuseki Connected"
                : "Fuseki Offline"}
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-4">
          {/* Sidebar with example queries */}
          <div className="lg:col-span-1 space-y-6">
            {/* Category Filter */}
            <div>
              <h2 className="font-heading text-lg font-semibold text-charcoal mb-3">
                Query Categories
              </h2>
              <div className="flex flex-wrap gap-2">
                {categories.map((category) => (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={`rounded-full px-3 py-1.5 text-xs font-medium transition-all ${
                      selectedCategory === category
                        ? "bg-gradient-to-r from-gold to-gold-dark text-charcoal shadow-md"
                        : "bg-ivory border border-bronze/20 text-charcoal-light hover:border-gold hover:text-charcoal"
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            {/* Example Queries */}
            <div>
              <h2 className="font-heading text-lg font-semibold text-charcoal mb-3">
                Example Queries
              </h2>
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
                {filteredQueries.map((example, index) => (
                  <button
                    key={index}
                    onClick={() => handleSelectExample(example.query)}
                    className="w-full rounded-xl border border-bronze/20 bg-ivory p-4 text-left transition-all hover:border-gold hover:shadow-md hover:bg-gold/5 group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-sm font-semibold text-charcoal group-hover:text-gold-dark">
                        {example.name}
                      </span>
                      <span className="shrink-0 rounded-full bg-parchment-dark/50 px-2 py-0.5 text-xs text-charcoal-light">
                        {example.category}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-charcoal-light line-clamp-2">
                      {example.description}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            {/* Endpoints Reference */}
            <div className="rounded-xl border border-bronze/20 bg-ivory p-5">
              <h2 className="font-heading text-lg font-semibold text-charcoal mb-4">
                SPARQL Endpoints
              </h2>
              <div className="space-y-4">
                <div>
                  <p className="text-xs font-semibold text-gold-dark uppercase tracking-wide">
                    ArP Triplestore
                  </p>
                  <code className="mt-1 block text-xs text-charcoal-light bg-charcoal/5 rounded px-2 py-1 break-all">
                    http://localhost:3030/arp/sparql
                  </code>
                </div>
                <div>
                  <p className="text-xs font-semibold text-gold-dark uppercase tracking-wide">
                    DBpedia
                  </p>
                  <code className="mt-1 block text-xs text-charcoal-light bg-charcoal/5 rounded px-2 py-1 break-all">
                    http://dbpedia.org/sparql
                  </code>
                </div>
                <div>
                  <p className="text-xs font-semibold text-gold-dark uppercase tracking-wide">
                    Wikidata
                  </p>
                  <code className="mt-1 block text-xs text-charcoal-light bg-charcoal/5 rounded px-2 py-1 break-all">
                    https://query.wikidata.org/sparql
                  </code>
                </div>
              </div>
            </div>

            {/* Keyboard Shortcuts */}
            <div className="rounded-xl border border-bronze/20 bg-ivory p-5">
              <h2 className="font-heading text-lg font-semibold text-charcoal mb-3">
                Shortcuts
              </h2>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-charcoal-light">Execute Query</span>
                  <kbd className="rounded bg-charcoal/10 px-2 py-0.5 text-xs font-mono">
                    Ctrl + Enter
                  </kbd>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-charcoal-light">Clear Editor</span>
                  <kbd className="rounded bg-charcoal/10 px-2 py-0.5 text-xs font-mono">
                    Ctrl + L
                  </kbd>
                </div>
              </div>
            </div>
          </div>

          {/* Main query area */}
          <div className="lg:col-span-3 space-y-6">
            {/* Query Editor */}
            <div className="rounded-2xl border border-bronze/20 bg-ivory shadow-lg overflow-hidden">
              <div className="flex items-center justify-between border-b border-bronze/10 px-6 py-4 bg-gradient-to-r from-charcoal/5 to-transparent">
                <div className="flex items-center gap-3">
                  <h2 className="font-heading text-lg font-semibold text-charcoal">
                    Query Editor
                  </h2>
                  <span className="rounded-full bg-charcoal/10 px-2 py-0.5 text-xs text-charcoal-light font-mono">
                    SPARQL 1.1
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={copyQuery}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-bronze/30 px-3 py-2 text-sm text-charcoal-light hover:border-gold hover:text-charcoal transition-all"
                    title="Copy query"
                  >
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                      />
                    </svg>
                    Copy
                  </button>
                  <button
                    onClick={handleClear}
                    className="rounded-lg border border-bronze/30 px-4 py-2 text-sm text-charcoal-light hover:border-burgundy hover:text-burgundy transition-all"
                  >
                    Clear
                  </button>
                  <button
                    onClick={handleExecuteQuery}
                    disabled={isLoading || !query.trim()}
                    className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-gold to-gold-dark px-6 py-2 font-medium text-charcoal shadow-md hover:shadow-lg hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                  >
                    {isLoading ? (
                      <>
                        <svg
                          className="h-4 w-4 animate-spin"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Executing...
                      </>
                    ) : (
                      <>
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        Execute
                      </>
                    )}
                  </button>
                </div>
              </div>
              <div className="p-4">
                <CodeMirror
                  value={query}
                  height="280px"
                  theme={oneDark}
                  extensions={[sql()]}
                  onChange={(value) => setQuery(value)}
                  className="rounded-lg overflow-hidden border border-bronze/10"
                  basicSetup={{
                    lineNumbers: true,
                    highlightActiveLineGutter: true,
                    highlightSpecialChars: true,
                    foldGutter: true,
                    drawSelection: true,
                    dropCursor: true,
                    allowMultipleSelections: true,
                    indentOnInput: true,
                    syntaxHighlighting: true,
                    bracketMatching: true,
                    closeBrackets: true,
                    autocompletion: true,
                    rectangularSelection: true,
                    crosshairCursor: false,
                    highlightActiveLine: true,
                    highlightSelectionMatches: true,
                    closeBracketsKeymap: true,
                    defaultKeymap: true,
                    searchKeymap: true,
                    historyKeymap: true,
                    foldKeymap: true,
                    completionKeymap: true,
                    lintKeymap: true,
                  }}
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="rounded-xl border border-burgundy/30 bg-gradient-to-r from-burgundy/10 to-burgundy/5 p-5 animate-in fade-in slide-in-from-top-2">
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-burgundy/20">
                    <svg
                      className="h-5 w-5 text-burgundy"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="font-semibold text-burgundy">Query Error</p>
                    <p className="mt-1 text-sm text-burgundy-dark">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Results */}
            {results && (
              <div className="rounded-2xl border border-bronze/20 bg-ivory shadow-lg overflow-hidden animate-in fade-in slide-in-from-bottom-2">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-bronze/10 px-6 py-4 bg-gradient-to-r from-green-50/50 to-transparent">
                  <div className="flex items-center gap-4">
                    <h2 className="font-heading text-lg font-semibold text-charcoal">
                      Results
                    </h2>
                    <div className="flex items-center gap-3 text-sm text-charcoal-light">
                      <span className="inline-flex items-center gap-1.5">
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                          />
                        </svg>
                        {results.results.bindings.length} rows
                      </span>
                      {executionTime !== null && (
                        <span className="inline-flex items-center gap-1.5">
                          <svg
                            className="h-4 w-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          {executionTime}ms
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={exportToCSV}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-bronze/30 px-4 py-2 text-sm font-medium text-charcoal-light hover:border-gold hover:text-charcoal transition-all hover:shadow-sm"
                    >
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      Export CSV
                    </button>
                    <button
                      onClick={exportToJSON}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-bronze/30 px-4 py-2 text-sm font-medium text-charcoal-light hover:border-gold hover:text-charcoal transition-all hover:shadow-sm"
                    >
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      Export JSON
                    </button>
                  </div>
                </div>

                {results.results.bindings.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-bronze/10">
                      <svg
                        className="h-8 w-8 text-bronze"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                        />
                      </svg>
                    </div>
                    <p className="mt-4 text-lg font-medium text-charcoal">
                      No results found
                    </p>
                    <p className="mt-1 text-sm text-charcoal-light">
                      The query executed successfully but returned no matching
                      data.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-bronze/10 bg-parchment-dark/30">
                          <th className="px-4 py-3 text-left text-xs font-semibold text-charcoal-light uppercase tracking-wide">
                            #
                          </th>
                          {results.head.vars.map((varName) => (
                            <th
                              key={varName}
                              className="px-4 py-3 text-left text-xs font-semibold text-charcoal-light uppercase tracking-wide"
                            >
                              ?{varName}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-bronze/10">
                        {results.results.bindings.map((binding, rowIndex) => (
                          <tr
                            key={rowIndex}
                            className="hover:bg-gold/5 transition-colors"
                          >
                            <td className="px-4 py-3 text-xs text-charcoal-light font-mono">
                              {rowIndex + 1}
                            </td>
                            {results.head.vars.map((varName) => (
                              <td
                                key={varName}
                                className="px-4 py-3 text-sm text-charcoal-light max-w-md"
                              >
                                {binding[varName]?.value?.startsWith("http") ? (
                                  <a
                                    href={binding[varName]?.value}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-gold-dark hover:text-gold hover:underline break-all"
                                  >
                                    <span className="line-clamp-1">
                                      {binding[varName]?.value}
                                    </span>
                                    <svg
                                      className="h-3 w-3 shrink-0"
                                      fill="none"
                                      viewBox="0 0 24 24"
                                      stroke="currentColor"
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                      />
                                    </svg>
                                  </a>
                                ) : (
                                  <span className="break-words">
                                    {binding[varName]?.value || (
                                      <span className="text-charcoal-light/50 italic">
                                        null
                                      </span>
                                    )}
                                  </span>
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Empty State */}
            {!results && !error && !isLoading && (
              <div className="rounded-2xl border-2 border-dashed border-bronze/30 bg-ivory/50 p-12">
                <div className="flex flex-col items-center justify-center text-center">
                  <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-gold/20 to-gold-dark/20">
                    <svg
                      className="h-10 w-10 text-gold-dark"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                  <h3 className="mt-6 font-heading text-xl font-semibold text-charcoal">
                    Ready to Query
                  </h3>
                  <p className="mt-2 max-w-sm text-charcoal-light">
                    Write your SPARQL query in the editor above or select one of
                    the example queries from the sidebar to get started.
                  </p>
                  <div className="mt-6 flex items-center gap-2 text-sm text-charcoal-light">
                    <kbd className="rounded bg-charcoal/10 px-2 py-1 font-mono text-xs">
                      Ctrl
                    </kbd>
                    <span>+</span>
                    <kbd className="rounded bg-charcoal/10 px-2 py-1 font-mono text-xs">
                      Enter
                    </kbd>
                    <span className="ml-1">to execute</span>
                  </div>
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
