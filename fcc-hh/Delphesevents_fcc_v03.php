<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'delphes';
$fileType = 'fcc-root';
$campaign = 'fcc-v03';

$dataFilePath = BASE_PATH . '/data/FCChh/Delphesevents_fcc_v03.txt';
$description = 'Delphes FCC-hh Physics events v0.3.';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
