<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'full-sim';
$fileType = 'fcc-root';
$campaign = 'v03-ecal';

$dataFilePath = BASE_PATH . '/data/FCChh/FCCsim_v03_ecal.txt';
$description = 'FCC-hh Full Simulation v0.3 ECal.';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
