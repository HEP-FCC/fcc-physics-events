<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'delphes';
$fileType = 'fcc-root';
$campaign = 'fcc-v02';

$dataFilePath = BASE_PATH . '/data/FCChh/Delphesevents_fcc_v02.txt';
$description = 'Delphes FCC-hh Physics events v0.2.';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
