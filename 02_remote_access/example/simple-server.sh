
uv run python 02_remote_access/simple-server.py ./data/
# in napari, run "viewer.open('http://localhost:8000/birefringent-data.ome.zarr/',plugin='napari-ome-zarr')"
# To connect through SSH/SCP, change the URL to 'ssh://<USERNAME>@localhost:<PORT>/birefringent-data.ome.zarr/' where USERNAME and PORT is your custom value.
# It is possible to use object storage