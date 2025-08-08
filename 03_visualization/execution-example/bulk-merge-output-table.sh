
export merge_code="03_visualization/merge_output_table.py"

uv run python $merge_code "output/bench-embryo-8G*/*.csv" output/merged-embryo-8G.csv
uv run python $merge_code "output/bench-tissue-on-8G*/*.csv" output/merged-tissue-on-8G.csv
uv run python $merge_code "output/bench-tissue-off-8G*/*.csv" output/merged-tissue-off-8G.csv
uv run python $merge_code "output/bench-organoid-8G*/*.csv" output/merged-organoid-8G.csv
uv run python $merge_code "output/bench-HeLa-8G*/*.csv" output/merged-HeLa-8G.csv
uv run python $merge_code "output/bench-bacteria-8G*/*.csv" output/merged-bacteria-8G.csv
