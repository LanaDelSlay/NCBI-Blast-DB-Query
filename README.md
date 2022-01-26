# NCBI-Blast-DB-Query
Little tool for monitoring updates and sizes and downloading BLAST DBs from NCBI's servers.

## Arguemnts:
--show_each_db_segment This will show each individual file making up a DB.

--show_db This will show each DB available that's hosted by NCBI

--dl_db {db name} example: --dl_db human_genome | For a full list of downloadable DBs do --show_db

--sort_size This will sort and output a list in order of largest total (total being the cumulative size of all segments) database size.

--sort_date This will sort and output a list in order of most recently updated. 


![Example Usage](ncbiDBexample.gif)


### TODO:
Add MD5 verification and redownload corrupt files. 

Unzip DB and put into one folder.
