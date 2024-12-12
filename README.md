# poc-mvt-proxy


This is a small POC to run a mvt proxy behind a corporate http proxy.

It uses [baremaps](https://baremaps.apache.org/map) as source of styles, glyphs and mvt tiles.

We use `squid` as http proxy and we separate the composition in 2 networks, one `isolated` where the mvt-proxy is running, and another called `internet` which allows external communication. The squid proxy is accessible on both, so it has access to internet, but not mvt-proxy.

We then do a bit of aggressive string replacement in the JSON resources needed for a maplibre application to run and forcing it to use our mvt-proxy as source of all data.

Requirements:

- docker
- (optional) make

## build

```shell
make build
```

## run

```shell
make up
```

if the user doesn't have `make` on his machine he can simply

```shell
cd proxy && docker compose up -d
```



## shutdown
```shell
make down
```

## test the application

the application serves 3 stylse on theses urls by default:

- [default basemap](http://localhost:8080/default)
- [light basemaps](http://localhost:8080/light)
- [dark basemap](http://localhost:8080/dark)

