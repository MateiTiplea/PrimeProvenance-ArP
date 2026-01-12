const AboutPage = () => {
  return (
    <div className="min-h-screen bg-parchment">
      {/* Hero */}
      <div className="bg-gradient-to-br from-charcoal via-charcoal to-burgundy-dark">
        <div className="mx-auto max-w-4xl px-4 py-20 sm:px-6 lg:px-8">
          <h1 className="text-center font-heading text-4xl font-bold text-ivory sm:text-5xl">
            About{' '}
            <span className="bg-gradient-to-r from-gold to-gold-light bg-clip-text text-transparent">
              ArP
            </span>
          </h1>
          <p className="mt-6 text-center text-lg text-parchment/80">
            Artwork Provenance — A semantic web platform for exploring
            the histories behind masterpieces
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
        {/* Mission */}
        <section className="prose prose-lg max-w-none">
          <h2 className="font-heading text-2xl font-bold text-charcoal">Our Mission</h2>
          <p className="text-charcoal-light leading-relaxed">
            ArP (Artwork Provenance) is a semantic web platform designed to model and manage
            the knowledge about the provenance of artistic works. By leveraging linked data
            technologies and integrating with major knowledge bases, ArP provides a comprehensive
            view of artwork histories, ownership chains, and cultural significance.
          </p>
        </section>

        {/* Technologies */}
        <section className="mt-16">
          <h2 className="font-heading text-2xl font-bold text-charcoal">Technologies</h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-2">
            <div className="rounded-xl border border-bronze/20 bg-ivory p-6">
              <h3 className="font-heading text-lg font-semibold text-charcoal">Semantic Web Stack</h3>
              <ul className="mt-4 space-y-2 text-charcoal-light">
                <li>• RDF / RDFa for data representation</li>
                <li>• SPARQL for querying</li>
                <li>• Schema.org vocabulary</li>
                <li>• CIDOC-CRM ontology</li>
                <li>• PROV-O for provenance</li>
              </ul>
            </div>
            <div className="rounded-xl border border-bronze/20 bg-ivory p-6">
              <h3 className="font-heading text-lg font-semibold text-charcoal">Development Stack</h3>
              <ul className="mt-4 space-y-2 text-charcoal-light">
                <li>• React with TypeScript</li>
                <li>• FastAPI backend</li>
                <li>• Apache Jena Fuseki</li>
                <li>• Tailwind CSS</li>
                <li>• Vite build tool</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Data Sources */}
        <section className="mt-16">
          <h2 className="font-heading text-2xl font-bold text-charcoal">Data Sources</h2>
          <p className="mt-4 text-charcoal-light">
            ArP integrates with multiple external knowledge bases to provide rich,
            interconnected data about artworks and their provenance:
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <a
              href="https://dbpedia.org"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl border border-bronze/20 bg-ivory p-6 text-center transition-all hover:border-gold hover:shadow-md"
            >
              <div className="font-heading text-xl font-bold text-charcoal">DBpedia</div>
              <p className="mt-2 text-sm text-charcoal-light">Structured data from Wikipedia</p>
            </a>
            <a
              href="https://www.wikidata.org"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl border border-bronze/20 bg-ivory p-6 text-center transition-all hover:border-gold hover:shadow-md"
            >
              <div className="font-heading text-xl font-bold text-charcoal">Wikidata</div>
              <p className="mt-2 text-sm text-charcoal-light">Free knowledge base</p>
            </a>
            <a
              href="https://vocab.getty.edu"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl border border-bronze/20 bg-ivory p-6 text-center transition-all hover:border-gold hover:shadow-md"
            >
              <div className="font-heading text-xl font-bold text-charcoal">Getty</div>
              <p className="mt-2 text-sm text-charcoal-light">Art vocabularies</p>
            </a>
            <a
              href="https://www.europeana.eu"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl border border-bronze/20 bg-ivory p-6 text-center transition-all hover:border-gold hover:shadow-md"
            >
              <div className="font-heading text-xl font-bold text-charcoal">Europeana</div>
              <p className="mt-2 text-sm text-charcoal-light">European cultural heritage</p>
            </a>
            <a
              href="https://data.gov.ro/dataset/bunuri-culturale-clasate-arta"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl border border-bronze/20 bg-ivory p-6 text-center transition-all hover:border-gold hover:shadow-md"
            >
              <div className="font-heading text-xl font-bold text-charcoal">data.gov.ro</div>
              <p className="mt-2 text-sm text-charcoal-light">Romanian open data portal</p>
            </a>
          </div>
        </section>

        {/* Features */}
        <section className="mt-16">
          <h2 className="font-heading text-2xl font-bold text-charcoal">Key Features</h2>
          <div className="mt-8 space-y-6">
            <div className="flex gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-gold/20 text-gold">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <div>
                <h3 className="font-heading text-lg font-semibold text-charcoal">Provenance Tracking</h3>
                <p className="mt-1 text-charcoal-light">
                  Complete ownership history visualization with timeline view of provenance events.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-gold/20 text-gold">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h3 className="font-heading text-lg font-semibold text-charcoal">SPARQL Interface</h3>
                <p className="mt-1 text-charcoal-light">
                  Interactive query editor with example queries and federated search capabilities.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-gold/20 text-gold">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
              <div>
                <h3 className="font-heading text-lg font-semibold text-charcoal">Linked Data Integration</h3>
                <p className="mt-1 text-charcoal-light">
                  Seamless connection to DBpedia, Wikidata, and Getty vocabularies for enriched metadata.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-gold/20 text-gold">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                </svg>
              </div>
              <div>
                <h3 className="font-heading text-lg font-semibold text-charcoal">QR Code Sharing</h3>
                <p className="mt-1 text-charcoal-light">
                  Generate QR codes for easy sharing and permanent URLs for each artwork.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Project Info */}
        <section className="mt-16 rounded-2xl border border-bronze/20 bg-ivory p-8">
          <h2 className="font-heading text-2xl font-bold text-charcoal">Project Information</h2>
          <div className="mt-6 space-y-4 text-charcoal-light">
            <p>
              <strong className="text-charcoal">Course:</strong> WADe (Web Application Development)
            </p>
            <p>
              <strong className="text-charcoal">University:</strong> Alexandru Ioan Cuza University, Iași
            </p>
            <p>
              <strong className="text-charcoal">License:</strong> MIT License / Creative Commons
            </p>
          </div>
          <div className="mt-8 flex gap-4">
            <a
              href="https://github.com/MateiTiplea/PrimeProvenance-ArP"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm font-medium text-charcoal hover:border-gold hover:text-gold transition-colors"
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
              View on GitHub
            </a>
            <a
              href="/docs/technical-report.html"
              className="inline-flex items-center gap-2 rounded-lg border border-bronze/30 bg-ivory px-4 py-2 text-sm font-medium text-charcoal hover:border-gold hover:text-gold transition-colors"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Technical Report
            </a>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AboutPage;

