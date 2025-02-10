<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'fcc-v04';

$dataFilePath = BASE_PATH . '/data/FCChh/Delphesevents_fcc_v04.txt';
$description = 'Delphes FCC-hh Physics events v0.4 based on EDM4Hep.';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
