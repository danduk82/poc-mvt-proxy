

.PHONY: data
data: data/tiles.mbtiles

data/tiles.mbtiles:
	@echo "Downloading tiles..."
	@curl -o data/tiles.mbtiles https://tiles.baremaps.com/2024-07/tiles.mbtiles

.PHONY: clean-tiles
clean-tiles:
	@echo "Cleaning tiles..."
	@rm -f data/tiles.mbtiles