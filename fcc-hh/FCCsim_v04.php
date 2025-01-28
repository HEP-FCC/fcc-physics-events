<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'full-sim';
$fileType = 'fcc-root';
$campaign = 'v04';

$dataFilePath = BASE_PATH . '/data/FCChh/FCCsim_v04.txt';
$description = 'FCC-hh Full Simulation samples v0.4.';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
