<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'fcc-v07';
$det = 'ii';

$dataFilePath = BASE_PATH . '/data/FCChh/Delphesevents_fcc_v07_II.txt';
$description = 'Delphes FCC-hh Physics events v0.7 scenario II. in EDM4Hep format.';
$stack = '/cvmfs/sw.hsf.org/key4hep/setup.sh -r 2025-01-28';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
