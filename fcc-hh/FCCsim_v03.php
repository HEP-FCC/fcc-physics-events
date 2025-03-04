<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'full-sim';
$fileType = 'fcc-root';
$campaign = 'v03';

$dataFilePath = BASE_PATH . '/data/FCChh/FCCsim_v03.txt';
$description = 'FCC-hh Full Simulation v0.3.';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
