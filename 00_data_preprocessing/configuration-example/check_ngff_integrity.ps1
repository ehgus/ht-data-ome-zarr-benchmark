conda activate dm312
for ( $i = 1; $i -le 20; $i++ ) {
    for ($j = 1; $j -le 20; $j++) {
        $zarr_path = "D:\birefringent tissue_data/{0:D3}_{1:D3}_DT.ome.zarr" -f $i, $j
        $zarr_metadata_path = "$zarr_path/.zattrs"
        if (-not (Test-Path $zarr_metadata_path)) {
            Write-Output "$zarr_path is not valid"
            Remove-Item -Path $zarr_path -Recurse
        }

    }
}