# es-grafana-bridge

Port over any/all index patterns that exist in Kibana to Grafana. If you want to confirm this works as expected use it like normal, to make changes for real, use the `--for-real` flag.

FYI: Grafana for whatever reason (at the time of writing) has a hardcoded 1000 datasource limit for all datasources. I mention this because *we have hit this* and it causes all of the datasources to go completely wonky, so be aware.

## Usage

```
usage: es_grafana_bridge.py [-h] --token TOKEN [-u USERNAME] [-p PASSWORD] -e
                            ELASTICSEARCH -k KIBANA -g GRAFANA
                            [-i [IGNORE [IGNORE ...]]] [--for-real]

optional arguments:
  -h, --help            show this help message and exit
  --token TOKEN         Grafana Bearer token (already base64'd)
  -u USERNAME, --username USERNAME
                        basic auth username for Kibana
  -p PASSWORD, --password PASSWORD
                        basic auth password for Kibana
  -e ELASTICSEARCH, --elasticsearch ELASTICSEARCH
                        Elasticsearch API
  -k KIBANA, --kibana KIBANA
                        Kibana host
  -g GRAFANA, --grafana GRAFANA
                        Grafana host
  -i [IGNORE [IGNORE ...]], --ignore [IGNORE [IGNORE ...]]
                        regex(es) to exclude patterns
  --for-real            dry run (do not create datasources)
```

It's important to note that the `--kibana` and `--elasticsearch` hosts should relate. The Kibana host is where Kibana lives, and Elasticsearch is the cluster that Kibana works with. Only Kibana is ever verified, so be sure the ES host works with the credentials provided (or else all the datasources it just made won't work 😕).
