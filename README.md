# Holotomographic data management test code collections

This repository contains the following code blocks:

 - data converter to zarr
 - compression benchmark automation
 - simple visualization tool used in publication.

I'm refactoring the codes into more reproducible.
Please make a issue if you found any OS or path dependency.

## Reuirements

### Benchmark Datasets

The following benchmark datasets are used in this project:

 - Embryo cells in a well
 - Birefringent tissue

To get data, contact me.

### Environment

The python packages used are listed on `pyproject.toml`.

### Troubleshooting helper

There was a case that `stitch_ngff.py` does not properly work in "Windows 10/11" returning 'OSError'.
A workaround is to use "Windows subsystem for linux, version 2".
File I/O handler of Windows seems not perfectly suitable with Zarr I/O operations.

## Results

The results of the benchmarks will be documented here.
