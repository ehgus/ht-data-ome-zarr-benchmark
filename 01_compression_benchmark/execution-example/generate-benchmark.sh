
uv run python ./01_compression_benchmark/generate_benchmark_sample.py ./data/embryo.ome.zarr ./data/test-embryo-8G 1024 "(1,1,32,256,256)" "(0,0,0,5,5)" --channel 0
uv run python ./01_compression_benchmark/generate_benchmark_sample.py ./data/birefringent-data.ome.zarr ./data/test-tissue-on-8G 1024 "(1,1,32,256,256)" "(0,0,0,540,200)" --channel 0
uv run python ./01_compression_benchmark/generate_benchmark_sample.py ./data/birefringent-data.ome.zarr ./data/test-tissue-off-8G 1024 "(1,1,32,256,256)" "(0,0,0,540,200)" --channel 1
