
$benchmark_code="01_compression_benchmark/benchmark_sampled_compression_preset_bulk.py"
$benchmark_recipe="01_compression_benchmark/benchmark_recipe.toml"

uv run python $benchmark_code $benchmark_recipe data/test-embryo-8G output/bench-embryo-8G
uv run python $benchmark_code $benchmark_recipe data/test-tissue-on-8G output/bench-tissue-on-8G
uv run python $benchmark_code $benchmark_recipe data/test-tissue-off-8G output/bench-tissue-off-8G