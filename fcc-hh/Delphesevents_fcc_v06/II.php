<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'fcc-v06';
$detector = 'ii';

$dataFilePath = BASE_PATH . '/data/FCChh/Delphesevents_fcc_v06_II.txt';
$description = 'Delphes FCC-hh Physics events v0.6 scenario II. in EDM4Hep format.';
$stack = '/cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
