$MaxThreads = 4

for ( $i = 1; $i -le 20; $i++ ) {
    for ($j = 1; $j -le 20; $j++) {
        $src_mat_path = "D:\birefringent tissue_data/_{0:D3}_{1:D3}_DT.mat" -f $i, $j
        $dst_zarr_path = "D:\birefringent tissue_data/{0:D3}_{1:D3}_DT.ome.zarr" -f $i, $j
        if (Test-Path $dst_zarr_path) {
            Write-Output "Skipping $dst_zarr_path"
            continue
        }
	    While ($(Get-Job -State Running).count -ge $MaxThreads){
		    Start-Sleep -Seconds 5
	    }
        Write-Output "Writing $dst_zarr_path"
	    Start-Job -ScriptBlock { # Invoke-Command
            param ($src_mat_path, $dst_zarr_path)
            C:\Users\labdo\.miniforge3\envs\dm312\python.exe "C:/Users/labdo/Desktop/02_data management/12_code/01_compression_benchmark/convert_mat73_to_ngff.py" $src_mat_path $dst_zarr_path "-c" "zstd-19"
        } -ArgumentList $src_mat_path, $dst_zarr_path
    }
}
# Wait for all jobs to finish
While ($(Get-Job -State Running).count -gt 0){
	Start-Sleep -Seconds 5
}

foreach($job in Get-Job){
    Receive-Job -Id ($job.Id)
}

# Remove all jobs created.
Get-Job | Remove-Job