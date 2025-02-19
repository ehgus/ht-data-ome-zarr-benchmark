import zarr
import numpy as np

def add_random_noise(input_zarr_path, output_zarr_path, noise_range=(-5e-5, 5e-5)):
    """
    Reads a Zarr file, adds random noise within the given range, and writes to a new Zarr file.

    Parameters:
    - input_zarr_path: Path to the input Zarr file.
    - output_zarr_path: Path to the output Zarr file.
    - noise_range: Tuple (min_noise, max_noise) defining the range of random noise.
    """
    # Open the input Zarr file
    input_zarr = zarr.open(input_zarr_path, mode='r')

    # Create a new Zarr file to store the modified data
    output_zarr = zarr.open(output_zarr_path, mode='w')

    # Iterate over all datasets in the input Zarr file
    for array_name in input_zarr.array_keys():
        data = input_zarr[array_name][:]
        
        # Generate random noise
        noise = np.random.uniform(noise_range[0], noise_range[1], data.shape)
        
        # Add noise to the data
        noisy_data = data + noise
        
        # Store the noisy data in the output Zarr file
        output_zarr.create_dataset(array_name, data=noisy_data, chunks=True, overwrite=True)

    print(f"Modified data with noise saved to {output_zarr_path}")

# Example usage
input_zarr_file = "input.zarr"   # Change to your input Zarr file path
output_zarr_file = "output.zarr" # Change to your desired output Zarr file path

add_random_noise(input_zarr_file, output_zarr_file)
