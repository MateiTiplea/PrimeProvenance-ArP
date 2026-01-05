FROM stain/jena-fuseki:latest

USER root
RUN mkdir -p /fuseki/configuration /fuseki/databases/arp

COPY config/config.ttl /fuseki/configuration/arp.ttl

RUN chown -R 1000:1000 /fuseki
