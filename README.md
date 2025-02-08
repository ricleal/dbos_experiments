# dbos_experiments

My DBOS experiments

See the directories `exp?` for the experiments.

## Instructions

```bash

## Start de DB
docker-compose up

## Stop de DB
docker-compose down

## Connect to the DB
pgcli


```

## Metrics

The demo exposes the following backends:

- Jaeger at http://0.0.0.0:16686
- Zipkin at http://0.0.0.0:9411
- Prometheus at http://0.0.0.0:9090

Based on (OTEL sample)[https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/examples/demo/README.md].

