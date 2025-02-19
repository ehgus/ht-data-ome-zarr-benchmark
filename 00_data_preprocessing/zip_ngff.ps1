conda activate dm312
for ( $i = 1; $i -le 20; $i++ ) {
    for ($j = 1; $j -le 20; $j++) {
        $zarr_path = "D:\birefringent tissue_data/{0:D3}_{1:D3}_DT.ome.zarr" -f $i, $j
        $zarr_zip_path = "D:\birefringent tissue_data/{0:D3}_{1:D3}_DT.ome.zarr.zip" -f $i, $j
        if (Test-Path $zarr_zip_path) {
            Write-Output "Skipping $zarr_zip_path"
            continue
        }
        Write-Output "Writing $zarr_zip_path"
        Compress-Archive -Path $zarr_path -DestinationPath $zarr_zip_path
    }
}